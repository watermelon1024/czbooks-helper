"""
Czbooks Crawler
~~~~~~~~~~~~~~~

A basic module for czbooks.net

Only for educational purposes.
Made by @watermelon1024
"""


# flake8: noqa: F401
from .api import fetch_book, get_code, search
from .comment import Comment
from .czbook import Czbook, load_from_json
from .error import BookNotFoundError
from .get_content import GetContentState
from .http import HyperLink
