import asyncio

from pathlib import Path
from datetime import datetime

import discord

from discord import Embed, ApplicationContext, Interaction, Bot
from discord.ui import View, Button

from bot import BaseCog
from utils.czbooks import (
    get_code,
    get_book,
    get_or_fetch_book,
    NotFoundError,
)


class InfoCog(BaseCog):
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
        await ctx.defer()
        code = get_code(link) or link
        try:
            book = await get_or_fetch_book(code)
            await ctx.respond(
                embed=book.overview_embed(),
                view=InfoView(self.bot),
            )
        except NotFoundError:
            await ctx.respond(
                embed=Embed(title="未知的書本", color=discord.Color.red()),
            )

    @info.error
    async def on_info_error(self, ctx: ApplicationContext, error):
        await ctx.respond(
            embed=Embed(title="發生未知的錯誤", color=discord.Color.red()),
            ephemeral=True,
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
            disabled=True,
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

        cancel_get_content_button = Button(
            custom_id="cancel_get_content_button",
            label="取消擷取"
        )
        cancel_get_content_button.callback = self.cancel_get_content
        self.cancel_get_content_view = View(
            cancel_get_content_button,
            timeout=None,
        )

    async def overview_button_callback(self, interaction: Interaction):
        self.overview_button.disabled = True
        self.chapter_button.disabled = False
        self.comment_button.disabled = False
        self.get_content_button.disabled = (
            interaction.message.components[-1].children[0].disabled
        )
        code = get_code(interaction.message.embeds[0].url)
        await interaction.response.edit_message(
            embed=get_book(code).overview_embed(),
            view=self,
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
            embed=get_book(code).chapter_embed(),
            view=self,
        )

    async def comment_button_callback(self, interaction: Interaction):
        self.overview_button.disabled = False
        self.chapter_button.disabled = False
        self.comment_button.disabled = True
        self.get_content_button.disabled = (
            interaction.message.components[-1].children[0].disabled
        )

        book = get_book(get_code(interaction.message.embeds[0].url))

        now_time = datetime.now().timestamp()
        if (not book.comment_last_update) or (
            now_time - book.comment_last_update > 600
        ):
            await interaction.response.defer()
            book.comment_last_update = now_time
            await book.update_comment()

        await interaction.message.edit(
            embed=book.comments_embed(),
            view=self,
        )

    async def get_content_button_callback(self, interaction: Interaction):
        self.get_content_button.disabled = (
            interaction.message.components[-1].children[0].disabled
        )
        self.get_content_button.disabled = True
        await interaction.message.edit(view=self)

        book = get_book(get_code(interaction.message.embeds[0].url))
        if book.content_cache:
            return await interaction.response.send_message(
                content=f"- 書名: {book.title}\n- 總字數: `{book.words_count}`字",
                file=discord.File(Path(f"./data/{book.code}.txt")),
            )

        content_msg = await interaction.response.send_message(
            embed=Embed(
                title="擷取內文中...",
                description="正在計算進度...",
            ),
            view=self.cancel_get_content_view,
        )
        print(f"{interaction.user} gets {book.title}'s content")
        task = asyncio.create_task(book.get_content(content_msg))
        book.get_content_task = task
        try:
            time_taken = await task
            print(f"{book.title} total words: {book.words_count}.")
        except asyncio.CancelledError:
            book.words_count = 0
            return await content_msg.edit_original_response(
                content="已取消",
                delete_after=5,
            )

        await content_msg.edit_original_response(
            content=f"擷取成功，耗時`{time_taken:.1f}`秒\n- 書名: {book.title}\n- 總字數: `{book.words_count}`字",  # noqa
            embed=None,
            view=None,
            file=discord.File(Path(f"./data/{book.code}.txt")),
        )
        if interaction.message.components[0].children[0].disabled:
            await interaction.message.edit(embed=book.overview_embed())

    async def cancel_get_content(self, interaction: Interaction):
        book = get_book(get_code(interaction.message.embeds[0].url))
        book.get_content_task.cancel()


def setup(bot: Bot):
    bot.add_cog(InfoCog(bot))
