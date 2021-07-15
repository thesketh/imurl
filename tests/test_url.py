# pylint: disable=missing-function-docstring,invalid-name,pointless-statement
# pylint: disable=missing-class-docstring,no-self-use,misplaced-comparison-constant
"""
Extra tests for the URL, to capture some functionality that purl doesn't have.

"""
from pathlib import PurePosixPath

import pytest

from imurl import URL


class TestConstructReplace:
    def test_posix_paths(self):
        posix_path = PurePosixPath("/some/path/here")
        u = URL("http://google.com", path=posix_path)
        assert u.path == "/some/path/here"
        assert u.path_as_posix == posix_path

    def test_multiple_query_same_key(self):
        url = URL.from_url_string("http://www.google.com/blog/article/1?q=yes&q=no")
        assert url.get_query("q") == ["yes", "no"]

    def test_multiple_query_same_key_some_none(self):
        url = URL.from_url_string("http://www.google.com/blog/article/1?q=yes&q=no&q")
        assert url.get_query("q") == ["yes", "no", None]

    def test_raise_for_non_url(self):
        with pytest.raises(TypeError):
            URL(2, path=PurePosixPath("/some/path/here"))

    def test_creation_from_url_obj(self):
        u = URL("https://google.com/search?q=some-param")
        assert URL(u) == u

    def test_path_params(self):
        u = URL("https://example.com/;path=param;and=another;nulled")
        assert u.parameters == "path=param;and=another;nulled"
        assert u.param_dict == {"path": "param", "and": "another", "nulled": None}
        assert u.has_parameter("path")
        assert not u.has_parameter("another_path")
        assert u.get_parameter("path") == "param"
        assert u.url == "https://example.com/;path=param;and=another;nulled"
        assert u.set_parameter("path", "changed").get_parameter("path") == "changed"
        assert not u.delete_parameter("nulled").has_parameter("nulled")

    def test_parse_port_params_no_path(self):
        u = URL("http://google.com:80;some-params-here")
        assert u.has_parameter("some-params-here")
        assert u.port == 80

    def test_parse_crap_port_params_no_path_still_errors(self):
        with pytest.raises(ValueError):
            URL("http://google.com:8a;some-params-here")

    def test_replace_with_unencode(self):
        u = URL("https://example.com/path")
        u2 = u.replace(path="/a/path%20with%20spaces", components_encoded=True)
        assert u2.path == "/a/path with spaces"

    def test_multiple_query_params(self):
        u = URL("http://example.com/", query_dict={"query": ["param", "another"]})
        assert str(u) == "http://example.com/?query=param&query=another"


class TestProperties:
    def test_no_path_as_posix(self):
        u = URL("http://example.com")
        assert u.path_as_posix is None

    def test_no_host_no_netloc(self):
        u = URL("file:///some/path/")
        assert u.netloc == ""
        assert u.host == ""
        u = URL("apt:a-package-name")
        assert u.netloc == ""

    def test_mutability_existing_props(self):
        u = URL("http://google.com")
        with pytest.raises(AttributeError):
            u.host = "example.com"

    def test_mutability_new_props(self):
        u = URL()
        with pytest.raises(AttributeError):
            u.a_property = True


class TestMisc:
    def test_repr_no_url(self):
        assert repr(URL()) == "imurl.URL()"

    def test_repr_with_url(self):
        assert repr(URL("https://example.com")) == "imurl.URL('https://example.com')"

    def test_str_no_url(self):
        assert str(URL()) == ""

    def test_equality(self):
        assert URL("example.com") == URL("example.com")
        assert URL("example.com") != "a string"

    def test_bool(self):
        assert bool(URL("example.com")) is True
        assert bool(URL()) is False
