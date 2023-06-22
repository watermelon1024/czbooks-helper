import json
import re
import os

from pathlib import Path

import requests
import discord

from discord import Embed, ApplicationContext, Bot
from bot import BaseCog
from bs4 import BeautifulSoup


chinese_char = re.compile(r"[\u4e00-\u9fa5]")
re_code = re.compile(r"(czbooks\.net\/n\/)([a-z0-9]+)")


def get_html(link: str) -> BeautifulSoup | None:
    try:
        response = requests.get(link)
        soup = BeautifulSoup(response.text, "html.parser")
        return soup
    except Exception:
        return None


class HyperLink():
    def __init__(self, text: str, link: str) -> None:
        self.text = text
        self.link = link


class Czbooks():
    def __init__(
        self,
        code: str,
        title: str,
        description: str,
        thumbnail: str | None,
        author: str,
        hashtags: list[HyperLink],
        chapter_lists: list[HyperLink],
    ) -> None:
        self.code = code
        self.title = title
        self.description = description
        self.thumbnail = thumbnail
        self.author = author
        self.hashtags = hashtags
        self.chapter_lists = chapter_lists

    def get_content(self):
        if os.path.exists(f"./data/{self.code}.txt"):
            return
        self.content = f"連結: https://czbooks.net/n/{self.code}"
        # 逐章爬取內容
        for ch in self.chapter_lists:
            # retry when error
            for _ in range(5):
                if soup := get_html(ch.link):
                    break
            if not soup:
                print(f"Error when getting {ch.link} .")
            # 尋找章節名稱
            # 尋找章節名稱 div 標籤
            ch_name = soup.find("div", class_="name")
            # 尋找內文 div 標籤
            div_content = ch_name.find_next("div", class_="content")
            # 儲存找到的內容
            self.content += f"\n\n{'='*32} {ch_name.text} {'='*32}\n\n"
            self.content += div_content.text.strip()
        # 計算總字數
        self.words_count = len(re.findall(chinese_char, self.content))
        with open(f"./data/{self.code}.txt", "w", encoding="utf-8") as file:
            file.write(self.content)


def get_book(code: str) -> Czbooks:
    soup = get_html(f"https://czbooks.net/n/{code}")
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

    return Czbooks(
        code, title, description, thumbnail, author, hashtags, chapter_lists
    )


def add_cache(book: Czbooks):
    with open("./data/books.json", "r+", encoding="utf-8") as file:
        data = json.load(file)
        data[book.code] = {
            "code": book.code,
            "title": book.title,
            "description": book.description,
            "thumbnail": book.thumbnail,
            "author": book.author,
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
                } for chapter in book.chapter_lists
            ]
        }
        file.seek(0, 0)
        json.dump(data, file, ensure_ascii=False)


class BookCog(BaseCog):
    def __init__(self, bot: Bot) -> None:
        super().__init__(bot)
        with open("./data/books.json", "r", encoding="utf-8") as file:
            data: dict[str, dict] = json.load(file)
            self.books_cache = {
                code: Czbooks(
                    *list(detail.values())[:5],
                    [
                        HyperLink(hashtag["text"], hashtag["link"])
                        for hashtag in detail["hashtags"]
                    ],
                    [
                        HyperLink(chapter["text"], chapter["link"])
                        for chapter in detail["chapters"]
                    ]
                ) for code, detail in data.items()
            }

    @discord.slash_command(
        guild_only=True,
        name="info",
        description="取得書本資訊",
    )
    @discord.option(
        "link",
        str,
        # name="書本連結",
        description="欲查詢的書本連結",
    )
    async def info(self, ctx: ApplicationContext, link: str):
        if match := re.search(re_code, link):
            code = match.group(2)
        else:
            code = link
        book = self.books_cache.get(code)
        if not book:
            book = get_book(code)
            add_cache(book)
            self.books_cache[code] = book

        embed = Embed(
            title=book.title,
            description=f"- 作者: {book.author}"
        )
        embed.add_field(
            name="書本簡述",
            value=book.description if len(
                book.description) < 1024 else book.description[:1020]+" ...",
            inline=False
        )

        hashtag_len = 0
        hashtag_text = ""
        for hashtag in book.hashtags:
            hashtag_len += len(text := f"[{hashtag.text}]({hashtag.link}), ")
            if hashtag_len > 1020:
                hashtag_text += " ..., "
                break
            hashtag_text += text
        embed.add_field(name="標籤", value=hashtag_text[:-2], inline=False)

        chapter_len = 0
        chapter_text = ""
        for chapter in book.chapter_lists:
            chapter_len += len(text := f"[{chapter.text}]({chapter.link}), ")
            if chapter_len > 1020:
                chapter_text += " ..., "
                break
            chapter_text += text
        embed.add_field(name="章節列表", value=chapter_text[:-2], inline=False)

        if book.thumbnail:
            embed.set_thumbnail(url=book.thumbnail)
        info_msg = await ctx.respond(embed=embed)

        content_msg = await info_msg.followup.send(
            embed=Embed(
                title="擷取內文中...",
                description=f"共{len(book.chapter_lists)}章",
            )
        )
        book.get_content()
        await content_msg.edit(
            "內文擷取完畢!",
            embed=None,
            file=discord.File(Path(f"./data/{book.code}.txt")),
        )


def setup(bot: Bot):
    bot.add_cog(BookCog(bot))
