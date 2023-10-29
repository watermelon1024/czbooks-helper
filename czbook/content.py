import asyncio

import aiohttp

from .http import fetch_as_html
from .utils import now_timestamp, time_diff, is_out_of_date
from .chapter import ChapterInfo, ChapterList


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


class ContentSearchResult:
    def __init__(
        self, chapter: ChapterInfo, context: str, position: int = None
    ) -> None:
        self.chapter = chapter
        self.context = context
        self.position = position


def _search_content(
    text: str, keyword: str, highlight: str = None, context_length: int = 20
) -> list[str]:
    keyword_length = len(keyword)
    keyword_position = 0
    context_positions: list[tuple[int, int]] = []

    while (keyword_position := text.find(keyword, keyword_position + 1)) != -1:
        start_position = max(0, keyword_position - context_length)
        end_position = keyword_position + keyword_length + context_length

        if context_positions and start_position <= context_positions[-1][1]:
            context_positions[-1] = (context_positions[-1][0], end_position)
        else:
            context_positions.append((start_position, end_position))
    if highlight:
        return [
            text[start:end].strip().replace(keyword, highlight % keyword)
            for (start, end) in context_positions
        ]

    return [text[start:end] for (start, end) in context_positions]


def search_content(
    chapter_list: ChapterList,
    keyword: str,
    highlight: str = None,
    context_length: int = 20,
) -> list[ContentSearchResult]:
    """
    Return: `list[ContentSearchResult]`
        the search results' context in content with the keyword.

    Raise:
        if chapter hasn't had content.
    """
    results = []
    for chapter in chapter_list:
        if not chapter.content:
            raise RuntimeError(f"Chapter '{chapter.name}' hasn't had content")
        results.extend(
            ContentSearchResult(chapter=chapter, context=result)
            for result in _search_content(
                chapter.content, keyword, highlight, context_length
            )
        )

    return results


def _search_content_sentences(
    text: str, keyword: str, highlight: str = None, context_sentences: int = 2
) -> list[str]:
    sentences = text.split("\n")
    sentences_index: list[tuple[int, int]] = []
    start_index = 0
    for index, sentence in enumerate(sentences):
        if keyword in sentence:
            start_index = max(0, index - context_sentences)
            end_index = index + context_sentences + 1
            if sentences_index and start_index <= sentences_index[-1][1]:
                sentences_index[-1] = (sentences_index[-1][0], end_index)
            else:
                sentences_index.append((start_index, end_index))

    return [
        "\n".join(s.strip() for s in sentences[start:end]).replace(
            keyword, highlight % keyword
        )
        for (start, end) in sentences_index
    ]


def search_content_sentences(
    chapter_list: ChapterList,
    keyword: str,
    highlight: str = None,
    context_sentences: int = 2,
) -> list[ContentSearchResult]:
    """
    Return: `list[ContentSearchResult]`
        the search results' context sentences in content with the keyword.

    Raise:
        if chapter hasn't had content.
    """
    results = []
    for chapter in chapter_list:
        if not chapter.content:
            raise RuntimeError(f"Chapter '{chapter.name}' hasn't had content")
        results.extend(
            ContentSearchResult(chapter=chapter, context=result)
            for result in _search_content_sentences(
                chapter.content, keyword, highlight, context_sentences
            )
        )

    return results
