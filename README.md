[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Linter: pylint](https://img.shields.io/badge/linter-pylint-09BB44.svg)](https://github.com/PyCQA/pylint)
[![Checked with mypy](http://www.mypy-lang.org/static/mypy_badge.svg)](http://mypy-lang.org/)

`imurl` is an immutable URL library, written in modern Python.

`imurl` is inspired by both [`purl`](https://github.com/codeinthehole/purl) and Python's [`pathlib`](https://docs.python.org/3/library/pathlib.html)
and [`datetime`](https://docs.python.org/3/library/datetime.html) modules. It aims to provide a simple, immutable data structure to represent 
URL structures, with support for a wide range of URL/URI schemes.

## Examples

Here are some quick examples for `imurl`. [There are more in the documentation](
    https://thesketh.github.io/imurl/imurl/url.html#URL).

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

## How does `imurl` differ from the alternatives?

`imurl` aims to be a clean, pythonic API around URL manipulation. It should be easier
than using `urllib.parse.urlparse`, and just as flexible as anything you'd roll yourself.

`imurl` is written with modern Python, with all the advantages that brings: static analysis
tools (`mypy`, `pylint`) are used to increase code quality, and the project's style is very consistent
(`black`). These tools should help to reduce bugs once `imurl` is out of the alpha stage.

Alternatives:
 - [`urllib.parse.urlparse`](https://docs.python.org/3/library/urllib.parse.html#urllib.parse.urlparse)
   is the standard library approach to URL parsing. Flexible, but manual. There's very little in the
   way of convenience.
 - [`furl`](https://github.com/gruns/furl)
   is a mutable URL parsing library. Furl is flexible and easily understood, but unfortunately mutable.
 - [`purl`](https://github.com/codeinthehole/purl)
   is the original immutable URL parsing library for Python. `purl` did a lot to inspire `imurl`:
   URLs are immutable, the jQuery-like approach (though nonstandard) feels intuitive, and it's
   relatively stable. `purl` doesn't handle file-like URLs particularly well (those without a host)
   and unfortunately is not currently typed. `purl` is recommended whilst imurl is in alpha. 

## Installation

`imurl` can be installed with `pip`, and has been tested on Python 3.8. `imurl` is still
alpha software, and should be considered unstable:

```
pip install imurl
```
