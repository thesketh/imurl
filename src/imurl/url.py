"""The URL class."""
import json
import urllib.parse
from copy import copy
from pathlib import PurePosixPath
from typing import Any, MutableMapping, Optional, TypedDict, Union

__all__ = ["URL", "URLDict"]


class URLDict(TypedDict, total=False):
    """A typed dictionary of URL components."""

    scheme: Optional[str]
    username: Optional[str]
    password: Optional[str]
    host: Optional[str]
    port: Optional[int]
    path: Optional[Union[str, PurePosixPath]]
    param_dict: MutableMapping[str, Optional[str]]
    param_delimiter: str
    query_dict: MutableMapping[str, Optional[str]]
    query_delimiter: str
    fragment: Optional[str]


URL_COMPONENTS = set(URLDict.__annotations__.keys())  # pylint: disable=no-member


def _encode_url_dict(url_dict: URLDict) -> URLDict:
    """Apply URL percent-endoding to a `URLDict`."""
    quoted_dict = URLDict()
    keys = set(url_dict.keys())

    # Keys which don't require quoting.
    for k in {"port", "param_delimiter", "query_delimiter"} & keys:
        quoted_dict[k] = url_dict[k]  # type: ignore

    # Keys which _do_ require quoting.
    for k in {"scheme", "username", "password", "host", "path", "fragment"} & keys:
        quoted_dict[k] = urllib.parse.quote(url_dict[k])  # type: ignore

    # Keys which need all the items in a dict to be quoted.
    for k in {"query_dict", "param_dict"} & keys:
        old_dict, new_dict = url_dict[k], {}  # type: ignore

        for key, value in old_dict.items():
            key = urllib.parse.quote(key)
            if value:
                value = urllib.parse.quote(value)
            new_dict[key] = value

        quoted_dict[k] = new_dict  # type: ignore

    return quoted_dict


