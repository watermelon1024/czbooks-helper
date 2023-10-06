"""
Czbooks Crawler
~~~~~~~~~~~~~~~

A basic module for czbooks.net

Only for educational purposes.
Made by @watermelon1024
"""


# flake8: noqa: F401
from . import utils
from .api import fetch_book
from .comment import Comment
from .czbook import Novel, load_from_json, get_code
from .error import NotFoundError
from .get_content import GetContentState
from .http import HyperLink
from .search import SearchResult, search, search_advance
