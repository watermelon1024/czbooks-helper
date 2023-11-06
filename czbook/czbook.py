import asyncio
from .novel_info import NovelInfo, Author, Category, HashtagList, Thumbnail
from .chapter import ChapterList, ChapterInfo
from .comment import CommentList
from .content import GetContent, GetContentState
from .http import fetch_as_html
from .utils import now_timestamp


class Novel:
    def __init__(
        self,
        id: str,
        info: NovelInfo,
        chapter_list: ChapterList,
        comment: CommentList = None,
        word_count: int = None,
        last_fetch_time: float = 0,
    ) -> None:
        self.id = id
        self.info = info
        self.chapter_list = chapter_list
        self.comment = comment or CommentList(id)
        self._word_count = word_count
        self._content_cache: bool = bool(word_count)
        self.last_fetch_time = last_fetch_time

        self._comment_last_update: float = 0
        self._get_content_state: GetContentState = None

    @property
    def title(self):
        return self.info.title

    @property
    def description(self):
        return self.info.description

    @property
    def thumbnail(self):
        return self.info.thumbnail

    @property
    def author(self):
        return self.info.author

    @property
    def state(self):
        return self.info.state

    @property
    def last_update(self):
        return self.info.last_update

    @property
    def views(self):
        return self.info.views

    @property
    def category(self):
        return self.info.category

    @property
    def hashtags(self):
        return self.info.hashtags

    @property
    def word_count(self) -> int:
        if (not self._word_count) and self._content_cache:
            self._word_count = sum(chapter.word_count for chapter in self.chapter_list)
        return self._word_count

    @property
    def content_cache(self) -> bool:
        return self._content_cache

    @property
    def content(self) -> str:
        info = (
            f"{self.title} —— {self.author.name}\n"
            f"連結：https://czbooks.net/n/{self.id}\n"
            f"作者：{self.author.name}\n"
            f"總章數：{self.chapter_list.total_chapter_count}\n"
            f"總字數：{self.word_count}\n"
        )
        content = "\n\n\n".join(
            f"{'-'*30} {chapter.name} {'-'*30}\n"
            + (
                f"本章擷取失敗，請至網站閱讀：{chapter.url}"
                if chapter._error
                else (("(本章可能非內文)\n\n" if chapter.maybe_not_conetent else "\n") + chapter.content)
            )
            for chapter in self.chapter_list
        )
        return info + "\n\n" + content

    async def update_comments(self) -> None:
        await self.comment.update()

    async def _get_content(self) -> None:
        await self._get_content_state.task
        self._content_cache = True

    def get_content(self) -> GetContentState:
        if not self._get_content_state:
            self._get_content_state = GetContent.start(self.chapter_list)
            loop = asyncio.get_event_loop()
            loop.create_task(self._get_content())
        return self._get_content_state

    def cencel_get_content(self) -> None:
        if not self._get_content_state:
            return
        self._get_content_state.task.cancel()
        self._get_content_state = None

    async def update(self) -> bool:
        """
        Return True if updated.
        """
        updated_novel = await fetch_novel(self.id, False)
        if updated_novel.last_update != self.last_update:
            self = updated_novel
            await self.thumbnail.get_theme_colors()
            return True
        self.last_fetch_time = now_timestamp()
        return False

    def to_dict(self) -> dict:
        return {
            "code": self.id,
            "title": self.title,
            "description": self.description,
            "thumbnail": self.thumbnail.to_dict() if self.thumbnail else None,
            "author": self.author.to_dict(),
            "state": self.state,
            "last_update": self.last_update,
            "views": self.views,
            "category": self.category.to_dict(),
            "hashtags": [hashtag.to_dict() for hashtag in self.hashtags],
            "chapter_list": [chapter.to_dict() for chapter in self.chapter_list],
            # "comments": [comment.to_dict() for comment in self.comments],
            "word_count": self.word_count,
            "last_fetch_time": self.last_fetch_time,
        }

    @classmethod
    def load_from_json(cls: type["Novel"], data: dict) -> "Novel":
        return cls(
            id=(id := data.get("id")),
            info=NovelInfo(
                id=id,
                title=data.get("title"),
                description=data.get("description"),
                thumbnail=(
                    Thumbnail.from_json(thumbnail)
                    if (thumbnail := data.get("thumbnail"))
                    else None
                ),
                author=Author(data.get("author").get("text")),
                state=data.get("state"),
                last_update=data.get("last_update"),
                views=data.get("views"),
                category=Category(*data.get("category").values()),
                hashtags=HashtagList.from_list(
                    [datum.get("text") for datum in data.get("hashtags", [])]
                ),
            ),
            chapter_list=ChapterList.from_json(data.get("chapter_list")),
            # comment=CommentList(id),
            word_count=data.get("word_count"),
            last_fetch_time=data.get("last_fetch_time", 0),
        )


async def fetch_novel(id: str, first: bool = True) -> Novel:
    soup = await fetch_as_html(f"https://czbooks.net/n/{id}")
    # state / detail / info
    state_children = soup.find("div", class_="state").find_all("td")
    detail_div = soup.find("div", class_="novel-detail")
    thumbnail_url = detail_div.find("img").get("src")
    category_a = state_children[9].contents[0]
    info = NovelInfo(
        id=id,
        title=detail_div.find("span", class_="title").text,
        description=detail_div.find("div", class_="description").text,
        thumbnail=Thumbnail(thumbnail_url)
        if thumbnail_url.startswith("https://img.czbooks.net")
        else None,
        author=Author(detail_div.find("span", class_="author").contents[1].text),
        state=state_children[1].text,
        last_update=state_children[7].text,
        views=state_children[5].text,
        category=Category(category_a.text, "https:" + category_a["href"]),
        hashtags=HashtagList.from_list(
            [hashtag.text for hashtag in soup.find("ul", class_="hashtag").find_all("a")[:-1]]
        ),
    )
    if info.thumbnail and first:
        await info.thumbnail.get_theme_colors()
    # chapter list
    chapter_list = ChapterList(
        [
            ChapterInfo(chapter.text, "https:" + chapter["href"])
            for chapter in soup.find("ul", id="chapter-list").find_all("a")
        ]
    )

    return Novel(
        id=id,
        info=info,
        chapter_list=chapter_list,
        last_fetch_time=now_timestamp(),
    )
