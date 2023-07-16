import discord

from discord import Embed, ApplicationContext, Interaction, Bot, OptionChoice
from discord.ui import View, Select

from bot import BaseCog
from utils.czbooks import (
    HyperLink,
    get_book,
    fetch_book,
    search,
)
from cogs.info import InfoView


class SearchCog(BaseCog):
    def __init__(self, bot: Bot) -> None:
        super().__init__(bot)

    search_group = discord.SlashCommandGroup("search", "搜尋小說")

    @search_group.command(
        guild_only=True,
        name="simple",
        description="基本搜尋",
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
        default="name",
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
                ),
                view=SearchView(self.bot, result[:20])
            )

        return await msg.edit_original_response(
            embed=Embed(title="無搜尋結果", color=discord.Color.red())
        )

    @simple_search.error
    async def on_simple_search_error(self, ctx: ApplicationContext, error):
        print(error)
        await ctx.respond(
            embed=Embed(title="發生未知的錯誤", color=discord.Color.red()),
            ephemeral=True
        )

    @search_group.command(
        guild_only=True,
        name="advanced",
        description="進階搜尋",
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

    @advanced_search.error
    async def on_advanced_search_error(self, ctx: ApplicationContext, error):
        print(error)
        await ctx.respond(
            embed=Embed(title="發生未知的錯誤", color=discord.Color.red()),
            ephemeral=True
        )

    @discord.Cog.listener()
    async def on_ready(self):
        self.bot.add_view(SearchView(self.bot))


class SearchView(View):
    def __init__(self, bot: Bot, options: list[HyperLink] = []):
        super().__init__(timeout=None)
        self.bot = bot

        self.select = Select(
            custom_id="search_select",
            placeholder="請選擇",
            options=[
                discord.SelectOption(
                    label=novel.text, value=novel.link
                ) for novel in options
            ],
            row=0,
        )
        self.select.callback = self.select_callback
        self.add_item(self.select)

    async def select_callback(self, interaction: Interaction):
        code = interaction.data["values"][0]
        print(f"{interaction.user} use /info link: {code}")

        if book := get_book(code):
            return await interaction.response.send_message(
                embed=book.overview_embed(),
                view=InfoView(self.bot)
            )

        msg = await interaction.response.send_message(
            embed=Embed(title="資料擷取中，請稍後...")
        )
        book = await fetch_book(code)
        await msg.edit_original_response(
            embed=book.overview_embed(),
            view=InfoView(self.bot)
        )


def setup(bot: Bot):
    bot.add_cog(SearchCog(bot))
