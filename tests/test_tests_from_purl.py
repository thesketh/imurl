# pylint: disable=missing-function-docstring,invalid-name,pointless-statement
# pylint: disable=missing-class-docstring,no-self-use,misplaced-comparison-constant
"""
Tests for the URL. These are taken from the tests for [`purl`](
    https://github.com/codeinthehole/purl), and are modified to make them
applicable to `imurl`. Tests around path segments/lists of query params have
been dropped.

This is the license file from `purl`:

    Copyright (C) 2012 purl authors (see AUTHORS file)

    Permission is hereby granted, free of charge, to any person obtaining a copy of
    this software and associated documentation files (the "Software"), to deal in
    the Software without restriction, including without limitation the rights to
    use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies
    of the Software, and to permit persons to whom the Software is furnished to do
    so, subject to the following conditions:

    The above copyright notice and this permission notice shall be included in all
    copies or substantial portions of the Software.

    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
    FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
    AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
    LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
    OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
    SOFTWARE.

This is the contents of said 'AUTHORS' file at the time of writing:

    David Winterbottom

    Contributors:

    Wolfgang Langner
    xrotwang (https://github.com/xrotwang)
    Przemysław Hejman (https://github.com/mieciu)

"""
import pickle

from imurl import URL


class TestConstructor:
    def test_url_can_be_created_with_just_host(self):
        u = URL(host="google.com")
        assert "//google.com" == str(u)

    def test_url_can_be_created_with_host_and_schema(self):
        u = URL(host="google.com", scheme="https")
        assert "https://google.com" == str(u)

    def test_url_can_be_created_with_host_and_post(self):
        u = URL(host="localhost", port=8000)
        assert "//localhost:8000" == str(u)

    def test_url_can_be_created_with_username_only(self):
        u = URL(
            scheme="postgres",
            username="user",
            host="127.0.0.1",
            port=5432,
            path="/db_name",
        )
        assert "postgres://user@127.0.0.1:5432/db_name" == str(u)

    def test_no_args_to_constructor(self):
        u = URL()
        assert "" == str(u)

    def test_full_url_can_be_used_as_first_param(self):
        u = URL("https://github.com")
        assert "https://github.com" == str(u)

    def test_kwargs_take_priority_when_used_with_full_url(self):
        u = URL("https://github.com", scheme="http")
        assert "http://github.com" == str(u)

    def test_creation_with_host_and_path(self):
        u = URL(host="localhost", path="/boo")
        assert "//localhost/boo" == str(u)

    def test_creation_with_host_and_path_2(self):
        u = URL(host="localhost").replace(path="/boo")
        assert "//localhost/boo" == str(u)


# pylint: disable=too-few-public-methods
class TestMoreFactory:
    def test_extracting_query_param(self):
        url_str = (
            "https://www.sandbox.paypal.com/webscr?cmd=_express-checkout"
            "&token=EC-6469953681606921P&AMT=200&CURRENCYCODE=GBP"
            "&RETURNURL=http%3A%2F%2Fexample.com%2Fcheckout%2Fpaypal%2Fresponse%2Fsuccess%2F"
            "&CANCELURL=http%3A%2F%2Fexample.com%2Fcheckout%2Fpaypal%2Fresponse%2Fcancel%2F"
        )
        u = URL(url_str)
        return_url = u.get_query("RETURNURL")
        assert "http://example.com/checkout/paypal/response/success/" == return_url


class TestFactory:

    url_str = "http://www.google.com/search/?q=testing#fragment"
    url = URL.from_url_string(url_str)

    def test_scheme(self):
        assert "http" == self.url.scheme

    def test_fragment(self):
        assert "fragment" == self.url.fragment

    def test_path(self):
        assert "/search/" == self.url.path

    def test_host(self):
        assert "www.google.com" == self.url.host

    def test_string_version(self):
        assert self.url_str == str(self.url)


