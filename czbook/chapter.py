class ChapterInfo:
    def __init__(self, name: str, url: str, content: str = None) -> None:
        self.name = name
        self.url = url
        self.content = content
        self._maybe_not_content: bool = None

    @property
    def maybe_not_conetent(self):
        if self._maybe_not_content is None:
            self._maybe_not_content = len(self.content) < 1024
        return self._maybe_not_content


class ChapterList(list):
    def __init__(self, chapter_list: list[ChapterInfo] = []) -> None:
        super().__init__(chapter_list)
