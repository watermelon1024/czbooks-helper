import re

from .comment import Comment, update_comments
from .const import RE_BOOK_CODE
from .get_content import GetContent, GetContentState
from .http import HyperLink


def get_code(s: str) -> str | None:
    if match := re.search(RE_BOOK_CODE, s):
        return match.group(2)
    return None


class Novel:
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
        self.word_count = word_count
        self.hashtags = hashtags
        self.chapter_list = chapter_list
        self.comments = comments
        self.last_fetch_time = last_fetch_time

        self._comment_last_update: float = 0
        self._get_content_state: GetContentState = None

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

    def to_dict(self) -> dict:
        return {
            "code": self.code,
            "title": self.title,
            "description": self.description,
            "thumbnail": self.thumbnail,
            "main_color": self.theme_colors,
            "author": self.author.to_dict(),
            "state": self.state,
            "last_update": self.last_update,
            "views": self.views,
            "category": self.category.to_dict(),
            # "content_cache": self.content_cache,
            "words_count": self.word_count,
            "hashtags": [hashtag.to_dict() for hashtag in self.hashtags],
            "chapter_list": [chapter.to_dict() for chapter in self.chapter_list],
            # "comments": [comment.to_dict() for comment in self.comments],
            "last_fetch_time": self.last_fetch_time,
        }


def load_from_json(data: dict) -> Novel:
    return Novel(
        code=data.get("code"),
        title=data.get("title"),
        description=data.get("description"),
        thumbnail=data.get("thumbnail"),
        theme_colors=data.get("main_color"),
        author=HyperLink(*data.get("author").values()),
        state=data.get("state"),
        last_update=data.get("last_update"),
        views=data.get("views"),
        category=HyperLink(*data.get("category").values()),
        content_cache=bool(data.get("words_count")),
        word_count=data.get("words_count"),
        hashtags=[HyperLink(*hashtag.values()) for hashtag in data.get("hashtags")],
        chapter_list=[
            HyperLink(*chapter.values()) for chapter in data.get("chapter_list")
        ],
        comments=[],
        last_fetch_time=data.get("last_fetch_time", 0),
    )
