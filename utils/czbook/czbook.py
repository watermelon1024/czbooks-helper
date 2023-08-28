from discord import Embed, Colour

from . import utils
from .comment import Comment, update_comments, comments_embed
from .color import get_random_theme_color
from .get_content import GetContent, GetContentState
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
        self._get_content_state: GetContentState = None

    def get_theme_color(self) -> Colour:
        return get_random_theme_color(self.theme_colors)

    def overview_embed(self, from_cache: bool = True) -> Embed:
        if self._overview_embed_cache and from_cache:
            self._overview_embed_cache.color = self.get_theme_color()
            return self._overview_embed_cache

        embed = Embed(
            title=self.title,
            description=f"""- 作　者：{self.author}
- 狀　態：{self.state} ({self.last_update}更新)
- 總字數：{f'`{self.words_count}`字' if self.words_count else '`請點擊取得內文以取得字數`'}
- 觀看數：`{self.views}`次
- 章節數：`{len(self.chapter_list)}`章
- 分　類：{self.category}""",
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
                utils.hyper_link_list_to_str(self.hashtags, 1024, "、", "⋯⋯")
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
            description=utils.hyper_link_list_to_str(
                self.chapter_list, 4096, "、", "⋯⋯"
            ),
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

    def get_content(self) -> GetContentState:
        if not self._get_content_state:
            self._get_content_state = GetContent.start(self)
        return self._get_content_state

    def cencel_get_content(self) -> None:
        if not self._get_content_state:
            return
        self._get_content_state.task.cancel()
        self._get_content_state = None
