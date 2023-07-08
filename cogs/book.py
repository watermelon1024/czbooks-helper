import json

from pathlib import Path
from datetime import datetime

import discord

from discord import Embed, ApplicationContext, Interaction, Bot
from discord.ui import View, Button

from bot import BaseCog
from utils.czbooks import (
    Czbooks,
    HyperLink,
    Comment,
    get_code,
    get_book,
    NotFoundError,
)

with open("./data/books.json", "r", encoding="utf-8") as file:
    data: dict[str, dict] = json.load(file)
    books_cache = {
        code: Czbooks(
            *list(detail.values())[:7],
            [
                HyperLink(*hashtag.values())
                for hashtag in detail["hashtags"]
            ],
            [
                HyperLink(*chapter.values())
                for chapter in detail["chapters"]
            ],
            [
                Comment(*comment.values())
                for comment in detail["comments"]
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
        msg = await ctx.respond(embed=Embed(title="資料擷取中，請稍後..."))
        code = get_code(link) or link
        try:
            book = books_cache.get(code) or await get_book(code)
            books_cache[code] = book
            return await msg.edit_original_response(
                embed=book.overview_embed(),
                view=InfoView(self.bot)
            )
        except NotFoundError:
            return await msg.edit_original_response(
                embed=Embed(title="未知的書本", color=discord.Color.red())
            )

    @info.error
    async def on_info_error(self, ctx: ApplicationContext, error):
        await ctx.respond(
            embed=Embed(title="發生未知的錯誤", color=discord.Color.red()),
            ephemeral=True
        )

    @discord.Cog.listener()
    async def on_ready(self):
        self.bot.add_view(InfoView(self.bot))


class InfoView(View):
    def __init__(self, bot: Bot):
        super().__init__(timeout=None)
        self.bot = bot

        self.overview_button = Button(
            custom_id="overview_button",
            label="書本總覽",
            row=0,
            disabled=True
        )
        self.overview_button.callback = self.overview_button_callback
        self.add_item(self.overview_button)

        self.chapter_button = Button(
            custom_id="chapter_button",
            label="章節列表",
            row=0,
        )
        self.chapter_button.callback = self.chapter_button_callback
        self.add_item(self.chapter_button)

        self.comment_button = Button(
            custom_id="comment_button",
            label="觀看評論",
            row=0,
        )
        self.comment_button.callback = self.comment_button_callback
        self.add_item(self.comment_button)

        self.get_content_button = Button(
            custom_id="get_content_button",
            label="取得內文",
            row=1,
        )
        self.get_content_button.callback = self.get_content_button_callback
        self.add_item(self.get_content_button)

    async def overview_button_callback(self, interaction: Interaction):
        self.overview_button.disabled = True
        self.chapter_button.disabled = False
        self.comment_button.disabled = False
        self.get_content_button.disabled = (
            interaction.message.components[-1].children[0].disabled
        )
        code = get_code(interaction.message.embeds[0].url)
        await interaction.response.edit_message(
            embed=books_cache[code].overview_embed(),
            view=self
        )

    async def chapter_button_callback(self, interaction: Interaction):
        self.overview_button.disabled = False
        self.chapter_button.disabled = True
        self.comment_button.disabled = False
        self.get_content_button.disabled = (
            interaction.message.components[-1].children[0].disabled
        )
        code = get_code(interaction.message.embeds[0].url)
        await interaction.response.edit_message(
            embed=books_cache[code].chapter_embed(),
            view=self
        )

    async def comment_button_callback(self, interaction: Interaction):
        self.overview_button.disabled = False
        self.chapter_button.disabled = False
        self.comment_button.disabled = True
        self.get_content_button.disabled = (
            interaction.message.components[-1].children[0].disabled
        )
        code = get_code(interaction.message.embeds[0].url)
        book = books_cache[code]
        await interaction.response.edit_message(
            embed=Embed(
                title=f"{book.title}評論列表",
                description="資料擷取中，請稍後...",
            ),
            view=self
        )
        now_time = datetime.now().timestamp()
        if (not book.comment_last_update) or (
            now_time - book.comment_last_update > 600
        ):
            book.comment_last_update = now_time
            await book.update_comment()
        await interaction.message.edit(embed=book.comments_embed())

    async def get_content_button_callback(self, interaction: Interaction):
        self.get_content_button.disabled = (
            interaction.message.components[-1].children[0].disabled
        )
        self.get_content_button.disabled = True
        await interaction.message.edit(view=self)

        code = get_code(interaction.message.embeds[0].url)
        book = books_cache.get(code)

        content_msg = await interaction.response.send_message(
            embed=Embed(
                title="擷取內文中...",
                description="正在計算進度..."
            )
        )
        if not book.content_cache:
            print(f"{interaction.user} gets {book.title}'s content")
            await book.get_content(content_msg)
            print(f"{book.title} total words: {book.words_count}.")

            if interaction.message.components[0].children[0].disabled:
                await interaction.message.edit(embed=book.overview_embed())

        await content_msg.edit_original_response(
            content=f"- 書名: {book.title}\n- 總字數: `{book.words_count}`字",
            embed=None,
            file=discord.File(Path(f"./data/{book.code}.txt")),
        )


def setup(bot: Bot):
    bot.add_cog(BookCog(bot))
