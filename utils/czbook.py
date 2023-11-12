import io
import random
import json

from discord import Embed, Colour

import czbook


class Novel(czbook.Novel):
    _overview_embed_cache: Embed = None
    _chapter_embed_cache: Embed = None
    _comment_embed_cache: Embed = None

    def get_theme_color(self) -> Colour:
        return (
            Colour(random.choice(self.thumbnail.theme_color))
            if self.thumbnail
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
                f"- 章節數：`{self.chapter_list.maybe_content_count}`章\n"
                f"- 分　類：{self.category}"
            ),
            url=f"https://czbooks.net/n/{self.id}",
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
            embed.set_thumbnail(url=self.thumbnail.url)

        self._overview_embed_cache = embed
        return self._overview_embed_cache

    def chapter_embed(self, from_cache: bool = True) -> Embed:
        if self._chapter_embed_cache and from_cache:
            self._chapter_embed_cache.color = self.get_theme_color()
            return self._chapter_embed_cache

        self._chapter_embed_cache = Embed(
            title=f"{self.title}章節列表",
            description=czbook.utils.hyper_link_list_to_str(self.chapter_list, 4096, "、", "⋯⋯"),
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

    async def _get_content(self) -> None:
        await super()._get_content()
        self._overview_embed_cache = None

    @property
    def filelike_content(self) -> io.StringIO:
        return io.StringIO(self.content)

    @classmethod
    def load_from_json(cls: type["Novel"], data: dict) -> "Novel":
        return cls.from_original_novel(super().load_from_json(data))

    @classmethod
    def from_original_novel(cls: type["Novel"], original: czbook.Novel) -> "Novel":
        return cls(
            id=original.id,
            info=original.info,
            chapter_list=original.chapter_list,
            comment=original.comment,
            word_count=original.word_count,
            last_fetch_time=original.last_fetch_time,
        )


def _comment_embed(novel: Novel) -> Embed:
    embed = Embed(
        title=f"{novel.title}評論列表",
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


def hashtag_list_to_str(hashtags: czbook.HashtagList) -> str:
    return json.dumps([item.text for item in hashtags], ensure_ascii=False)


def hashtag_str_to_list(s: str) -> czbook.HashtagList:
    return czbook.HashtagList([czbook.Hashtag(item) for item in json.loads(s)])


def chapter_list_to_str(chapter_list: czbook.ChapterList) -> str:
    return json.dumps([item.to_dict() for item in chapter_list], ensure_ascii=False)


def chapter_str_to_list(s: str) -> czbook.ChapterList:
    return czbook.ChapterList.from_json(json.loads(s))
