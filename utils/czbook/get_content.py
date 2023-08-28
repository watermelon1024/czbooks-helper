import asyncio
import re
from typing import TYPE_CHECKING


import aiohttp
from bs4 import BeautifulSoup

from .const import RE_CHINESE_CHARS
from .http import HyperLink
from .timestamp import now_timestamp

if TYPE_CHECKING:
    from .czbook import Czbook


class GetContentState:
    def __init__(
        self,
        task: asyncio.Task[tuple[str, int]] = None,
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

        self._last_update = None
        self._progress_bar_cache = None

    def _progress_bar(
        self, filled_char: str = "-", bar_length: int = 28
    ) -> tuple[float, str]:
        percentage = self.current / self.total
        filled_length = int(bar_length * percentage)
        return (
            percentage,
            f"```[{filled_char*filled_length}{' '*(bar_length-filled_length)}]```",
        )

    def get_progress(self) -> str:
        if self._last_update == self.current:
            return self._progress_bar_cache

        total_diff = now_timestamp() - self.start_time
        progress, bar = self._progress_bar()
        eta = total_diff / progress - total_diff
        eta_display = f"`{eta:.1f}`秒" if progress > 0.1 or total_diff > 10 else "計算中..."
        self._progress_bar_cache = f"第{self.current}/{self.total}章 {progress*100:.1f}%{bar}預計剩餘時間：{eta_display}"  # noqa
        self.percentage = progress
        self.eta = eta
        self._last_update = self.current
        return self._progress_bar_cache


class GetContent:
    def __init__(self) -> None:
        pass

    async def get_content(
        self, chapter_list: list[HyperLink], state: GetContentState
    ) -> tuple[str, int]:
        """
        Retrun the content and total word count of the book
        """
        content = ""
        word_count = 0
        # 逐章爬取內容
        async with aiohttp.ClientSession() as session:
            for index, ch in enumerate(chapter_list, start=1):
                state.current = index
                try:
                    async with session.get(ch.url) as response:
                        soup = BeautifulSoup(await response.text(), "html.parser")
                except Exception as e:
                    print(f"Error when getting {ch.url}: {e}")
                # 尋找章節
                ch_name = soup.find("div", class_="name")
                # 尋找內文
                div_content = ch_name.find_next("div", class_="content")
                content += f"\n\n{'='*30} {ch_name.text} {'='*30}\n"
                ch_word_count = len(re.findall(RE_CHINESE_CHARS, div_content.text))
                if ch_word_count < 1024:
                    content += "(本章可能非內文)\n\n"
                else:
                    word_count += ch_word_count
                    content += "\n"
                content += div_content.text

        state.finished = True
        return content, word_count

    @classmethod
    def start(cls: "GetContent", book: "Czbook") -> GetContentState:
        state = GetContentState(None, None, 0, len(book.chapter_list))
        task = asyncio.create_task(cls.get_content(book.chapter_list, state))
        task = asyncio.create_task(cls.get_content(cls, book.chapter_list, state))
        state.task = task

        return state
