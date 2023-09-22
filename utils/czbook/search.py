from typing import Literal

from .const import DICT_SEARCH_BY
from .czbook import get_code
from .http import get_html


class SearchResult:
    def __init__(self, book_title: str, code: str) -> None:
        self.book_title = book_title
        self.code = code


async def search(
    keyword: str,
    by: Literal["name", "hashtag", "author"] = "name",
    page: int = 1,
) -> list[SearchResult] | None:
    if not (_by := DICT_SEARCH_BY.get(by)):
        raise ValueError(f'Unknown value "{by}" of by')
    soup = await get_html(f"https://czbooks.net/{_by}/{keyword}/{page}")

    if not (
        novel_list_ul := soup.find(
            "ul", class_="nav novel-list style-default"
        ).find_all("li", class_="novel-item-wrapper")
    ):
        return None

    return [
        SearchResult(
            book_title=novel.find("div", class_="novel-item-title").text.strip(),
            code=get_code(novel.find("a").get("href")),
        )
        for novel in novel_list_ul
    ]


async def search_advance(
    name: str = None, hashtag: str = None, author: str = None
) -> set[SearchResult]:
    name_set: set[SearchResult] = set() if name else None
    hashtag_set: set[SearchResult] = set() if hashtag else None
    author_set: set[SearchResult] = set() if author else None
    page = 1
    while True:
        if name:
            if novel := await search(name, "s", page):
                name_set.update(novel)
        if hashtag:
            if novel := await search(hashtag, "hashtag", page):
                hashtag_set.update(novel)
        if author:
            if novel := await search(author, "a", page):
                author_set.update(novel)

        sets = [set_ for set_ in [name_set, hashtag_set, author_set] is not None]
        result: set[SearchResult] = sets[0].intersection(*sets[1:])
        if len(result) < 20:
            page += 1
        else:
            break

    return result
