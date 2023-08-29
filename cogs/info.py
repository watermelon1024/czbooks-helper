import asyncio
from pathlib import Path

import discord

from discord import Embed, ApplicationContext, Interaction, Colour, MISSING
from discord.ui import View, Button

from bot import BaseCog, Bot
from utils import czbook
from utils.discord import get_or_fetch_message_from_reference


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
        code = czbook.get_code(link) or link
        try:
            book = await self.bot.get_or_fetch_book(code)
            self.bot.add_cache(book)
            await ctx.respond(
                embed=book.overview_embed(),
                view=InfoView(self.bot),
            )
        except czbook.NotFoundError:
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
            label="取消擷取",
            style=discord.ButtonStyle.red,
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
        code = czbook.get_code(interaction.message.embeds[0].url)
        await interaction.response.edit_message(
            embed=(await self.bot.get_or_fetch_book(code)).overview_embed(),
            view=self,
        )

    async def chapter_button_callback(self, interaction: Interaction):
        self.overview_button.disabled = False
        self.chapter_button.disabled = True
        self.comment_button.disabled = False
        self.get_content_button.disabled = (
            interaction.message.components[-1].children[0].disabled
        )
        code = czbook.get_code(interaction.message.embeds[0].url)
        await interaction.response.edit_message(
            embed=(await self.bot.get_or_fetch_book(code)).chapter_embed(),
            view=self,
        )

    async def comment_button_callback(self, interaction: Interaction):
        self.get_content_button.disabled = (
            interaction.message.components[-1].children[0].disabled
        )
        await interaction.response.defer()

        book = await self.bot.get_or_fetch_book(
            czbook.get_code(interaction.message.embeds[0].url)
        )
        await interaction.response.edit_message(embed=await book.comments_embed())

    async def get_content_button_callback(self, interaction: Interaction):
        self.get_content_button.disabled = (
            interaction.message.components[-1].children[0].disabled
        )
        self.get_content_button.disabled = True
        await interaction.message.edit(view=self)

        book = await self.bot.get_or_fetch_book(
            czbook.get_code(interaction.message.embeds[0].url)
        )
        if book.content_cache:
            return await interaction.response.send_message(
                content=f"- 書名: {book.title}\n- 總字數: `{book.word_count}`字",
                file=discord.File(Path(f"./data/{book.code}.txt")),
            )

        print(f"{interaction.user} gets {book.title}'s content")
        content_msg = await interaction.response.send_message(
            embed=Embed(
                title="擷取內文中...",
                description="正在計算進度...",
            ),
            view=self.cancel_get_content_view,
        )
        stats = book.get_content()
        msg = await content_msg.original_response()
        self.bot.get_content_msg.add(msg.id)
        while True:
            await asyncio.sleep(1)
            if stats.finished:
                break
            elif msg.id not in self.bot.get_content_msg:
                return
            await msg.edit(
                embed=Embed(
                    title="擷取內文中",
                    description=stats.get_progress(),
                    color=Colour.from_rgb(
                        min(int(510 * stats.percentage), 255),
                        min(int(510 * (1 - stats.percentage)), 255),
                        0,
                    ),
                ),
                view=None if stats.eta < 2 else MISSING,
            )

        await msg.edit(
            content=f"- 書名: {book.title}\n- 總字數: `{book.word_count}`字",
            file=discord.File(Path(f"./data/{book.code}.txt")),
            embed=None,
        )

    async def cancel_get_content(self, interaction: Interaction):
        message = await get_or_fetch_message_from_reference(interaction.message)
        book = await self.bot.get_or_fetch_book(czbook.get_code(message.embeds[0].url))
        if book.content_cache:
            return
        self.bot.get_content_msg.discard(interaction.message.id)
        if not self.bot.get_content_msg:
            book.cencel_get_content()
        print(f"{interaction.user} cancel gets {book.title}'s content")
        await interaction.response.edit_message(
            embed=Embed(title="已取消"),
            view=None,
            delete_after=3,
        )
        self.get_content_button.disabled = False
        await message.edit(view=self)


def setup(bot: Bot):
    bot.add_cog(InfoCog(bot))
