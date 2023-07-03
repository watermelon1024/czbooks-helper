import json
import re

from datetime import datetime
from pathlib import Path

import aiohttp
import discord

from discord import Embed, ApplicationContext, Interaction, Bot
from discord.ui import View, Button
from bot import BaseCog
from bs4 import BeautifulSoup


chinese_char = re.compile(r"[\u4e00-\u9fa5]")
re_code = re.compile(r"(czbooks\.net\/n\/)([a-z0-9]+)")


def progress_bar(
    current: int, total: int, bar_length: int = 25,
) -> tuple[float, str]:
    percentage = current / total
    filled_length = int(bar_length * percentage)
    return percentage, f"[{'='*filled_length}{' '*(bar_length-filled_length)}]"


async def get_html(link: str) -> tuple[BeautifulSoup | None, int | None]:
    try:
        async with aiohttp.request("GET", link) as response:
            if response.status >= 300:
                return None, response.status
            soup = BeautifulSoup(await response.text(), "html.parser")
            return soup, response.status
    except Exception as e:
        print("ERROR:", e)
        return None, None


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
        content_cache: bool,
        words_count: int,
        hashtags: list[HyperLink],
        chapter_list: list[HyperLink],
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

    async def get_content(self, msg: Interaction):
        self.content = f"連結: https://czbooks.net/n/{self.code}"
        self.words_count = 0
        chapter_count = len(self.chapter_list)
        # 逐章爬取內容
        start_time = datetime.now().timestamp()
        last_time = start_time
        for index, ch in enumerate(self.chapter_list, start=1):
            soup, _ = await get_html(ch.link)
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
            self.words_count += len(re.findall(chinese_char, div_content.text))

            # 計算進度
            now_time = datetime.now().timestamp()
            total_diff = now_time - start_time
            if now_time - last_time > 3:
                last_time = now_time
                progress, bar = progress_bar(index, chapter_count)
                eta = total_diff/progress - total_diff
                await msg.edit_original_response(
                    embed=Embed(
                        title="擷取內文中...",
                        description=f"{progress*100:.1f}% {index}/{chapter_count}```{bar}```預計剩餘時間: {eta:.1f}秒"  # noqa
                        # description=f"共{len(book.chapter_list)}章",
                    )
                )

        with open(f"./data/{self.code}.txt", "w", encoding="utf-8") as file:
            file.write(self.content)

        self.content_cache = True
        add_cache(self)


async def get_book(code: str) -> tuple[Czbooks | None, int]:
    soup, status_code = await get_html(f"https://czbooks.net/n/{code}")
    if status_code >= 300:
        return None, status_code

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
        hashtags, chapter_lists,
    )
    add_cache(book)

    return book, status_code


def add_cache(book: Czbooks):
    books_cache[book.code] = book
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
            ]
        }
        file.seek(0, 0)
        json.dump(data, file, ensure_ascii=False)
        file.truncate()


with open("./data/books.json", "r", encoding="utf-8") as file:
    data: dict[str, dict] = json.load(file)
    books_cache = {
        code: Czbooks(
            *list(detail.values())[:7],
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


class BookCog(BaseCog):
    def __init__(self, bot: Bot) -> None:
        super().__init__(bot)

    @discord.slash_command(
        guild_only=True,
        name="info",
        description="取得書本資訊",
    )
    @discord.option(
        "link",
        str,
        description="欲查詢的書本連結",
    )
    async def info(self, ctx: ApplicationContext, link: str):
        print(f"{ctx.author} used /info link: {link}")
        if match := re.search(re_code, link):
            code = match.group(2)
        else:
            code = link
        book = books_cache.get(code)
        if not book:
            book, status_code = await get_book(code)
            if status_code == 404:
                return await ctx.respond(
                    embed=Embed(title="未知的書本")
                )
            elif status_code >= 300:
                return await ctx.respond(
                    embed=Embed(title="未知的錯誤")
                )

        embed = Embed(
            title=book.title,
            description=f"https://czbooks.net/n/{code}\n- 作者: {book.author}\n- 總字數: {f'`{book.words_count}`字' if book.words_count else '`請點擊取得內文以取得字數`'}"  # noqa
        )
        embed.add_field(
            name="書本簡述",
            value=book.description if len(
                book.description) < 1024 else book.description[:1020]+" ...",
            inline=False
        )

        hashtag_text = ""
        hashtag = book.hashtags[-1]
        hashtag_len = len(
            last_hashtag := f"[{hashtag.text}]({hashtag.link})"
        )
        for hashtag in book.hashtags[:-1]:
            hashtag_len += len(text := f"[{hashtag.text}]({hashtag.link}), ")
            if hashtag_len > 1018:
                hashtag_text += " ..., "
                break
            hashtag_text += text
        hashtag_text += last_hashtag
        embed.add_field(name="標籤", value=hashtag_text, inline=False)

        chapter_text = ""
        chapter = book.chapter_list[-1]
        chapter_len = len(
            last_chapter := f"[{chapter.text}]({chapter.link})"
        )
        for chapter in book.chapter_list[:-1]:
            chapter_len += len(text := f"[{chapter.text}]({chapter.link}), ")
            if chapter_len > 1018:
                chapter_text += " ..., "
                break
            chapter_text += text
        chapter_text += last_chapter
        embed.add_field(
            name=f"章節列表(共{len(book.chapter_list)}章)", value=chapter_text,
            inline=False,
        )

        if book.thumbnail:
            embed.set_thumbnail(url=book.thumbnail)

        await ctx.respond(embed=embed, view=GetContentView(self.bot))

    @discord.Cog.listener()
    async def on_ready(self):
        self.bot.add_view(GetContentView(self.bot))


class GetContentView(View):
    def __init__(self, bot: Bot):
        super().__init__(timeout=None)
        self.bot = bot

        (
            get_content_button := Button(
                custom_id="get_content_button",
                label="取得內文",
            )
        ).callback = self.get_content_button_callback

        self.add_item(get_content_button)

        self.disable_get_content_button = Button(
            custom_id="get_content_button",
            label="取得內文",
            disabled=True,
        )

    async def get_content_button_callback(self, interaction: Interaction):
        await interaction.message.edit(
            view=View(self.disable_get_content_button)
        )

        code = re.search(
            re_code, interaction.message.embeds[0].description
        ).group(2)
        book = books_cache.get(code)

        content_msg = await interaction.response.send_message(
            embed=Embed(
                title="擷取內文中...",
            )
        )
        if not book.content_cache:
            print(f"{interaction.user} gets {book.title}'s content")
            await book.get_content(content_msg)
            print(f"{book.title} total words: {book.words_count}.")

            original_embed = interaction.message.embeds[0]
            original_embed.description = f"https://czbooks.net/n/{code}\n- 作者: {book.author}\n- 總字數: `{book.words_count}`字"  # noqa
            await interaction.message.edit(embed=original_embed)

        await content_msg.edit_original_response(
            content=f"- 書名: {book.title}\n- 總字數: `{book.words_count}`字",
            embed=None,
            file=discord.File(Path(f"./data/{book.code}.txt")),
        )


def setup(bot: Bot):
    bot.add_cog(BookCog(bot))
