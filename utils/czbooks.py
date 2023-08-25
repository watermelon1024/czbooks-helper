import asyncio
import json
import random
import re

from pathlib import Path

import aiohttp

from discord import Embed, File, InteractionMessage, Color, MISSING
from bs4 import BeautifulSoup

from . import api
from .discord import get_or_fetch_message_from_reference
from .time import now_timestamp

chinese_char = re.compile(r"[\u4e00-\u9fa5]")


def progress_bar(
    current: int,
    total: int,
    bar_length: int = 27,
) -> tuple[float, str]:
    percentage = current / total
    filled_length = int(bar_length * percentage)
    return percentage, f"[{'='*filled_length}{' '*(bar_length-filled_length)}]"


class HyperLink:
    def __init__(self, text: str, url: str) -> None:
        self.text = text
        self.url = url

    def __str__(self) -> str:
        return f"[{self.text}]({self.url})"

    def to_dict(self) -> dict:
        return {
            "text": self.text,
            "link": self.url,
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
        last_update: str,
        views: int,
        category: HyperLink,
        content_cache: bool,
        words_count: int,
        hashtags: list[HyperLink],
        chapter_list: list[HyperLink],
        comments: list[Comment],
        last_fetch_time: float = 0,
    ) -> None:
        self.code = code
        self.title = title
        self.description = description
        self.thumbnail = thumbnail
        self.theme_colors = theme_colors
        self.author = author
        self.state = state
        self.last_update = last_update
        self.views = views
        self.category = category
        self.content_cache = content_cache
        self.words_count = words_count
        self.hashtags = hashtags
        self.chapter_list = chapter_list
        self.comments = comments
        self.last_fetch_time = last_fetch_time

        self._overview_embed_cache: Embed = None
        self._chapter_embed_cache: Embed = None
        self._comments_embed_cache: Embed = None
        self.comment_last_update: float = None
        self.get_content_task: asyncio.Task = None
        self.get_content_progress_messages: dict[str, InteractionMessage] = {}

    async def _edit_progress_message(self, embed: Embed, delete_view: bool) -> None:
        for msg in self.get_content_progress_messages.values():
            await msg.edit(
                embed=embed,
                view=None if delete_view else MISSING,
            )

    async def _get_content(self) -> None:
        content = ""
        words_count = 0
        chapter_count = len(self.chapter_list)
        # 逐章爬取內容
        start_time = now_timestamp()
        last_time = start_time
        r, g = 255, 0
        async with aiohttp.ClientSession() as session:
            for index, ch in enumerate(self.chapter_list, start=1):
                try:
                    async with session.get(ch.url) as response:
                        soup = BeautifulSoup(await response.text(), "html.parser")
                except Exception as e:
                    print(f"Error when getting {ch.url}: {e}")
                # 尋找章節
                ch_name = soup.find("div", class_="name")
                # 尋找內文
                div_content = ch_name.find_next("div", class_="content")
                content += f"\n\n{'='*30} {ch_name.text} {'='*30}\n"
                ch_words_count = len(re.findall(chinese_char, div_content.text))
                if ch_words_count < 1024:
                    content += "(本章可能非內文)\n\n"
                else:
                    words_count += ch_words_count
                    content += "\n"
                content += div_content.text

                # 計算進度
                now_time = now_timestamp()
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
                        True if eta < 4 else False,
                    )
                )

        with open(f"./data/{self.code}.txt", "w", encoding="utf-8") as file:
            file.write(
                f"""{self.title}
連結：https://czbooks.net/n/{self.code}
作者：{self.author.text}
總章數：{chapter_count}
總字數：{words_count}
{content}"""
            )

        self.words_count = words_count
        self.content_cache = True
        edit_data(self)

        print(f"{self.title} total words: {words_count}.")
        content = (
            f"擷取成功，耗時`{total_diff:.1f}`秒\n- 書名: {self.title}\n- 總字數: `{words_count}`字"
        )
        book_file = File(Path(f"./data/{self.code}.txt"))
        self.overview_embed(from_cache=False)
        for msg in self.get_content_progress_messages.values():
            await msg.edit(content=content, embed=None, view=None, file=book_file)
            (await get_or_fetch_message_from_reference(msg)).edit(
                embed=self.overview_embed()
            )

    def get_content(self, message: InteractionMessage) -> asyncio.Task:
        self.get_content_progress_messages[str(message.id)] = message
        if not self.get_content_task:
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
        # edit_data(self)

    def get_theme_color(self) -> Color:
        return (
            Color(random.choice(self.theme_colors))
            if self.theme_colors
            else Color.random()
        )

    def overview_embed(self, from_cache: bool = True) -> Embed:
        if self._overview_embed_cache and from_cache:
            self._overview_embed_cache.color = self.get_theme_color()
            return self._overview_embed_cache

        embed = Embed(
            title=self.title,
            description=f"""- 作　者：{self.author}
- 狀　態：{self.state} ({self.last_update}更新)
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

        self._overview_embed_cache = embed
        return self._overview_embed_cache

    def chapter_embed(self, from_cache: bool = True) -> Embed:
        if self._chapter_embed_cache and from_cache:
            self._chapter_embed_cache.color = self.get_theme_color()
            return self._chapter_embed_cache

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

        self._chapter_embed_cache = Embed(
            title=f"{self.title}章節列表",
            description=chapter_text + chapter_text_,
            url=f"https://czbooks.net/n/{self.code}",
            color=self.get_theme_color(),
        )
        return self._chapter_embed_cache

    def comments_embed(self, from_cache: bool = True) -> Embed:
        if self._comments_embed_cache and from_cache:
            self._comments_embed_cache.color = self.get_theme_color()
            return self._comments_embed_cache

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

        self._comments_embed_cache = embed
        return self._comments_embed_cache

    def to_dict(self) -> dict:
        return {
            "code": self.code,
            "title": self.title,
            "description": self.description,
            "thumbnail": self.thumbnail,
            "main_color": self.theme_colors,
            "author": self.author.to_dict(),
            "state": self.state,
            "last_update": self.last_update,
            "views": self.views,
            "category": self.category.to_dict(),
            # "content_cache": self.content_cache,
            "words_count": self.words_count,
            "hashtags": [hashtag.to_dict() for hashtag in self.hashtags],
            "chapter_list": [chapter.to_dict() for chapter in self.chapter_list],
            # "comments": [comment.to_dict() for comment in self.comments],
            "last_fetch_time": self.last_fetch_time,
        }

    def load_from_json(self, data: dict) -> "Czbooks":
        return Czbooks(
            code=data.get("code"),
            title=data.get("title"),
            description=data.get("description"),
            thumbnail=data.get("thumbnail"),
            theme_colors=data.get("main_color"),
            author=HyperLink(*data.get("author").values()),
            state=data.get("state"),
            last_update=data.get("last_update"),
            views=data.get("views"),
            category=HyperLink(*data.get("category").values()),
            content_cache=bool(data.get("words_count")),
            words_count=data.get("words_count"),
            hashtags=[HyperLink(*hashtag.values()) for hashtag in data.get("hashtags")],
            chapter_list=[
                HyperLink(*chapter.values()) for chapter in data.get("chapter_list")
            ],
            comments=[],
            last_fetch_time=data.get("last_fetch_time", 0),
        )


def get_book(code: str) -> Czbooks:
    return books_cache.get(code)


async def get_or_fetch_book(code: str) -> Czbooks:
    return get_book(code) or await api.fetch_book(code)


with open("./data/books.json", "r", encoding="utf-8") as file:
    data: dict[str, dict] = json.load(file)
    books_cache = {
        code: Czbooks.load_from_json(detail) for code, detail in data.items()
    }


def edit_data(book: Czbooks):
    with open("./data/books.json", "r+", encoding="utf-8") as file:
        data = json.load(file)
        data[book.code] = book.to_dict()
        file.seek(0, 0)
        json.dump(data, file, ensure_ascii=False)
        file.truncate()
