import json

from pathlib import Path
from datetime import datetime

import discord

from discord import Embed, ApplicationContext, Interaction, Bot, OptionChoice
from discord.ui import View, Button

from bot import BaseCog
from utils.czbooks import (
    Czbooks,
    HyperLink,
    Comment,
    get_code,
    get_book,
    search,
    NotFoundError,
)


class SearchCog(BaseCog):
    def __init__(self, bot: Bot) -> None:
        super().__init__(bot)

    search_group = discord.SlashCommandGroup("search")

    @search_group.command(
        guild_only=True,
        name="simple",
        description="搜尋小說(基本搜尋)",
    )
    @discord.option(
        "keyword",
        str,
        description="關鍵字",
    )
    @discord.option(
        "by",
        str,
        description="欲使用的搜尋方式",
        choices=[
            OptionChoice("名稱", "name"),
            OptionChoice("標籤", "hashtag"),
            OptionChoice("作者", "author"),
        ],
    )
    async def simple_search(
        self, ctx: ApplicationContext,
        keyword: str, by: str,
    ):
        print(f"{ctx.author} used /search keyword: {keyword} by: {by}")
        msg = await ctx.respond(embed=Embed(title="搜尋中，請稍後..."))
        if result := await search(keyword, by):
            return await msg.edit_original_response(
                embed=Embed(
                    title="搜尋結果",
                    description="\n".join(
                        f"{index}. [{novel.text}](https://czbooks.net/n/{novel.link})"  # noqa
                        for index, novel in enumerate(result[:20], start=1)
                    )
                )
            )

        return await msg.edit_original_response(
            embed=Embed(title="無搜尋結果", color=discord.Color.red())
        )

    @search_group.command(
        guild_only=True,
        name="advanced",
        description="搜尋小說(進階搜尋)",
    )
    @discord.option(
        "name",
        str,
        description="使用書本名稱搜尋",
        required=False,
    )
    @discord.option(
        "hashtag",
        str,
        description="使用標籤搜尋(使用,分隔每個標籤)",
        required=False,
    )
    @discord.option(
        "author",
        str,
        description="使用作者名稱搜尋",
        required=False,
    )
    async def advanced_search(
        self, ctx: ApplicationContext,
        name: str, hashtag: str, author: str,
    ):
        return await ctx.respond(
            embed=Embed(title="暫不開放", color=discord.Color.red()),
            ephemeral=True
        )
        print(f"{ctx.author} used /search name: {name} hashtag: {hashtag} author: {author}")  # noqa
        msg = await ctx.respond(embed=Embed(title="搜尋中，請稍後..."))
        # search by name: s, hashtag: hashtag, author: a
        novel_list: list[list[HyperLink]] = []
        page = 0
        while True:
            if name:
                if name_list := await search(name, "s", page):
                    novel_list.append(name_list)
            if hashtag:
                if hashtag_list := await search(hashtag, "hashtag", page):
                    novel_list.append(hashtag_list)
            if author:
                if author_list := await search(author, "a", page):
                    novel_list.append(author_list)

            if not novel_list:
                page += 1
            else:
                break
        if not novel_list:
            return await msg.edit_original_response(
                embed=Embed(title="無搜尋結果", color=discord.Color.red())
            )

        novel_codes = set(novel.link for novel in novel_list[0])
        for sub_novel_list in novel_list:
            codes = {item.link for item in sub_novel_list}
            novel_codes.intersection_update(codes)
        novel_list_ = [
            item for item in novel_list[0] if item.link in novel_codes
        ]

        if novel_list_:
            return await msg.edit_original_response(
                embed=Embed(
                    title="搜尋結果",
                    description="\n".join(
                        f"{index}. [{novel.text}](https://czbooks.net/n/{novel.link})"  # noqa
                        for index, novel in enumerate(novel_list_, start=1)
                    )
                )
            )

        return await msg.edit_original_response(
            embed=Embed(title="無搜尋結果", color=discord.Color.red())
        )

    # @search.error
    # async def on_info_error(self, ctx: ApplicationContext, error):
    #     print(error)
    #     await ctx.respond(
    #         embed=Embed(title="發生未知的錯誤", color=discord.Color.red()),
    #         ephemeral=True
    #     )

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
    bot.add_cog(SearchCog(bot))
