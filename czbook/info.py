from .http import HyperLink
from .category import Category


class Author(HyperLink):
    def __init__(self, name: str) -> None:
        self.name = name
        super().__init__(name, f"https://czbooks.net/a/{name}")


class Thumbnail:
    def __init__(self, url: str) -> None:
        self.url = url

    @property
    def theme_color(self):
        ...


class NovelInfo:
    """
    id: `str`
        the ID of the novel
    title: `str`
        the title of the novel
    description: `str`
        the description of the novel
    thumbnail: `Thumbnail`
        the description of the novel
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
    hashtag: list[HyperLink]
        the description of the novel
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
        hashtags: list[HyperLink],
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
