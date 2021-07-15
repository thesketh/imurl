"""The URL class."""
import json
import urllib.parse
from copy import deepcopy
from pathlib import PurePosixPath
from typing import (
    Any,
    Iterable,
    Iterator,
    MutableMapping,
    Optional,
    List,
    TypedDict,
    Tuple,
    Union,
)

__all__ = ["URL", "URLDict"]


ParameterValue = Union[str, None, List[Optional[str]]]
Parameters = MutableMapping[str, ParameterValue]


class URLDict(TypedDict, total=False):
    """A typed dictionary of URL components."""

    scheme: Optional[str]
    username: Optional[str]
    password: Optional[str]
    host: Optional[str]
    port: Optional[int]
    path: Optional[Union[str, PurePosixPath]]
    param_dict: Parameters
    param_delimiter: str
    query_dict: Parameters
    query_delimiter: str
    fragment: Optional[str]


URL_COMPONENTS = set(URLDict.__annotations__.keys())  # pylint: disable=no-member


def _unencode_url_dict(url_dict: URLDict) -> URLDict:
    """Undo URL percent-endoding to a `URLDict`."""
    quoted_dict = URLDict()
    keys = set(url_dict.keys())

    # Keys which don't require quoting.
    for k in {"port", "param_delimiter", "query_delimiter"} & keys:
        quoted_dict[k] = url_dict[k]  # type: ignore

    # Keys which _do_ require quoting.
    for k in {"scheme", "username", "password", "host", "path", "fragment"} & keys:
        quoted_dict[k] = urllib.parse.unquote(url_dict[k])  # type: ignore

    # Keys which need all the items in a dict to be quoted.
    for k in {"query_dict", "param_dict"} & keys:
        old_dict, new_dict = url_dict[k], {}  # type: ignore

        for key, value in old_dict.items():
            key = urllib.parse.unquote(key)

            if isinstance(value, list):
                new_values: List[Optional[str]] = []
                for sub_value in value:
                    if sub_value is not None:
                        sub_value = urllib.parse.unquote(sub_value)
                    new_values.append(sub_value)

                value = new_values
            elif isinstance(value, str):
                value = urllib.parse.unquote(value)

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

    Some components behave differently if there is an empty string or if
    there is a true `None` value. For instance, in a file URI, the URL will
    appear differently if `url.host` is not None:

    ```python
    >>> u = URL(scheme="file", path="/some/path/on/disk")
    >>> u
    imurl.URL("file:/some/path/on/disk")
    >>> u.replace(host="")
    imurl.URL("file:///some/path/on/disk")
    ```

    **URL encoding**

    Many special characters are supposed to be '% encoded' in URLs. With the
    `components_encoded` flag set to `False` (the default), keyword args to the
    constructor and to `replace` are percent encoded using [`urllib.parse.quote`](
        https://docs.python.org/3/library/urllib.parse.html#urllib.parse.quote).
    URLs are always assumed to be pre-encoded.

    Data is stored in the class in its unencoded form, and encoded only when
    composite components are encoded (e.g. `userinfo`, `netloc`, `url`)

    ```python
    >>> u = URL("https://example.com)
    >>> u.replace(path="/some/path with spaces")
    imurl.URL('https://example.com/some/path%20with%20spaces')
    >>> u.replace(path="/some/path%20with%20spaces")
    imurl.URL('https://example.com/some/path%2520with%2520spaces')
    >>> u.replace(path="/some/path%20with%20spaces", components_encoded=True)
    imurl.URL('https://example.com/some/path%20with%20spaces')
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

    Repeated query/path parameters can also be specified. These work with `None`
    values the same way that single values do.

    ```python
    >>> u = URL("https://example.com/?query=a&query=list&query=of&query=params")
    >>> u.get_query("query")
    ['a', 'list', 'of', 'params']
    >>> u.query_dict
    {"query": ['a', 'list', 'of', 'params']}
    ```

    Since these components are quite 'special', there are some extra methods to
    work with them.

    The following properties are available:

     - `query` / `parameters`: encoded strings of the components.
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
        url: Optional[Union["URL", str]] = None,
        *,
        scheme: Optional[str] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
        host: Optional[str] = None,
        port: Optional[int] = None,
        path: Optional[Union[str, PurePosixPath]] = None,
        param_dict: Optional[Parameters] = None,
        param_delimiter: str = ";",
        query_dict: Optional[Parameters] = None,
        query_delimiter: str = "&",
        fragment: Optional[str] = None,
        components_encoded: bool = False,
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

        # Undo percent encoding.
        if components_encoded:
            quoted_url = self.from_dict(_unencode_url_dict(self.to_dict()))

            self.__dict__ = quoted_url.__dict__
            object.__setattr__(self, "_frozen", False)

        if url:
            # Read in the URL.
            # This needs to be done post-quoting to ensure we don't
            # double percent encode any components.
            if isinstance(url, str):
                url = self.from_url_string(url, query_delimiter, param_delimiter)

            if not isinstance(url, URL):
                raise TypeError("URL must be string or `imurl.URL`.")

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
    def param_dict(self) -> Parameters:
        """A copy of the path parameter dictionary."""
        return deepcopy(self._param_dict)

    @property
    def query_dict(self) -> Parameters:
        """A copy of the query parameter dictionary."""
        return deepcopy(self._query_dict)

    @property
    def userinfo(self) -> Optional[str]:
        """
        The URL's `userinfo` component.

        This is a composite of the username and password:

        ```plaintext
        username[:password]
        ```

        This is returned in a URL encoded form.

        """
        if not self.username:
            return None

        components = []
        components.append(urllib.parse.quote(self.username))
        if self.password:
            components.append(":")
            components.append(urllib.parse.quote(self.password))

        return "".join(components)

    @property
    def netloc(self) -> Optional[str]:
        """
        The URL's network location component.

        This is a composite of the userinfo, the host, and the port:

        ```plaintext
        [userinfo@]host[:port]
        ```

        This is returned in a URL encoded form.

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

        components.append(urllib.parse.quote(self.host))

        if isinstance(self.port, int):  # 0 is okay too.
            components.append(":")
            components.append(str(self.port))

        return "".join(components)

    @property
    def parameters(self) -> Optional[str]:
        """The URL's path parameters, encoded as they are in the URL."""
        return self._build_k_v_string(self._param_dict, self.param_delimiter)

    @property
    def query(self) -> Optional[str]:
        """The URL's query parameters, encoded as they are in the URL."""
        return self._build_k_v_string(self._query_dict, self.query_delimiter)

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
            components.append(urllib.parse.quote(self.scheme))
            components.append(":")

        netloc = self.netloc
        if netloc is not None:
            components.append("//")
            components.append(netloc)

        if self.path:
            components.append(urllib.parse.quote(self.path))

        parameters = self.parameters
        if parameters:
            components.append(self.param_delimiter)
            components.append(parameters)

        query = self.query
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
        components_encoded: bool = False,
        **url_dict: Optional[Union[str, Parameters, PurePosixPath]],
    ) -> "URL":
        """
        Create a new `URL` by replacing attributes of the current `URL`.

        This method takes the same keyword arguments as the constructor,
        but does not accept the URL string.

        """
        dictionary = self.to_dict()
        if components_encoded:
            url_dict = _unencode_url_dict(url_dict)  # type: ignore
        dictionary.update(url_dict)  # type: ignore
        return self.from_dict(dictionary)

    def has_parameter(self, key: str) -> bool:
        """Return whether a given key is a URL path parameter."""
        return key in self._param_dict

    def get_parameter(self, key: str) -> ParameterValue:
        """Given a path parameter key, return a copy of the parameter value."""
        return deepcopy(self._param_dict[key])

    def set_parameter(self, key: str, value: ParameterValue) -> "URL":
        """
        Given a path parameter key and a value to add/replace, return a new `URL`
        with that parameter set.

        """
        new_params = deepcopy(self._param_dict)
        new_params[key] = value
        return self.replace(param_dict=new_params)

    def delete_parameter(self, key: str) -> "URL":
        """
        Given a path parameter key, return a new `URL` without that parameter.

        """
        new_params = deepcopy(self._param_dict)
        del new_params[key]
        return self.replace(param_dict=new_params)

    def has_query(self, key: str) -> bool:
        """Return whether a given key is in the URL query parameters."""
        return key in self._query_dict

    def get_query(self, key: str) -> ParameterValue:
        """Given a query parameter key, return a copy of the query value."""
        return deepcopy(self._query_dict[key])

    def set_query(self, key: str, value: Optional[str]) -> "URL":
        """
        Given a query parameter key and a value to add/replace, return a new `URL`
        with that query parameter set.

        """
        new_query = deepcopy(self._query_dict)
        new_query[key] = value
        return self.replace(query_dict=new_query)

    def delete_query(self, key: str) -> "URL":
        """Given a query parameter key, return a new `URL` without that query."""
        new_query = deepcopy(self._query_dict)
        del new_query[key]
        return self.replace(query_dict=new_query)

    @classmethod
    def from_dict(cls, dictionary: URLDict) -> "URL":
        """Deserialize the URL from a dict."""
        return cls(**dictionary, components_encoded=False)

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
                dictionary[field] = deepcopy(value)  # type: ignore

        return dictionary

    @classmethod
    def from_url_string(
        cls,
        url: str,
        query_delimiter: str = "&",
        param_delimiter: str = ";",
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
        # Need examples for these - I triggered it manually before but can't
        # find the URL I used.
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
            if not message.startswith(
                "Port could not be cast to integer"
            ):  # pragma: no cover
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
        param_string = params.lstrip(param_delimiter)
        parameters = cls._parse_k_v_string(param_string, param_delimiter)

        query_string = parsed_url.query.lstrip("?")
        query = cls._parse_k_v_string(query_string, query_delimiter)

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
            components_encoded=True,
        )

    @staticmethod
    def _build_k_v_string(dictionary: Parameters, delimiter: str) -> str:
        """Build a string from an unencoded parameter dict and a delimiter."""
        if not dictionary:
            return ""

        def iterate_k_v_pairs(
            param_seq: Iterable[Tuple[str, ParameterValue]]
        ) -> Iterator[str]:
            """Loop through key/value pairs and yield formatted strings."""
            for key, value in param_seq:
                key = urllib.parse.quote(key)

                if value is None:
                    yield key
                elif isinstance(value, list):
                    iterable = ((key, sub_value) for sub_value in value)
                    for string in iterate_k_v_pairs(iterable):
                        yield string
                else:
                    value = urllib.parse.quote(str(value))
                    yield f"{key}={value}"

        items = iterate_k_v_pairs(dictionary.items())
        return delimiter.join(items)

    @staticmethod
    def _parse_k_v_string(string: str, delimiter: str) -> Parameters:
        """Parse a string into an unencoded parameter dict, given a delimiter."""
        dictionary: Parameters = {}

        for item in string.split(delimiter):
            key: str
            value: Optional[str]

            try:
                key, value = item.split("=")
                value = urllib.parse.unquote(value)
            except ValueError:
                key, value = item, None

            key = urllib.parse.unquote(key)

            if key not in dictionary:
                dictionary[key] = value
            else:
                current_value = dictionary[key]

                if isinstance(current_value, list):
                    current_value.append(value)
                else:
                    dictionary[key] = [current_value, value]

        return dictionary

    def __str__(self) -> str:
        return self.url

    def __repr__(self) -> str:
        url = self.url
        if not url:
            return "imurl.URL()"
        return f"imurl.URL({url!r})"

    def __hash__(self) -> int:
        return hash(json.dumps(self.__dict__))

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, URL):
            return False
        return hash(self) == hash(other)

    def __setattr__(self, attr: str, value: Any):
        # Ensuring we can freeze instances after instantiation.
        if not getattr(self, "_frozen", False):
            super().__setattr__(attr, value)
        else:
            name = repr(self.__class__.__name__)
            if hasattr(self, attr):
                raise AttributeError(f"{name} object attribute {attr!r} is read-only")
            raise AttributeError(f"{name} object has no attribute {attr!r}")

    def __bool__(self) -> bool:
        if self.url:
            return True
        return False
