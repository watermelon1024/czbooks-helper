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
    page: int = 0,
) -> list[SearchResult] | None:
    if not (_by := DICT_SEARCH_BY.get(by)):
        raise ValueError(f'Unknown value "{by}" of by')
    soup = await get_html(f"https://czbooks.net/{_by}/{keyword}")

    if not (
        novel_list_ul := soup.find(
            "ul", class_="nav novel-list style-default"
        ).find_all("li", class_="novel-item-wrapper")
    ):
        return None

    return [
        SearchResult(
            novel.find("div", class_="novel-item-title").text.strip(),
            get_code(novel.find("a").get("href")),
        )
        for novel in novel_list_ul
    ]
