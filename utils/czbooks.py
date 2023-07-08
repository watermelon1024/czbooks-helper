import json
import re

from datetime import datetime

import aiohttp

from discord import Embed, Interaction
from bs4 import BeautifulSoup

chinese_char = re.compile(r"[\u4e00-\u9fa5]")
re_code = re.compile(r"(czbooks\.net\/n\/)([a-z0-9]+)")


class NotFoundError(Exception):
    """
    Book not found.
    """

    def __init__(self):
        super().__init__()


def progress_bar(
    current: int, total: int, bar_length: int = 27,
) -> tuple[float, str]:
    percentage = current / total
    filled_length = int(bar_length * percentage)
    return percentage, f"[{'='*filled_length}{' '*(bar_length-filled_length)}]"


async def get(link: str) -> str:
    async with aiohttp.request("GET", link) as response:
        return await response.text()


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


class Comment:
    def __init__(
        self,
        author: str, message: str, date: int
    ) -> None:
        self.author = author
        self.message = message
        self.date = date


class Czbooks:
    def __init__(
        self,
        code: str,
        title: str,
        description: str,
        thumbnail: str | None,
        author: str,
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
        self.author = author
        self.content_cache = content_cache
        self.words_count = words_count
        self.hashtags = hashtags
        self.chapter_list = chapter_list
        self.comments = comments
        self.comment_last_update: float = None

    async def get_content(self, msg: Interaction):
        self.content = f"連結: https://czbooks.net/n/{self.code}"
        self.words_count = 0
        chapter_count = len(self.chapter_list)
        # 逐章爬取內容
        start_time = datetime.now().timestamp()
        last_time = start_time
        for index, ch in enumerate(self.chapter_list, start=1):
            try:
                soup = await get_html(ch.link)
            except Exception as e:
                print(f"Error when getting {ch.link}: {e}")
            # 尋找章節
            ch_name = soup.find("div", class_="name")
            # 尋找內文
            div_content = ch_name.find_next("div", class_="content")
            self.content += f"\n\n{'='*32} {ch_name.text} {'='*32}\n\n"
            self.content += div_content.text.strip()
            # 計算字數
            self.words_count += len(re.findall(chinese_char, div_content.text))

            # 計算進度
            now_time = datetime.now().timestamp()
            total_diff = now_time - start_time
            if now_time - last_time > 2:
                last_time = now_time
                progress, bar = progress_bar(index, chapter_count)
                eta = total_diff / progress - total_diff
                await msg.edit_original_response(
                    embed=Embed(
                        title="擷取內文中...",
                        description=f"{progress*100:.1f}% {index}/{chapter_count}章```{bar}```預計剩餘時間: {eta:.1f}秒"  # noqa
                    )
                )

        with open(f"./data/{self.code}.txt", "w", encoding="utf-8") as file:
            file.write(self.content)

        self.content_cache = True
        edit_data(self)

    async def update_comment(self):
        comments = []
        page = 0
        last_id = ""
        while True:
            page += 1
            try:
                resp = await get(f"https://api.czbooks.net/web/comment/list?novelId={self.code}&page={page}&cleanCache=true")  # noqa
                items = json.loads(resp)["data"]["items"]
                if len(items) == 0 or last_id == items[0]["id"]:
                    break
                last_id = items[0]["id"]
                comments += [
                    Comment(
                        comment["nickname"],
                        comment["message"],
                        comment["date"],
                    ) for comment in items
                ]
            except Exception as e:
                print(f"ERROR GET COMMENTS: {e}")
                pass

        self.comments = comments

    def overview_embed(self) -> Embed:
        embed = Embed(
            title=self.title,
            description=f"https://czbooks.net/n/{self.code}\n- 作者: {self.author}\n- 總字數: {f'`{self.words_count}`字' if self.words_count else '`請點擊取得內文以取得字數`'}"  # noqa
        )
        embed.add_field(
            name="書本簡述",
            value=(
                self.description if len(self.description) < 1024
                else self.description[:1020] + " ..."
            ),
            inline=False
        )

        hashtag_text = ""
        hashtag_len = len(
            last_hashtag := str(self.hashtags[-1])
        )
        for hashtag in self.hashtags[:-1]:
            hashtag_len += len(text := f"{hashtag}, ")
            if hashtag_len > 1018:
                hashtag_text += " ..., "
                break
            hashtag_text += text
        hashtag_text += last_hashtag
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
            description=chapter_text + chapter_text_
        )

    def comments_embed(self) -> Embed:
        embed = Embed(
            title=f"{self.title}評論列表",
            description=f"https://czbooks.net/n/{self.code}"
        )
        for comment in self.comments:
            embed.add_field(
                name=comment.author,
                value=f"```{comment.message}```",
                inline=False
            )
            if len(embed) > 6000:
                embed.remove_field(-1)
                break

        return embed


def get_code(s: str) -> str | None:
    if match := re.search(re_code, s):
        return match.group(2)
    return None


async def get_book(code: str) -> Czbooks:
    soup = await get_html(f"https://czbooks.net/n/{code}")
    detail_div = soup.find("div", class_="novel-detail")
    # basic info
    title = detail_div.find("span", class_="title").text
    description = detail_div.find("div", class_="description").text
    thumbnail = detail_div.find("img").get("src")
    if not thumbnail.startswith("https://img.czbooks.net"):
        thumbnail = None
    author = detail_div.find("span", class_="author").contents[1].text
    # hashtags
    hashtags = [
        HyperLink(hashtag.text, "https:"+hashtag["href"])
        for hashtag in soup.find(
            "ul", class_="hashtag"
        ).find_all("a")[:-1]
    ]
    # chapter list
    chapter_lists = [
        HyperLink(chapter.text, "https:"+chapter["href"])
        for chapter in soup.find(
            "ul", id="chapter-list"
        ).find_all("a")
    ]

    book = Czbooks(
        code, title, description, thumbnail, author, False, 0,
        hashtags, chapter_lists, []
    )
    edit_data(book)

    return book


def edit_data(book: Czbooks):
    with open("./data/books.json", "r+", encoding="utf-8") as file:
        data = json.load(file)
        data[book.code] = {
            "code": book.code,
            "title": book.title,
            "description": book.description,
            "thumbnail": book.thumbnail,
            "author": book.author,
            "content_cache": book.content_cache,
            "words_count": book.words_count,
            "hashtags": [
                {
                    "text": hashtag.text,
                    "link": hashtag.link
                } for hashtag in book.hashtags
            ],
            "chapters": [
                {
                    "text": chapter.text,
                    "link": chapter.link
                } for chapter in book.chapter_list
            ],
            "comments": [
                {
                    "author": comment.author,
                    "message": comment.message,
                    "date": comment.date
                } for comment in book.comments
            ]
        }
        file.seek(0, 0)
        json.dump(data, file, ensure_ascii=False)
        file.truncate()
