"""A URL class, implemented in pure Python."""
from typing import Any, Dict, Optional
import urllib.parse


# pylint: disable=too-many-instance-attributes,too-many-locals
class URL:
    """
    A URL class, inspired by [`purl`](https://github.com/codeinthehole/purl) and
    [`pathlib`](https://docs.python.org/3/library/pathlib.html).

    """

    def __init__(
        self,
        url: Optional[str] = None,
        *,
        scheme: Optional[str] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
        host: Optional[str] = None,
        port: Optional[int] = None,
        path: Optional[str] = None,
        parameters: Optional[Dict[str, str]] = None,
        param_delimiter: str = ";",
        query: Optional[Dict[str, str]] = None,
        query_delimiter: str = "&",
        fragment: Optional[str] = None,
        quote: bool = True,
    ):
        query_dict = query or {}
        param_dict = parameters or {}

        if quote:
            if scheme:
                scheme = urllib.parse.quote(scheme)
            if username:
                username = urllib.parse.quote(username)
            if password:
                password = urllib.parse.quote(password)
            if host:
                host = urllib.parse.quote(host)
            if path:
                path = urllib.parse.quote(path)

            query_dict, old_query_dict = {}, query_dict
            param_dict, old_param_dict = {}, param_dict

            for new_dict, old_dict in (
                (query_dict, old_query_dict),
                (param_dict, old_param_dict),
            ):
                for key, value in old_dict.items():
                    key = urllib.parse.quote(key)
                    value = urllib.parse.quote(value)
                    new_dict[key] = value

        if url:
            from_url = self.from_url(url, query_delimiter, param_delimiter)

            # Preferrentially take kwargs over URL.
            scheme = scheme or from_url.scheme
            username = username or from_url.username
            password = password or from_url.password
            host = host or from_url.host
            port = port or from_url.port
            path = path or from_url.path
            fragment = fragment or from_url.fragment

            # pylint: disable=protected-access
            query_dict, old_query_dict = from_url._query, query_dict
            # pylint: disable=protected-access
            param_dict, old_param_dict = from_url._parameters, param_dict
            query_dict.update(old_query_dict)
            param_dict.update(old_param_dict)

        self.scheme = scheme or "https"
        self.username = username
        self.password = password
        self.host = host
        self.port = port
        self.path = path
        self._parameters = param_dict
        self.param_delimiter = param_delimiter
        self._query = query_dict
        self.query_delimiter = query_delimiter
        self.fragment = fragment

        self._frozen = True

    @classmethod
    def from_url(cls, url: str, query_delimiter: str = "&", param_delimiter: str = ";"):
        """Create a `URL` class from a URL string."""
        parsed_url = urllib.parse.urlparse(url)
        query, parameters = {}, {}

        if parsed_url.query:
            query_string = parsed_url.query[1:]  # Strip leading '?'

            for item in query_string.split(query_delimiter):
                key, value = item.split("=")
                query[key] = value

        if parsed_url.params:
            param_string = parsed_url.params

            for item in param_string.split(param_delimiter):
                key, value = item.split("=")
                parameters[key] = value

        return cls(
            scheme=parsed_url.scheme,
            username=parsed_url.username,
            password=parsed_url.password,
            host=parsed_url.hostname,
            port=parsed_url.port,
            path=parsed_url.path or None,
            parameters=parameters,
            param_delimiter=param_delimiter,
            query=query,
            query_delimiter=query_delimiter,
            fragment=parsed_url.fragment or None,
            quote=False,
        )

    def __setattr__(self, attr: str, value: Any):
        if not getattr(self, "_frozen", False):
            super().__setattr__(attr, value)
        else:
            name = repr(self.__class__.__name__)
            if hasattr(self, attr):
                raise AttributeError(f"{name} object attribute {attr!r} is read-only")
            else:
                raise AttributeError(f"{name} object has no attribute {attr!r}")

    @property
    def query(self) -> Optional[str]:
        """The URL query string."""
        if not self._query:
            return None

        items = map("=".join, self._query.items())
        return "?" + self.query_delimiter.join(items)

    @property
    def parameters(self) -> Optional[str]:
        """The URL parameters string."""
        if not self._parameters:
            return None

        items = map("=".join, self._parameters.items())
        return ";" + self.param_delimiter.join(items)

    @property
    def netloc(self) -> Optional[str]:
        """The URL's network location."""
        if not self.host:
            return None
        components = []
        if self.username:
            components.append(self.username)
            if self.password:
                components.append(f":{self.password}")
            components.append("@")
        components.append(self.host)
        if self.port:
            components.append(f":{self.port!s}")

        return "".join(components)

    @property
    def url(self) -> str:
        """The complete URL, as a string."""
        components = [f"{self.scheme}://"]

        netloc, params, query = self.netloc, self.parameters, self.query

        if netloc:
            components.append(netloc)
        if self.path:
            components.append(self.path)
        if params:
            components.append(params)
        if query:
            components.append(query)
        if self.fragment:
            components.append(self.fragment)
        return "".join(components)

    def __str__(self) -> str:
        return self.url

    def __repr__(self) -> str:
        return f"imurl.URL({self.url!r})"