class TestEdgeCaseExtraction:
    def test_no_equals_sign_means_none(self):
        url = URL.from_url_string("http://www.google.com/blog/article/1?q")
        assert url.get_query("q") is None

    def test_username_extraction(self):
        url = URL.from_url_string("ftp://user:pw@ftp.host")
        assert "user" == url.username
        assert "pw" == url.password

    def test_username_in_unicode_repr(self):
        u = "ftp://user:pw@ftp.host"
        url = URL.from_url_string(u)
        assert u == str(url)

    def test_auth_in_netloc(self):
        url = URL.from_url_string("ftp://user:pw@ftp.host")
        assert "user:pw@ftp.host" == url.netloc

    def test_auth_with_special_char(self):
        url = URL.from_url_string("ftp://user:b@z@ftp.host")
        assert "user" == url.username
        assert "b@z" == url.password

    def test_port_in_netloc(self):
        url = URL.from_url_string("http://localhost:5000")
        assert "localhost" == url.host
        assert 5000 == url.port

    def test_passwordless_netloc(self):
        url = URL.from_url_string("postgres://user@127.0.0.1:5432/db_name")
        assert "user" == url.username
        assert url.password is None

    def test_unicode_username_and_password(self):
        url = URL.from_url_string("postgres://jeść:niejeść@127.0.0.1:5432/db_name")
        assert "jeść" == url.username
        assert "niejeść" == url.password

    def test_unicode_username_only(self):
        url = URL.from_url_string("postgres://jeść@127.0.0.1:5432/db_name")
        assert "jeść" == url.username
        assert url.password is None

    def test_port_for_https_url(self):
        url = URL.from_url_string("https://github.com")
        assert None is url.port


class TestSimpleExtraction:
    url = URL.from_url_string("http://www.google.com/blog/article/1?q=testing")

    def test_has_actual_param(self):
        assert self.url.has_query("q") is True

    def test_remove_query_param(self):
        new_url = self.url.delete_query("q")
        assert "http://www.google.com/blog/article/1" == str(new_url)

    def test_has_param_negative(self):
        assert self.url.has_query("r") is False

    def test_netloc(self):
        assert "www.google.com" == self.url.netloc

    def test_port_defaults_to_none(self):
        assert self.url.port is None

    def test_scheme(self):
        assert "http" == self.url.scheme

    def test_host(self):
        assert "www.google.com" == self.url.host

    def test_path(self):
        assert "/blog/article/1" == self.url.path

    def test_query(self):
        assert "q=testing" == self.url.query

    def test_query_params(self):
        assert {"q": "testing"} == self.url.query_dict

    def test_parameter_extraction(self):
        assert "testing" == self.url.get_query("q")


class TestBuilder:
    def test_setting_list_as_query_params(self):
        first = URL.from_url_string("?q=testing")
        second = URL().replace(query_dict=first.query_dict)
        assert first.query == second.query

    def test_set_fragment(self):
        url = URL.from_url_string("http://www.google.com/").replace(fragment="hello")
        assert "hello" == url.fragment

    def test_set_scheme(self):
        url = URL.from_url_string("http://www.google.com/").replace(scheme="https")
        assert "https" == url.scheme

    def test_set_host(self):
        url = URL.from_url_string("http://www.google.com/").replace(
            host="maps.google.com"
        )
        assert "maps.google.com" == url.host

    def test_set_path(self):
        url = URL.from_url_string("http://www.google.com/").replace(path="/search")
        assert "/search" == url.path

    def test_set_path_with_special_chars(self):
        url = URL.from_url_string("http://www.google.com/").replace(
            path="/search something"
        )
        assert url.url == "http://www.google.com/search%20something"

    def test_set_query(self):
        url = URL.from_url_string("http://www.google.com/").replace(
            query_dict={"q": "testing"}
        )
        assert "q=testing" == url.query

    def test_set_port(self):
        url = URL.from_url_string("http://www.google.com/").replace(port=8000)
        assert 8000 == url.port

    def test_set_query_param(self):
        url = URL.from_url_string("http://www.google.com/search").set_query(
            "q", "testing"
        )
        assert "testing" == url.get_query("q")

    def test_remove_port(self):
        url = URL("https://example.com:8000/hello?x=100")
        new = url.replace(port=None)
        assert "https://example.com/hello?x=100" == str(new)


class TestMisc:
    def test_url_can_be_used_as_key_in_dict(self):
        u = URL.from_url_string("http://google.com")
        {u: 0}

    def test_equality_comparison(self):
        assert URL.from_url_string("http://google.com") == URL.from_url_string(
            "http://google.com"
        )

    def test_negative_equality_comparison(self):
        assert URL.from_url_string("http://google.com") != URL.from_url_string(
            "https://google.com"
        )

    def test_urls_are_hashable(self):
        u = URL.from_url_string("http://google.com")
        hash(u)

    def test_urls_can_be_pickled(self):
        u = URL.from_url_string("http://google.com")
        pickle.dumps(u)

    def test_urls_can_be_pickled_and_restored(self):
        u = URL.from_url_string("http://google.com")
        pickled = pickle.dumps(u)
        v = pickle.loads(pickled)
        assert u == v
