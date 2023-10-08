from .author import Author
from .category import Category
from .hashtag import HashtagList
from .thumbnail import Thumbnail


class NovelInfo:
    """
    id: `str`
        the ID of the novel
    title: `str`
        the title of the novel
    description: `str`
        the description of the novel
    thumbnail: `Thumbnail`
        the thumbnail of the novel
    author: `Author`
        the author of the novel
    state: `str`
        the state of the novel
        usually is `連載中` or `已完結`
    last_update: `str`
        the latest time when the novel update
        format: `YYYY-MM-DD`
    views: `int`
        the views of the novel
    category: `Category`
        the category of the novel
    hashtag: `HashtagList`
        the list of the novel hashtags
    """

    def __init__(
        self,
        id: str,
        title: str,
        description: str,
        thumbnail: Thumbnail | None,
        author: Author,
        state: str,
        last_update: str,
        views: int,
        category: Category,
        hashtags: HashtagList,
    ) -> None:
        id = id
        title = title
        description = description
        thumbnail = thumbnail
        author = author
        state = state
        last_update = last_update
        views = views
        category = category
        hashtags = hashtags
