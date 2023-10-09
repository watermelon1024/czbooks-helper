import re

from .const import RE_CHINESE_CHARS


class ChapterInfo:
    def __init__(self, name: str, url: str, content: str = None) -> None:
        self.name = name
        self.url = url
        self.content = content
        self._word_count: int = None
        self._maybe_not_content: bool = None

    @property
    def word_count(self) -> int:
        if self.content is None:
            return 0
        if self._word_count is None:
            self._word_count = len(re.findall(RE_CHINESE_CHARS, self.content))
        return self._word_count

    @property
    def maybe_not_conetent(self) -> bool:
        if self._maybe_not_content is None:
            self._maybe_not_content = self.word_count < 1024
        return self._maybe_not_content

    def to_dict(self) -> dict:
        return {"name": self.name, "url": self.url}


class ChapterList(list[ChapterInfo]):
    def __init__(self, chapter_list: list[ChapterInfo] = []) -> None:
        super().__init__(chapter_list)
        self._total_chapter_count: int = None
        self._maybe_content_count: int = None

    @property
    def total_chapter_count(self) -> int:
        if self._total_chapter_count is None:
            self._total_chapter_count = len(self)
        return self._total_chapter_count

    @property
    def maybe_content_count(self) -> int:
        return self._maybe_content_count or self.total_chapter_count
