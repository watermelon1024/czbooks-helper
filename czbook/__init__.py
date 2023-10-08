"""
Czbooks Crawler
~~~~~~~~~~~~~~~

A basic module for czbooks.net

Only for educational purposes.
Made by @watermelon1024
"""


# flake8: noqa: F401
from . import utils
from .comment import CommentList, Comment
from .czbook import Novel, fetch_novel
from .error import NotFoundError
from .get_content import GetContentState
from .http import HyperLink
from .search import SearchResult, search, search_advance
