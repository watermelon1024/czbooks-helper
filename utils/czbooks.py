import asyncio
import json
import random
import re

from datetime import datetime
from typing import Literal

import aiohttp

from discord import Embed, Interaction, Color, MISSING
from bs4 import BeautifulSoup

from .color import extract_theme_light_colors_hex, get_img_from_url

chinese_char = re.compile(r"[\u4e00-\u9fa5]")
re_code = re.compile(r"(czbooks\.net\/n\/)([a-z0-9]+)")


class NotFoundError(Exception):
    """
    Book not found.
    """

    def __init__(self):
        super().__init__()


def progress_bar(
    current: int,
    total: int,
    bar_length: int = 27,
) -> tuple[float, str]:
    percentage = current / total
    filled_length = int(bar_length * percentage)
    return percentage, f"[{'='*filled_length}{' '*(bar_length-filled_length)}]"


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


class HyperLink:
    def __init__(self, text: str, link: str) -> None:
        self.text = text
        self.link = link

    def __str__(self) -> str:
        return f"[{self.text}]({self.link})"

    def to_dict(self) -> dict:
        return {
            "text": self.text,
            "link": self.link,
        }


class Comment:
    def __init__(
        self,
        author: str,
        message: str,
        date: int,
    ) -> None:
        self.author = author
        self.message = message
        self.date = date

    def to_dict(self) -> dict:
        return {
            "author": self.author,
            "message": self.message,
            "date": self.date,
        }


class Czbooks:
    def __init__(
        self,
        code: str,
        title: str,
        description: str,
        thumbnail: str | None,
        theme_colors: list[int] | None,
        author: HyperLink,
        state: str,
        views: int,
        category: HyperLink,
        content_cache: bool,
        words_count: int,
        hashtags: list[HyperLink],
        chapter_list: list[HyperLink],
        comments: list[Comment],
    ) -> None:
        self.code = code
        self.title = title
        self.description = description
        self.thumbnail = thumbnail
        self.theme_colors = theme_colors
        self.author = author
        self.state = state
        self.views = views
        self.category = category
        self.content_cache = content_cache
        self.words_count = words_count
        self.hashtags = hashtags
        self.chapter_list = chapter_list
        self.comments = comments

        self.comment_last_update: float = None
        self.get_content_task: asyncio.Task = None
        self.get_content_progress_messages: list[Interaction] = []

    async def _edit_progress_message(self, embed: Embed, delete_view: bool) -> None:
        for msg in self.get_content_progress_messages:
            await msg.edit_original_response(
                embed=embed,
                view=None if delete_view else MISSING,
            )

    async def _get_content(self) -> float:
        content = f"{self.title}\n連結: https://czbooks.net/n/{self.code}\n作者: {self.author.text}"  # noqa
        words_count = 0
        chapter_count = len(self.chapter_list)
        # 逐章爬取內容
        start_time = datetime.now().timestamp()
        last_time = start_time
        r, g = 255, 0
        async with aiohttp.ClientSession() as session:
            for index, ch in enumerate(self.chapter_list, start=1):
                try:
                    async with session.get(ch.link) as response:
                        soup = BeautifulSoup(await response.text(), "html.parser")
                except Exception as e:
                    print(f"Error when getting {ch.link}: {e}")
                # 尋找章節
                ch_name = soup.find("div", class_="name")
                # 尋找內文
                div_content = ch_name.find_next("div", class_="content")
                content += f"\n\n{'='*32} {ch_name.text} {'='*32}\n"
                ch_words_count = len(re.findall(chinese_char, div_content.text))
                if ch_words_count < 1024:
                    content += "(本章可能非內文)\n\n"
                else:
                    words_count += ch_words_count
                    content += "\n"
                content += div_content.text.strip()

                # 計算進度
                now_time = datetime.now().timestamp()
                total_diff = now_time - start_time
                if now_time - last_time < 2:
                    continue
                last_time = now_time
                progress, bar = progress_bar(index, chapter_count)
                eta = total_diff / progress - total_diff
                eta_display = (
                    f"`{eta:.1f}`秒" if progress > 0.1 or total_diff > 10 else "計算中..."
                )
                if progress < 0.5:
                    g = int(510 * progress)
                else:
                    r = int(510 * (1 - progress))
                asyncio.create_task(
                    self._edit_progress_message(
                        Embed(
                            title="擷取內文中...",
                            description=f"第{index}/{chapter_count}章 {progress*100:.1f}%```{bar}```預計剩餘時間: {eta_display}",  # noqa
                            color=Color.from_rgb(r, g, 0),
                        ),
                        None if eta < 4 else True,
                    )
                )

        with open(f"./data/{self.code}.txt", "w", encoding="utf-8") as file:
            file.write(content)

        self.words_count = words_count
        self.content_cache = True
        edit_data(self)

        return total_diff

    def get_content(self, msg: Interaction) -> asyncio.Task[float]:
        self.get_content_progress_messages.append(msg)
        if self.get_content_task:
            return self.get_content_task
        self.get_content_task = asyncio.create_task(self._get_content())
        return self.get_content_task

    async def update_comment(self):
        comments = []
        page = 1
        async with aiohttp.ClientSession() as session:
            while True:
                async with session.get(
                    f"https://api.czbooks.net/web/comment/list?novelId={self.code}&page={page}&cleanCache=true"  # noqa
                ) as response:
                    data = await response.json()
                    items = data["data"]["items"]
                comments += [
                    Comment(
                        comment["nickname"],
                        comment["message"],
                        comment["date"],
                    )
                    for comment in items
                ]

                if not (page := data.get("next")):
                    break

        self.comments = comments
        edit_data(self)

    def get_theme_color(self) -> Color:
        return (
            Color(random.choice(self.theme_colors))
            if self.theme_colors
            else Color.random()
        )

    def overview_embed(self) -> Embed:
        embed = Embed(
            title=self.title,
            description=f"""- 作　者：{self.author}
- 狀　態：{self.state}
- 總字數：{f'`{self.words_count}`字' if self.words_count else '`請點擊取得內文以取得字數`'}
- 觀看數：`{self.views}`次
- 章節數：`{len(self.chapter_list)}`章
- 分　類：{self.category}""",
            url=f"https://czbooks.net/n/{self.code}",
            color=self.get_theme_color(),
        )
        embed.add_field(
            name="書本簡述",
            value=(
                self.description
                if len(self.description) < 1024
                else self.description[:1020] + " ..."
            ),
            inline=False,
        )
        if self.hashtags:
            hashtag_text = ""
            hashtag_len = len(last_hashtag := str(self.hashtags[-1]))
            for hashtag in self.hashtags[:-1]:
                hashtag_len += len(text := f"{hashtag}、")
                if hashtag_len > 1018:
                    hashtag_text += "⋯⋯、"
                    break
                hashtag_text += text
            hashtag_text += last_hashtag
        else:
            hashtag_text = "尚無標籤"
        embed.add_field(name="標籤", value=hashtag_text, inline=False)

        if self.thumbnail:
            embed.set_thumbnail(url=self.thumbnail)

        return embed

    def chapter_embed(self) -> Embed:
        chapter_len = len(
            chapter_text_ := "、".join(
                str(chapter) for chapter in self.chapter_list[-8:]
            )
        )
        chapter_text = ""
        for chapter in self.chapter_list[:-8]:
            chapter_len += len(text := f"{chapter}、")
            if chapter_len > 4094:
                chapter_text += "⋯⋯、"
                break
            chapter_text += text

        return Embed(
            title=f"{self.title}章節列表",
            description=chapter_text + chapter_text_,
            url=f"https://czbooks.net/n/{self.code}",
            color=self.get_theme_color(),
        )

    def comments_embed(self) -> Embed:
        embed = Embed(
            title=f"{self.title}評論列表",
            url=f"https://czbooks.net/n/{self.code}",
            color=self.get_theme_color(),
        )
        for comment in self.comments:
            embed.add_field(
                name=comment.author,
                value=f"```{comment.message}```",
                inline=False,
            )
            if len(embed) > 6000:
                embed.remove_field(-1)
                break

        return embed

    def to_dict(self) -> dict:
        return {
            "code": self.code,
            "title": self.title,
            "description": self.description,
            "thumbnail": self.thumbnail,
            "main_color": self.theme_colors,
            "author": self.author.to_dict(),
            "state": self.state,
            "views": self.views,
            "category": self.category.to_dict(),
            # "content_cache": self.content_cache,
            "words_count": self.words_count,
            "hashtags": [hashtag.to_dict() for hashtag in self.hashtags],
            "chapter_list": [chapter.to_dict() for chapter in self.chapter_list],
            # "comments": [comment.to_dict() for comment in self.comments],
        }


