from typing import Literal

from .const import DICT_SEARCH_BY
from .utils import get_code, now_timestamp, is_out_of_date
from .http import fetch_as_html


class SearchResult:
    def __init__(self, book_title: str, code: str) -> None:
        self.book_title = book_title
        self.code = code

    def __eq__(self, __value: object) -> bool:
        if isinstance(__value, SearchResult):
            return self.code == __value.code
        return False

    def __hash__(self) -> int:
        return hash(self.code)


async def search(
    keyword: str,
    by: Literal["name", "hashtag", "author"] = "name",
    page: int = 1,
) -> list[SearchResult] | None:
    if not (_by := DICT_SEARCH_BY.get(by)):
        raise ValueError(f'Unknown value "{by}" of by')
    soup = await fetch_as_html(f"https://czbooks.net/{_by}/{keyword}/{page}")

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
    name: str = None,
    hashtag: str | list[str] = None,
    author: str = None,
    timeout: float = 30,
) -> list[SearchResult]:
    start = now_timestamp()
    if not isinstance(hashtag, list):
        hashtag = [hashtag]
    name_set: set[SearchResult] = set() if name else None
    hashtag_set: list[set[SearchResult]] = (
        [set() for _ in range(len(hashtag))] if hashtag else None
    )
    author_set: set[SearchResult] = set() if author else None
    page = 1
    while True:
        if name:
            if novel := await search(name, "name", page):
                name_set.update(novel)
        if hashtag:
            for index, hashtag_ in enumerate(hashtag):
                if novel := await search(hashtag_, "hashtag", page):
                    hashtag_set[index].update(novel)
        if author:
            if novel := await search(author, "author", page):
                author_set.update(novel)

        sets = [
            set_ for set_ in [name_set, *hashtag_set, author_set] if set_ is not None
        ]
        result = sets[0].intersection(*sets[1:])
        if len(result) >= 20 or page >= 20 or is_out_of_date(start, timeout):
            break
        else:
            page += 1

    return list(result)
