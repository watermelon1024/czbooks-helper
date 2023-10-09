from .novel_info import NovelInfo, Author, Category, HashtagList, Thumbnail
from .chapter import ChapterList, ChapterInfo
from .comment import CommentList
from .get_content import GetContent, GetContentState
from .http import fetch_as_html
from .timestamp import now_timestamp


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
            "thumbnail": self.info.thumbnail.to_dict(),
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


async def fetch_novel(id: str, first: bool = True) -> Novel:
    soup = await fetch_as_html(f"https://czbooks.net/n/{id}")
    # state / detail / info
    state_children = soup.find("div", class_="state").find_all("td")
    detail_div = soup.find("div", class_="novel-detail")
    thumbnail_url = detail_div.find("img").get("src")
    category_a = state_children[9].contents[0].text
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
            [
                hashtag.text
                for hashtag in soup.find("ul", class_="hashtag").find_all("a")[:-1]
            ]
        ),
    )
    if info.thumbnail and first:
        info.thumbnail.theme_color
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
        comment=CommentList(),
        last_fetch_time=now_timestamp(),
    )
