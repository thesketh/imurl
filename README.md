[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Linter: pylint](https://img.shields.io/badge/linter-pylint-09BB44.svg)](https://github.com/PyCQA/pylint)
[![Checked with mypy](http://www.mypy-lang.org/static/mypy_badge.svg)](http://mypy-lang.org/)

`imurl` is an immutable URL library, written in modern Python.

`imurl` is inspired by both [`purl`](https://github.com/codeinthehole/purl) and Python's [`pathlib`](https://docs.python.org/3/library/pathlib.html).
It aims to maximise simplicity and ease of use, with support for a wide range of URL schemes.

URLs can be created from URL strings, and have the attributes you'd expect:

```python
>>> from imurl import URL
>>> u = URL("https://example.com")
>>> u
imurl.URL('https://example.com')
>>> u.host
'example.com'
>>> u.scheme
'https'
```

URLs are immutable, but components can be replaced similarly to `datetime`/`pathlib` objects:

```python
>>> u.replace(path="/some/path")
imurl.URL('https://example.com/some/path')
>>> u.path  # This is still `None` - we haven't modified `u`.
>>> u.replace(path="/some/path").path_as_posix
PurePosixPath('/some/path')
```

URLs can also be built from components, and query/path parameters can be set/get/deleted:

```python
>>> u = URL(scheme="https", host="google.com", path="/search")
imurl.URL('https://google.com/search')
>>> u2 = u.set_query("q", "a+search+term")
>>> u2
imurl.URL('https://google.com/search?q=a+search+term')
>>> u2.delete_query("q")
imurl.URL('https://google.com/search')
```