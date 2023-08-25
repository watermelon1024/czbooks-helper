import re

from typing import Literal

import aiohttp

from bs4 import BeautifulSoup

from .color import extract_theme_light_colors_hex, get_img_from_url
from .czbooks import Czbooks, HyperLink
from .time import now_timestamp

re_code = re.compile(r"(czbooks\.net\/n\/)([a-z0-9]+)")


class NotFoundError(Exception):
    """
    Book not found.
    """

    def __init__(self):
        super().__init__()


async def get(link: str) -> str:
    async with aiohttp.request("GET", link) as response:
        text = await response.text()
    return text


async def get_html(link: str) -> BeautifulSoup:
    async with aiohttp.request("GET", link) as response:
        if response.status == 404:
            raise NotFoundError()
        soup = BeautifulSoup(await response.text(), "html.parser")
    return soup


def get_code(s: str) -> str | None:
    if match := re.search(re_code, s):
        return match.group(2)
    return None


async def fetch_book(code: str) -> Czbooks:
    soup = await get_html(f"https://czbooks.net/n/{code}")
    # book state
    state_div = soup.find("div", class_="state")
    state_children = state_div.find_all("td")
    state = state_children[1].text
    last_update = state_children[7].text
    views = state_children[5].text
    category_a = state_children[9].contents[0]
    category = HyperLink(
        category_a.text,
        "https:" + category_a["href"],
    )
    # basic info
    detail_div = soup.find("div", class_="novel-detail")
    title = detail_div.find("span", class_="title").text
    description = detail_div.find("div", class_="description").text
    thumbnail = detail_div.find("img").get("src")
    if thumbnail.startswith("https://img.czbooks.net"):
        theme_colors = extract_theme_light_colors_hex(await get_img_from_url(thumbnail))
    else:
        thumbnail = None
        theme_colors = None
    author_span = detail_div.find("span", class_="author").contents[1]
    author = HyperLink(author_span.text, "https:" + author_span["href"])
    # hashtags
    hashtags = [
        HyperLink(hashtag.text, "https:" + hashtag["href"])
        for hashtag in soup.find("ul", class_="hashtag").find_all("a")[:-1]
    ]
    # chapter list
    chapter_lists = [
        HyperLink(chapter.text, "https:" + chapter["href"])
        for chapter in soup.find("ul", id="chapter-list").find_all("a")
    ]

    book = Czbooks(
        code=code,
        title=title,
        description=description,
        thumbnail=thumbnail,
        theme_colors=theme_colors,
        author=author,
        state=state,
        last_update=last_update,
        views=views,
        category=category,
        content_cache=False,
        words_count=0,
        hashtags=hashtags,
        chapter_list=chapter_lists,
        comments=[],
        last_fetch_time=now_timestamp(),
    )

    return book


# search by name: s, hashtag: hashtag, author: a
BY_DICT = {
    "name": "s",
    "hashtag": "hashtag",
    "author": "a",
}


async def search(
    keyword: str,
    by: Literal["name", "hashtag", "author"],
    page: int = 0,
) -> list[HyperLink]:
    if not (_by := BY_DICT.get(by)):
        raise ValueError(f'Unknown value "{by}" of by')
    soup = await get_html(f"https://czbooks.net/{_by}/{keyword}")
    novel_list_ul = soup.find("ul", class_="nav novel-list style-default").find_all(
        "li", class_="novel-item-wrapper"
    )

    if not novel_list_ul:
        return None

    return [
        HyperLink(
            novel.find("div", class_="novel-item-title").text.strip(),
            get_code(novel.find("a").get("href")),
        )
        for novel in novel_list_ul
    ]