# pylint: disable=too-many-instance-attributes
class URL:
    """
    A simple, immutable URL class.

    **URLs and their components**

    URLs, as represented by this class, take the following general form (as
    outlined by [RFC1738](https://datatracker.ietf.org/doc/html/rfc1738) and
    [RFC3986](https://datatracker.ietf.org/doc/html/rfc3986)):

    ```plaintext
    [scheme:][//[username[:password]@]host[:port]][path][;parameters][?query][#fragment]
    ```

    Some combinations of components also have represenations:
     - `URL.userinfo`
     - `URL.netloc`

    **Construction and use**

    The constructor can take a URL string, URL components as key word arguments,
    or a mixture of both (keyword arguments will override the URL string):

    ```python
    >>> URL('http://example.com')
    imurl.URL('http://example.com')
    >>> URL(scheme="https", host="example.com")
    imurl.URL('http://example.com')
    >>> URL("http://google.com", host="example.com", path="/some/path")
    imurl.URL('http://example.com/some/path')
    ```

    As `URL` objects are immutable, a handy `URL.replace` method (which takes
    the same arguments as the constructor) will create a new `URL` by replacing
    parts from the original `URL` (similarly to how [`datetime`](
        https://docs.python.org/3/library/datetime.html#datetime.date.replace)
    work in the stdlib):

    ```python
    >>> URL("http://example.com").replace(path="/index.html")
    imurl.URL('http://example.com/index.html')
    ```

    Most URL components need to be strings or `None`, with the exception of:
     - `URL.port`, which can be an `int` or `None`
     - `URL.path`, which can be a `str`, [`PurePosixPath`](
       https://docs.python.org/3/library/pathlib.html#pathlib.PurePosixPath)
       or `None`
     - `URL.query` and `URL.parameters` (see below).

    **URL encoding**

    Many special characters are supposed to be '% encoded' in URLs. With the
    `quote_components` flag set, keyword args to the constructor and to
    `replace` are percent encoded using [`urllib.parse.quote`](
        https://docs.python.org/3/library/urllib.parse.html#urllib.parse.quote).
    This is set to `True` by default for the constructor, and `False` for
    arguments to `replace`.

    ```python
    >>> u = URL("https://example.com)
    >>> u.replace(path="/some/path with spaces", quote_components=True)
    imurl.URL('https://example.com/some/path%20with%20spaces')
    >>> u.replace(path="/some/path with spaces", quote_components=False)
    imurl.URL('https://example.com/some/path with spaces')
    ```

    **Working with query/path parameters**

    Path parameters and query parameters are parts of the URL which can
    be used to represent key-value data.

    This is an example of a URL with a scheme, host and path:

    ```plaintext
    scheme://some-host.com/path/to/somewhere
    ```

    Path parameters come after the path section of the URL These are not commonly
    used in modern URL schemes, but have some historical significance. They're
    typically delimited using a semicolon, but some examples use a comma.
    This delimiter can be configured by changing `URL.param_delimiter`:

    ```plaintext
    scheme://some-host.com/path/to/somewhere;these=are;path=params
    ```

    Query parameters come after the path section of the URL *and* after
    the path parameters. The query section starts with a question mark,
    and then uses a delimiter between key-value pairs (typically an ampersand,
    though this can be configured by changing `URL.query_delimiter`):

    ```plaintext
    scheme://some-host.com/path/to/somewhere?these=are&query=params
    scheme://some-host.com/path/to/somewhere;path=params?query=params
    ```

    Since these typically represent key-value data, `imurl` considers them to be
    string-string mappings instead of strings, and they are set/accessed as such.
    In the constructor/`replace`, these are passed as `param_dict` and `query_dict`.

    ```python
    >>> u = URL("https://example.com", query_dict={"query": "param"))
    >>> u
    imurl.URL('https://example.com?query=param')
    >>> u.query
    'query=param'
    >>> u.query_dict
    {'query': 'param'}
    >>> u.get_query('query'):
    'param'
    ```

    Additionally, if the values are set to `None`, the keys appear without '=value':

    ```python
    >>> u = URL("https://example.com/")
    >>> u.replace(param_dict={"key": None})
    imurl.URL('https://example.com/;key')
    >>> u.replace(query_dict={"key": None})
    imurl.URL('https://example.com/?key')
    ```

    Since these components are quite 'special', there are some extra methods to
    work with them.

    The following properties are available:

     - `query` / `parameters`: the string form of these components.
     - `query_dict` / `param_dict`: copies of the dictionaries.

    And the following methods are available:

     - `has_query` / `has_parameter`: get whether the given key is in the dict.
     - `get_query` / `get_parameter`: get the value from the key.
     - `set_query` / `set_parameter`: add/modify a key/value pair, getting
       a new URL.
     - `delete_query` / `delete_parameter`: remove a k/v pair, getting a new
       URL.

    """

    # pylint: disable=too-many-arguments,too-many-locals
    def __init__(
        self,
        url_string: Optional[str] = None,
        *,
        scheme: Optional[str] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
        host: Optional[str] = None,
        port: Optional[int] = None,
        path: Optional[Union[str, PurePosixPath]] = None,
        param_dict: Optional[MutableMapping[str, Optional[str]]] = None,
        param_delimiter: str = ";",
        query_dict: Optional[MutableMapping[str, Optional[str]]] = None,
        query_delimiter: str = "&",
        fragment: Optional[str] = None,
        quote_components: bool = True,
    ):
        self.scheme = scheme
        """The 'scheme' component of the URL (e.g. 'http')."""
        self.username = username
        """The 'username' component of the URL."""
        self.password = password
        """The 'password' component of the URL."""
        self.host = host
        """The 'host' component of the URL (AKA the domain, e.g. 'example.com')."""
        self.port = port
        """The port component of the URL (e.g. 8080)."""
        if isinstance(path, PurePosixPath):
            path = str(path)
        self.path = path
        """The 'path' component of the URL. Usually a POSIX path."""
        self._param_dict = param_dict or {}
        """The path parameters from the URL."""
        self.param_delimiter = param_delimiter
        """The delimiter for the path parameters. Usually ';'."""
        self._query_dict = query_dict or {}
        """The query parameters from the URL."""
        self.query_delimiter = query_delimiter
        """The delimiter for the path parameters. Usually '&'."""
        self.fragment = fragment
        """The fragment component of the URL (e.g. 'some-html-tag')"""

        # Perform percent encoding.
        if quote_components:
            url = self.from_dict(_encode_url_dict(self.to_dict()))

            self.__dict__ = url.__dict__
            object.__setattr__(self, "_frozen", False)

        if url_string:
            # Read in the URL string.
            # This needs to be done post-quoting to ensure we don't
            # double percent encode any components.
            url = self.from_url_string(url_string, query_delimiter, param_delimiter)

            # Apply changes from the kwargs to the URL parsed from
            # the URL string.
            dict_from_kwargs = self.to_dict()
            url = url.replace(**dict_from_kwargs)  # type: ignore

            self.__dict__ = url.__dict__
            object.__setattr__(self, "_frozen", False)

        self._frozen = True

    @property
    def path_as_posix(self) -> Optional[PurePosixPath]:
        """
        The URL path as a [`pathlib.PurePosixPath`](
            https://docs.python.org/3/library/pathlib.html#pathlib.PurePosixPath).
        This can be really useful for transforming the path component of a HTTP url:

        ```python
        >>> u = URL("https://example.com/some/path")
        >>> u.replace(path=u.path_as_posix.parent)
        imurl.URL('https://example.com/some')
        ```

        """
        if not self.path:
            return None
        return PurePosixPath(self.path)

    @property
    def parameters(self) -> Optional[str]:
        """The URL's path parameters as a string."""
        if not self._param_dict:
            return None

        items = [k if v is None else f"{k}={v}" for k, v in self._param_dict.items()]
        return self.param_delimiter.join(items)

    @property
    def param_dict(self) -> MutableMapping[str, Optional[str]]:
        """A copy of the path parameter dictionary."""
        return copy(self._param_dict)

    @property
    def query(self) -> Optional[str]:
        """The URL query parameters as a string."""
        if not self._query_dict:
            return None

        items = [k if v is None else f"{k}={v}" for k, v in self._query_dict.items()]
        return self.query_delimiter.join(items)

    @property
    def query_dict(self) -> MutableMapping[str, Optional[str]]:
        """A copy of the query parameter dictionary."""
        return copy(self._query_dict)

    @property
    def userinfo(self) -> Optional[str]:
        """
        The URL's `userinfo` component.

        This is a composite of the username and password:

        ```plaintext
        username[:password]
        ```

        """
        if not self.username:
            return None

        components = []
        components.append(self.username)
        if self.password:
            components.append(":")
            components.append(self.password)

        return "".join(components)

    @property
    def netloc(self) -> Optional[str]:
        """
        The URL's network location component.

        This is a composite of the userinfo, the host, and the port:

        ```plaintext
        [userinfo@]host[:port]
        ```
        """
        if self.host is None:
            return None
        if not self.host:
            return ""

        components = []
        userinfo = self.userinfo
        if userinfo is not None:
            components.append(userinfo)
            components.append("@")

        components.append(self.host)

        if isinstance(self.port, int):  # 0 is okay too.
            components.append(":")
            components.append(str(self.port))

        return "".join(components)

    @property
    def url(self) -> str:
        """
        The complete URL, as a string, built up from the components:

        ```plaintext
        [scheme:][//netloc][path][;parameters][?query][#fragment]
        ```
        """
        components = []

        if self.scheme:
            components.append(self.scheme)
            components.append(":")

        netloc = self.netloc
        if netloc is not None:
            components.append("//")
            components.append(netloc)

        if self.path:
            components.append(self.path)

        params, query = self.parameters, self.query
        if params:
            components.append(self.param_delimiter)
            components.append(params)
        if query:
            components.append("?")
            components.append(query)
        if self.fragment:
            components.append("#")
            components.append(self.fragment)
        return "".join(components)

    def replace(
        self,
        *,
        quote_components: bool = False,
        **url_dict: Union[str, MutableMapping[str, Optional[str]], None],
    ) -> "URL":
        """
        Create a new `URL` by replacing attributes of the current `URL`.

        This method takes the same keyword arguments as the constructor,
        but does not accept the URL string.

        """
        dictionary = self.to_dict()
        if quote_components:
            url_dict = _encode_url_dict(url_dict)  # type: ignore
        dictionary.update(url_dict)  # type: ignore
        return self.from_dict(dictionary)

    def has_parameter(self, key: str) -> bool:
        """Return whether a given key is a URL path parameter."""
        return key in self._param_dict

    def get_parameter(self, key: str, unquote: bool = True) -> Optional[str]:
        """Given a path parameter key, return the parameter value."""
        value = self._param_dict[key]
        if unquote and value is not None:
            return urllib.parse.unquote(value)
        return value

    def set_parameter(self, key: str, value: Optional[str]) -> "URL":
        """
        Given a path parameter key and a value to add/replace, return a new `URL`
        with that parameter set.

        """
        new_params = copy(self._param_dict)
        new_params[key] = value
        return self.replace(param_dict=new_params)

    def delete_parameter(self, key: str) -> "URL":
        """
        Given a path parameter key, return a new `URL` without that parameter.

        """
        new_params = copy(self._param_dict)
        del new_params[key]
        return self.replace(param_dict=new_params)

    def has_query(self, key: str) -> bool:
        """Return whether a given key is in the URL query parameters."""
        return key in self._query_dict

    def get_query(self, key: str, unquote: bool = True) -> Optional[str]:
        """Given a query parameter key, return the query value."""
        value = self._query_dict[key]
        if unquote and value is not None:
            return urllib.parse.unquote(value)
        return value

    def set_query(self, key: str, value: Optional[str]) -> "URL":
        """
        Given a query parameter key and a value to add/replace, return a new `URL`
        with that query parameter set.

        """
        new_query = copy(self._query_dict)
        new_query[key] = value
        return self.replace(query_dict=new_query)

    def delete_query(self, key: str) -> "URL":
        """Given a query parameter key, return a new `URL` without that query."""
        new_query = copy(self._query_dict)
        del new_query[key]
        return self.replace(query_dict=new_query)

    @classmethod
    def from_dict(cls, dictionary: URLDict) -> "URL":
        """Deserialize the URL from a dict."""
        return cls(**dictionary, quote_components=False)

    def to_dict(self) -> URLDict:
        """Serialize the URL to a dict."""
        dictionary = URLDict()

        fields = URL_COMPONENTS & set(self.__dict__.keys())
        for field in fields:
            value = self.__dict__[field]
            if value is not None:
                dictionary[field] = value  # type: ignore

        for field in ("query_dict", "param_dict"):
            value = self.__dict__[f"_{field}"]
            if value:
                dictionary[field] = value  # type: ignore

        return dictionary

    @classmethod
    def from_url_string(
        cls, url: str, query_delimiter: str = "&", param_delimiter: str = ";",
    ) -> "URL":
        """
        Create a `URL` class from a URL string. This isn't perfect - two valid
        sets of URL components can result in the same string.

        At present this involves quite a bit of hacking the standard library's
        `urllib.parse.urlparse`, and could probably do with a rewrite.

        """
        # TL;DR: parsing non-trivial URLs is really hard.
        parsed_url = urllib.parse.urlparse(url)

        # The URL format is ambiguous if there's no scheme.
        # It's easy to get path and host mixed up. The rules we use here are:
        #  - If there's only one of path and host, and it starts with a slash,
        #    it's a path.
        #  - If there's a slash in a host, it's actually a combined host and
        #    path.
        path, host = parsed_url.path or "", parsed_url.hostname or ""
        if not parsed_url.scheme:
            if host.startswith("/") and not path:
                path, host = host, path

            if "/" in host and not path:
                host, *path_components = host.split("/")
                path = "/" + "/".join(path_components)

        # In URLs with parameters and an empty path, urlparse is unable to
        # parse the port.
        try:
            port, params = parsed_url.port, parsed_url.params
        except ValueError as err:
            message = str(err)
            if not message.startswith("Port could not be cast to integer value"):
                raise

            unparsed_port_string = message.split("'")[1]
            port_str, *params_list = unparsed_port_string.split(param_delimiter)
            try:
                port = int(port_str)
            except ValueError as new_err:
                message = f"Port could not be cast to integer value as {port_str!r}"
                raise ValueError(message) from new_err
            params = param_delimiter.join(params_list)

        # Capture URL query parameters as dict: ';key=value' -> {'key': 'value'}.
        # Keys without values are stored with 'None' as the value.
        query = {}
        if parsed_url.query:
            query_string = parsed_url.query.lstrip("?")

            for item in query_string.split(query_delimiter):
                key: str
                value: Optional[str]

                try:
                    key, value = item.split("=")
                except ValueError:
                    key, value = item, None
                query[key] = value

        # And the same with path parameters.
        parameters = {}
        if params:
            param_string = params.lstrip(param_delimiter)

            for item in param_string.split(param_delimiter):
                try:
                    key, value = item.split("=")
                except ValueError:
                    key, value = item, None
                parameters[key] = value

        return cls(
            scheme=parsed_url.scheme or None,
            username=parsed_url.username,
            password=parsed_url.password,
            host=host,
            port=port,
            path=path or None,
            param_dict=parameters,
            param_delimiter=param_delimiter,
            query_dict=query,
            query_delimiter=query_delimiter,
            fragment=parsed_url.fragment or None,
            quote_components=False,
        )

    def __hash__(self) -> int:
        return hash(json.dumps(self.__dict__))

    def __str__(self) -> str:
        return self.url

    def __repr__(self) -> str:
        url = self.url
        if not url:
            return "imurl.URL()"
        return f"imurl.URL({url!r})"

    def __eq__(self, other: object) -> bool:
        # Allow equality comparisons with strings.
        if not isinstance(other, URL):
            return False
        return self.url == other.url

    def __setattr__(self, attr: str, value: Any):
        # Ensuring we can freeze instances after instantiation.
        if not getattr(self, "_frozen", False):
            super().__setattr__(attr, value)
        else:
            name = repr(self.__class__.__name__)
            if hasattr(self, attr):
                raise AttributeError(f"{name} object attribute {attr!r} is read-only")
            raise AttributeError(f"{name} object has no attribute {attr!r}")
