import random

from discord import Embed, Colour

import czbook


class Novel(czbook.Novel):
    _overview_embed_cache: Embed = None
    _chapter_embed_cache: Embed = None
    _comment_embed_cache: Embed = None

    def get_theme_color(self) -> Colour:
        return (
            Colour(random.choice(self.info.thumbnail.theme_color))
            if self.info.thumbnail
            else Colour.random()
        )

    def overview_embed(self, from_cache: bool = True) -> Embed:
        if self._overview_embed_cache and from_cache:
            self._overview_embed_cache.color = self.get_theme_color()
            return self._overview_embed_cache

        embed = Embed(
            title=self.info.title,
            description=(
                f"- 作　者：{self.info.author}\n"
                f"- 狀　態：{self.info.state} ({self.info.last_update}更新)\n"
                f"- 總字數：{f'`{self.word_count}`字' if self.word_count else '`點擊取得內文以取得字數`'}\n"
                f"- 觀看數：`{self.info.views}`次\n"
                f"- 章節數：`{len(self.chapter_list)}`章\n"
                f"- 分　類：{self.info.category}"
            ),
            url=f"https://czbooks.net/n/{self.id}",
            color=self.get_theme_color(),
        )
        embed.add_field(
            name="書本簡述",
            value=(
                self.info.description
                if len(self.info.description) < 1024
                else self.info.description[:1021] + "⋯⋯"
            ),
            inline=False,
        )
        embed.add_field(
            name="標籤",
            value=(
                czbook.utils.hyper_link_list_to_str(self.info.hashtags, 1024, "、", "⋯⋯")
                if self.info.hashtags
                else "尚無標籤"
            ),
            inline=False,
        )
        if self.info.thumbnail:
            embed.set_thumbnail(url=self.info.thumbnail.url)

        self._overview_embed_cache = embed
        return self._overview_embed_cache

    def chapter_embed(self, from_cache: bool = True) -> Embed:
        if self._chapter_embed_cache and from_cache:
            self._chapter_embed_cache.color = self.get_theme_color()
            return self._chapter_embed_cache

        self._chapter_embed_cache = Embed(
            title=f"{self.info.title}章節列表",
            description=czbook.utils.hyper_link_list_to_str(
                self.chapter_list, 4096, "、", "⋯⋯"
            ),
            url=f"https://czbooks.net/n/{self.id}",
            color=self.get_theme_color(),
        )
        return self._chapter_embed_cache

    async def comment_embed(self, update_when_out_of_date: bool = True):
        if update_when_out_of_date and (
            now := czbook.utils.is_out_of_date(self._comment_last_update, 600)
        ):
            self._comment_last_update = now
            await self.update_comments()
            self._comment_embed_cache = _comment_embed(self)
        elif not self._comment_embed_cache:
            self._comment_embed_cache = _comment_embed(self)

        return self._comment_embed_cache

    @classmethod
    def load_from_json(cls: type["Novel"], data: dict) -> "Novel":
        return cls.from_original_novel(super().load_from_json(data))

    @classmethod
    def from_original_novel(cls: type["Novel"], original: czbook.Novel) -> "Novel":
        return cls(
            id=original.id,
            info=original.info,
            content_cache=original.content_cache,
            word_count=original.word_count,
            chapter_list=original.chapter_list,
            comment=original.comment,
            last_fetch_time=original.last_fetch_time,
        )


def _comment_embed(novel: Novel) -> Embed:
    embed = Embed(
        title=f"{novel.info.title}評論列表",
        url=f"https://czbooks.net/n/{novel.id}",
        color=novel.get_theme_color(),
    )
    for comment in novel.comment:
        embed.add_field(
            name=comment.author,
            value=f"```{comment.message}```",
            inline=False,
        )
        if len(embed) > 6000:
            embed.remove_field(-1)
            break

    return embed
