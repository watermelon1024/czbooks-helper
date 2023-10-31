import re

import aiohttp

RE_BOOK_CODE = re.compile(r"(czbooks\.net\/n\/)([a-z0-9]+)")
RE_CHINESE_CHARS = re.compile(r"[\u4e00-\u9fa5]")

# search by name: s, hashtag: hashtag, author: a
DICT_SEARCH_BY = {
    "name": "s",
    "hashtag": "hashtag",
    "author": "a",
}
RE_WHITESPACE_CHAR = re.compile(r"\s")

# crawler
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"  # noqa
CRAWLER_HEADER = {"User-Agent": USER_AGENT}
DEFAULT_TIMEOUT = aiohttp.ClientTimeout(total=10, connect=5)
