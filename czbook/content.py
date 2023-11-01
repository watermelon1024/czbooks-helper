import asyncio

import aiohttp

from .http import fetch_as_html
from .utils import now_timestamp, time_diff, is_out_of_date
from .chapter import ChapterInfo, ChapterList
from .error import ChapterNoContentError


class GetContentState:
    def __init__(
        self,
        task: asyncio.Task = None,
        start_time: float = None,
        current: int = None,
        total: int = None,
    ) -> None:
        self.task = task
        self.start_time = start_time or now_timestamp()
        self.current = current
        self.total = total
        self.percentage: float = 0
        self.eta: float = 0
        self.finished: bool = False

        self._last_update = 0
        self._progress_bar_cache = None

    def _progress_bar(
        self, filled_char: str = "-", bar_length: int = 27
    ) -> tuple[float, str]:
        percentage = self.current / self.total
        filled_length = int(bar_length * percentage)
        return (
            percentage,
            f"```[{filled_char*filled_length}{' '*(bar_length-filled_length)}]```",
        )

    def get_progress(self) -> str:
        if not (now := is_out_of_date(self._last_update, 1)):
            return self._progress_bar_cache

        total_diff = time_diff(self.start_time, now)
        progress, bar = self._progress_bar()
        eta = total_diff / progress - total_diff
        eta_display = f"`{eta:.1f}`秒" if progress > 0.1 or total_diff > 10 else "計算中..."

        self.percentage = progress
        self.eta = eta
        self._progress_bar_cache = f"第{self.current}/{self.total}章 {progress*100:.1f}%\n{bar}預計剩餘時間：{eta_display}"  # noqa
        self._last_update = now

        return self._progress_bar_cache


class GetContent:
    async def get_content(
        self, chapter_list: ChapterList, state: GetContentState
    ) -> None:
        """
        Get the content of the novel.
        """
        async with aiohttp.ClientSession() as session:
            for index, chapter in enumerate(chapter_list, start=1):
                state.current = index
                try:
                    soup = await fetch_as_html(chapter.url, session)
                    chapter.content = soup.find("div", class_="content").text
                except Exception as e:
                    print(f"Error when getting {chapter.url}: {e}")
                    chapter._error = str(e)

        state.finished = True
        return None

    @classmethod
    def start(cls: type["GetContent"], chapter_list: ChapterList) -> GetContentState:
        state = GetContentState(None, None, 0, chapter_list.total_chapter_count)
        task = asyncio.create_task(cls.get_content(cls, chapter_list, state))
        state.task = task

        return state


def _get_context_without_space(s: str, pos: int, length: int, keyword_len: int) -> str:
    result = ""

    current_pos = pos
    count = -1
    while current_pos >= 0 and count < length:
        if not (c := s[current_pos]).isspace():
            result = c + result
            count += 1
        current_pos -= 1

    s_len = len(s)
    current_pos = pos + 1
    count = -keyword_len + 1
    while current_pos < s_len and count < length:
        if not (c := s[current_pos]).isspace():
            result += c
            count += 1
        current_pos += 1

    return result


class ContentSearchResult:
    def __init__(
        self,
        chapter: ChapterInfo,
        keyword: str,
        position: int,
        context_length: int,
        highlight: str = None,
    ) -> None:
        self._chapter = chapter
        self._keyword = keyword
        self._keyword_len = len(keyword)
        self._position = position
        self._context_len = context_length
        self._highlight = highlight
        self._display = None
        self._jump_url = None

    @property
    def chapter(self) -> ChapterInfo:
        return self._chapter

    @property
    def keyword(self) -> str:
        return self._keyword

    @property
    def display(self) -> str:
        """
        Retrun the raw context without whitespace.
        """
        if not self._display:
            self._display = _get_context_without_space(
                self.chapter.content,
                self._position,
                self._context_len,
                self._keyword_len,
            )
        return self._display

    def display_highlight(self, highlight: str = None) -> str:
        """
        highlight must be like: "**%s**"
        """
        return self.display.replace(
            self.keyword, (highlight % self.keyword) if highlight else self._highlight
        )

    @property
    def jump_url(self) -> str:
        if not self._jump_url:
            start_index = self._context_len - 5
            end_index = -self._context_len + 4
            self._jump_url = (
                f"{self.chapter.url}#:~:text="
                f"{self.display_highlight('-,%s,-')[start_index:end_index]}"
            )

        return self._jump_url


def _search_content_pos(text: str, keyword: str) -> list[int]:
    keyword_position = 0
    context_positions: list[int] = []

    while (keyword_position := text.find(keyword, keyword_position + 1)) != -1:
        context_positions.append(keyword_position)

    return context_positions


def search_content(
    chapter_list: ChapterList,
    keyword: str,
    highlight: str = None,
    context_length: int = 20,
) -> list[ContentSearchResult]:
    """
    Args:
        highlight must be like: "**%s**"

    Return: `list[ContentSearchResult]`
        the search results' context in content with the keyword.

    Raise:
        if chapter hasn't had content.
    """
    if highlight:
        highlight = highlight % keyword
    results = []
    for chapter in chapter_list:
        if not chapter.content:
            raise ChapterNoContentError(f"Chapter '{chapter.name}' hasn't had content")
        results.extend(
            ContentSearchResult(
                chapter=chapter,
                keyword=keyword,
                position=pos,
                context_length=context_length,
                highlight=highlight,
            )
            for pos in _search_content_pos(chapter.content, keyword)
        )

    return results
