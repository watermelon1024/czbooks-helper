from .novel_info import NovelInfo, Author, Category, HashtagList
from .chapter import ChapterList
from .comment import CommentList
from .get_content import GetContent, GetContentState


class Novel:
    def __init__(
        self,
        id: str,
        info: NovelInfo,
        # content_cache: bool,
        # word_count: int,
        chapter_list: ChapterList,
        comment: CommentList,
        last_fetch_time: float = 0,
    ) -> None:
        self.id = id
        self.info = info
        # self.content_cache = content_cache
        # self.word_count = word_count
        self.chapter_list = chapter_list
        self.comment = comment
        self.last_fetch_time = last_fetch_time

        self._comment_last_update: float = 0
        self._get_content_state: GetContentState = None

    async def update_comments(self) -> None:
        await self.comment.update()

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
            "code": self.id,
            "title": self.info.title,
            "description": self.info.description,
            "thumbnail": self.info.thumbnail,
            "author": self.info.author.to_dict(),
            "state": self.info.state,
            "last_update": self.info.last_update,
            "views": self.info.views,
            "category": self.info.category.to_dict(),
            # "content_cache": self.content_cache,
            # "words_count": self.word_count,
            "hashtags": [hashtag.to_dict() for hashtag in self.info.hashtags],
            "chapter_list": [chapter.to_dict() for chapter in self.chapter_list],
            # "comments": [comment.to_dict() for comment in self.comments],
            "last_fetch_time": self.last_fetch_time,
        }

    @classmethod
    def load_from_json(cls: "Novel", data: dict) -> "Novel":
        return Novel(
            id=(id := data.get("id")),
            info=NovelInfo(
                id=id,
                title=data.get("title"),
                description=data.get("description"),
                thumbnail=data.get("thumbnail"),
                author=Author(data.get("author")),
                state=data.get("state"),
                last_update=data.get("last_update"),
                views=data.get("views"),
                category=Category(*data.get("category").values()),
                hashtags=HashtagList.from_list(data.get("hashtags", [])),
            ),
            chapter_list=ChapterList(),
            comment=CommentList(id),
            last_fetch_time=data.get("last_fetch_time", 0),
        )
