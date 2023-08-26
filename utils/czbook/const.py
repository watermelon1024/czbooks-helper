import re

RE_BOOK_CODE = re.compile(r"(czbooks\.net\/n\/)([a-z0-9]+)")
RE_CHINESE_CHARS = re.compile(r"[\u4e00-\u9fa5]")

# search by name: s, hashtag: hashtag, author: a
DICT_SEARCH_BY = {
    "name": "s",
    "hashtag": "hashtag",
    "author": "a",
}
