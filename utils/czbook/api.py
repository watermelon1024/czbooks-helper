import re

from typing import TYPE_CHECKING

from .color import extract_theme_light_colors_hex, get_img_from_url
from .const import RE_BOOK_CODE
from .http import HyperLink, get_html
from .timestamp import now_timestamp

if TYPE_CHECKING:
    from .czbook import Czbook


def get_code(s: str) -> str | None:
    if match := re.search(RE_BOOK_CODE, s):
        return match.group(2)
    return None


async def fetch_book(code: str, first: bool = True) -> "Czbook":
    soup = await get_html(f"https://czbooks.net/n/{code}")
    # state
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
    # detail / info
    detail_div = soup.find("div", class_="novel-detail")
    title = detail_div.find("span", class_="title").text
    description = detail_div.find("div", class_="description").text
    thumbnail = detail_div.find("img").get("src")
    if first and thumbnail.startswith("https://img.czbooks.net"):
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
    from .czbook import Czbook

    return Czbook(
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
        word_count=0,
        hashtags=hashtags,
        chapter_list=chapter_lists,
        comments=[],
        last_fetch_time=now_timestamp(),
    )