def load_from_json(data: dict) -> Czbooks:
    return Czbooks(
        code=data.get("code"),
        title=data.get("title"),
        description=data.get("description"),
        thumbnail=data.get("thumbnail"),
        theme_colors=data.get("main_color"),
        author=HyperLink(*data.get("author").values()),
        state=data.get("state"),
        views=data.get("views"),
        category=HyperLink(*data.get("category").values()),
        content_cache=bool(data.get("words_count")),
        words_count=data.get("words_count"),
        hashtags=[HyperLink(*hashtag.values()) for hashtag in data.get("hashtags")],
        chapter_list=[
            HyperLink(*chapter.values()) for chapter in data.get("chapter_list")
        ],
        comments=[],
    )


with open("./data/books.json", "r", encoding="utf-8") as file:
    data: dict[str, dict] = json.load(file)
    books_cache = {code: load_from_json(detail) for code, detail in data.items()}


def edit_data(book: Czbooks):
    with open("./data/books.json", "r+", encoding="utf-8") as file:
        data = json.load(file)
        data[book.code] = book.to_dict()
        file.seek(0, 0)
        json.dump(data, file, ensure_ascii=False)
        file.truncate()


def get_code(s: str) -> str | None:
    if match := re.search(re_code, s):
        return match.group(2)
    return None


def get_book(code: str) -> Czbooks:
    return books_cache.get(code)


async def fetch_book(code: str) -> Czbooks:
    soup = await get_html(f"https://czbooks.net/n/{code}")
    # book state
    state_div = soup.find("div", class_="state")
    state_children = state_div.find_all("td")
    state = f"{state_children[1].text} (更新時間：{state_children[7].text})"
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
        views=views,
        category=category,
        content_cache=False,
        words_count=0,
        hashtags=hashtags,
        chapter_list=chapter_lists,
        comments=[],
    )
    books_cache[code] = book
    edit_data(book)

    return book


async def get_or_fetch_book(code: str) -> Czbooks:
    return get_book(code) or await fetch_book(code)


# search by name: s, hashtag: hashtag, author: a
by_dict = {
    "name": "s",
    "hashtag": "hashtag",
    "author": "a",
}


async def search(
    keyword: str,
    by: Literal["name", "hashtag", "author"],
    page: int = 0,
) -> list[HyperLink]:
    if not (_by := by_dict.get(by)):
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
