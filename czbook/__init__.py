"""
Czbooks Crawler
~~~~~~~~~~~~~~~

A basic module for czbooks.net

Only for educational purposes.
Made by @watermelon1024
"""


# flake8: noqa: F401
from . import utils
from .novel_info import NovelInfo, Author, Category, Thumbnail
from .novel_info.hashtag import Hashtag, HashtagList
from .chapter import ChapterInfo, ChapterList
from .comment import Comment, CommentList
from .czbook import Novel, fetch_novel
from .error import NotFoundError
from .get_content import GetContentState, GetContent
from .http import HyperLink
from .search import SearchResult, search, search_advance
