import random

from discord import Embed, Colour

import czbook
from czbook.comment import Comment
from czbook.http import HyperLink


class Book(czbook.Book):
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
        word_count: int,
        hashtags: list[HyperLink],
        chapter_list: list[HyperLink],
        comments: list[Comment],
        last_fetch_time: float = 0,
        *args,
        **kwargs,
    ) -> None:
        super().__init__(
            code,
            title,
            description,
            thumbnail,
            theme_colors,
            author,
            state,
            last_update,
            views,
            category,
            content_cache,
            word_count,
            hashtags,
            chapter_list,
            comments,
            last_fetch_time,
        )

        self._overview_embed_cache: Embed = None
        self._chapter_embed_cache: Embed = None
        self._comments_embed_cache: Embed = None

    def get_theme_color(self) -> Colour:
        return (
            Colour(random.choice(self.theme_colors))
            if self.theme_colors
            else Colour.random()
        )

    def overview_embed(self, from_cache: bool = True) -> Embed:
        if self._overview_embed_cache and from_cache:
            self._overview_embed_cache.color = self.get_theme_color()
            return self._overview_embed_cache

        embed = Embed(
            title=self.title,
            description=(
                f"- 作　者：{self.author}\n"
                f"- 狀　態：{self.state} ({self.last_update}更新)\n"
                f"- 總字數：{f'`{self.word_count}`字' if self.word_count else '`點擊取得內文以取得字數`'}\n"
                f"- 觀看數：`{self.views}`次\n"
                f"- 章節數：`{len(self.chapter_list)}`章\n"
                f"- 分　類：{self.category}"
            ),
            url=f"https://czbooks.net/n/{self.code}",
            color=self.get_theme_color(),
        )
        embed.add_field(
            name="書本簡述",
            value=(
                self.description
                if len(self.description) < 1024
                else self.description[:1021] + "⋯⋯"
            ),
            inline=False,
        )
        embed.add_field(
            name="標籤",
            value=(
                czbook.utils.hyper_link_list_to_str(self.hashtags, 1024, "、", "⋯⋯")
                if self.hashtags
                else "尚無標籤"
            ),
            inline=False,
        )
        if self.thumbnail:
            embed.set_thumbnail(url=self.thumbnail)

        self._overview_embed_cache = embed
        return self._overview_embed_cache

    def chapter_embed(self, from_cache: bool = True) -> Embed:
        if self._chapter_embed_cache and from_cache:
            self._chapter_embed_cache.color = self.get_theme_color()
            return self._chapter_embed_cache

        self._chapter_embed_cache = Embed(
            title=f"{self.title}章節列表",
            description=czbook.utils.hyper_link_list_to_str(
                self.chapter_list, 4096, "、", "⋯⋯"
            ),
            url=f"https://czbooks.net/n/{self.code}",
            color=self.get_theme_color(),
        )
        return self._chapter_embed_cache

    async def comments_embed(self, update_when_out_of_date: bool = True):
        if update_when_out_of_date and (
            now := czbook.utils.is_out_of_date(self._comment_last_update, 600)
        ):
            self._comment_last_update = now
            await self.update_comments()
            self._comments_embed_cache = _comments_embed(self)
        elif not self._comments_embed_cache:
            self._comments_embed_cache = _comments_embed(self)

        return self._comments_embed_cache


def _comments_embed(book: Book) -> Embed:
    embed = Embed(
        title=f"{book.title}評論列表",
        url=f"https://czbooks.net/n/{book.code}",
        color=book.get_theme_color(),
    )
    for comment in book.comments:
        embed.add_field(
            name=comment.author,
            value=f"```{comment.message}```",
            inline=False,
        )
        if len(embed) > 6000:
            embed.remove_field(-1)
            break

    return embed
