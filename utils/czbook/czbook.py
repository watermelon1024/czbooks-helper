from discord import Embed, Colour

from .comment import Comment, update_comments, comments_embed
from .color import get_random_theme_color
from .http import HyperLink
from .timestamp import now_timestamp


class Czbook:
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
        words_count: int,
        hashtags: list[HyperLink],
        chapter_list: list[HyperLink],
        comments: list[Comment],
        last_fetch_time: float = 0,
    ) -> None:
        self.code = code
        self.title = title
        self.description = description
        self.thumbnail = thumbnail
        self.theme_colors = theme_colors
        self.author = author
        self.state = state
        self.last_update = last_update
        self.views = views
        self.category = category
        self.content_cache = content_cache
        self.words_count = words_count
        self.hashtags = hashtags
        self.chapter_list = chapter_list
        self.comments = comments
        self.last_fetch_time = last_fetch_time

        self._overview_embed_cache: Embed = None
        self._chapter_embed_cache: Embed = None
        self._comments_embed_cache: Embed = None
        self._comment_last_update: float = None

    def get_theme_color(self) -> Colour:
        return get_random_theme_color(self.theme_colors)

    def chapter_embed(self, from_cache: bool = True) -> Embed:
        if self._chapter_embed_cache and from_cache:
            self._chapter_embed_cache.color = self.get_theme_color()
            return self._chapter_embed_cache

        chapter_len = len(
            chapter_text_ := "、".join(
                str(chapter) for chapter in self.chapter_list[-8:]
            )
        )
        chapter_text = ""
        for chapter in self.chapter_list[:-8]:
            chapter_len += len(text := f"{chapter}、")
            if chapter_len > 4094:
                chapter_text += "⋯⋯、"
                break
            chapter_text += text

        self._chapter_embed_cache = Embed(
            title=f"{self.title}章節列表",
            description=chapter_text + chapter_text_,
            url=f"https://czbooks.net/n/{self.code}",
            color=self.get_theme_color(),
        )
        return self._chapter_embed_cache

    async def comments_embed(self, update_when_out_of_date: bool = True):
        if (
            update_when_out_of_date
            and ((now := now_timestamp()) - self._comment_last_update) > 600
        ):
            self._comment_last_update = now
            await self.update_comments()
            self._comments_embed_cache = comments_embed(self)
        elif not self._comments_embed_cache:
            self._comments_embed_cache = comments_embed(self)

        return self._comments_embed_cache

    async def update_comments(self):
        self.comments = await update_comments(self.code)
