from typing import Literal

import discord

from discord import Embed, ApplicationContext, Interaction, OptionChoice
from discord.ui import View, Select

import czbook
from bot import BaseCog, Bot
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
        self,
        ctx: ApplicationContext,
        keyword: str,
        by: Literal["name", "hashtag", "author"],
    ):
        await ctx.defer()
        if results := await czbook.search(keyword, by):
            return await ctx.respond(
                embed=Embed(
                    title="搜尋結果",
                    description="\n".join(
                        f"{index}. [{novel.novel_title}](https://czbooks.net/n/{novel.id})"  # noqa
                        for index, novel in enumerate(results[:20], start=1)
                    ),
                    color=discord.Color.green(),
                ),
                view=SearchView(self.bot, results[:20]),
            )

        return await ctx.respond(embed=Embed(title="無搜尋結果", color=discord.Color.red()))

    @simple_search.error
    async def on_simple_search_error(self, ctx: ApplicationContext, error):
        await ctx.respond(
            embed=Embed(title="發生未知的錯誤", color=discord.Color.red()),
            ephemeral=True,
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
        self,
        ctx: ApplicationContext,
        name: str,
        hashtag: str,
        author: str,
    ):
        await ctx.defer()
        if results := await czbook.search_advance(
            name=name or None, hashtag=hashtag.split(",") or None, author=author or None
        ):
            return await ctx.respond(
                embed=Embed(
                    title="搜尋結果",
                    description="\n".join(
                        f"{index}. [{novel.novel_title}](https://czbooks.net/n/{novel.id})"  # noqa
                        for index, novel in enumerate(results[:20], start=1)
                    ),
                    color=discord.Color.green(),
                ),
                view=SearchView(self.bot, results[:20]),
            )

        return await ctx.respond(embed=Embed(title="無搜尋結果", color=discord.Color.red()))

    @advanced_search.error
    async def on_advanced_search_error(self, ctx: ApplicationContext, error):
        await ctx.respond(
            embed=Embed(title="發生未知的錯誤", color=discord.Color.red()),
            ephemeral=True,
        )

    @search_group.command(
        guild_only=True,
        name="content",
        description="內容搜尋",
    )
    @discord.option(
        "link",
        str,
        description="欲搜尋的書本",
    )
    @discord.option(
        "keyword",
        str,
        description="欲搜尋的關鍵字",
    )
    async def content(
        self,
        ctx: ApplicationContext,
        link: str,
        keyword: str,
    ):
        await ctx.defer()

        try:
            novel = await self.bot.db.get_or_fetch_novel(czbook.utils.get_code(link) or link)
            results = czbook.search_content(novel.chapter_list, keyword, context_length=8)
        except czbook.NotFoundError:
            return await ctx.respond(embed=Embed(title="未知的書本", color=discord.Color.red()))
        except czbook.ChapterNoContentError:
            return await ctx.respond(embed=Embed(title="該書尚未取得內文", color=discord.Color.red()))
        if not results:
            return await ctx.respond(embed=Embed(title="無搜尋結果", color=discord.Color.red()))

        embed = Embed(title=f"{novel.title}搜尋結果", url=f"https://czbooks.net/n/{novel.id}")
        for result in results:
            embed.add_field(
                name=f"{result.chapter.name}",
                value=f"[{result.display_highlight('__***%s***__')}]({result.jump_url})",
                inline=False,
            )
            if len(embed) > 6000:
                embed.remove_field(-1)
                break
        embed.set_footer(text=f"已顯示{len(embed.fields)}/共{len(results)}筆結果")

        await ctx.respond(embed=embed)

    @discord.Cog.listener()
    async def on_ready(self):
        self.bot.add_view(SearchView(self.bot))


class SearchView(View):
    def __init__(self, bot: Bot, options: list[czbook.SearchResult] = []):
        super().__init__(timeout=None)
        self.bot = bot

        self.select = Select(
            custom_id="search_select",
            placeholder="請選擇",
            options=[
                discord.SelectOption(
                    label=f"{index}. {novel.novel_title}",
                    value=novel.id,
                )
                for index, novel in enumerate(options, start=1)
            ],
            row=0,
        )
        self.select.callback = self.select_callback
        self.add_item(self.select)

    async def select_callback(self, interaction: Interaction):
        code = interaction.data["values"][0]
        print(f"{interaction.user} used /info link: {code}")
        await interaction.response.defer()

        novel = await self.bot.db.get_or_fetch_novel(code)
        await interaction.followup.send(
            embed=novel.overview_embed(),
            view=InfoView(self.bot),
        )


def setup(bot: Bot):
    bot.add_cog(SearchCog(bot))
