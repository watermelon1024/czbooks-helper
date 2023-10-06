import asyncio
import re
from typing import TYPE_CHECKING

import aiohttp
from bs4 import BeautifulSoup

from .const import RE_CHINESE_CHARS
from .http import fetch_url
from .timestamp import now_timestamp, time_diff, is_out_of_date

if TYPE_CHECKING:
    from .czbook import Novel


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
    def __init__(self) -> None:
        pass

    async def get_content(
        self, book: "Novel", state: GetContentState
    ) -> tuple[str, int]:
        """
        Retrun the content and total word count of the book
        """
        content = ""
        word_count = 0
        # 逐章爬取內容
        async with aiohttp.ClientSession() as session:
            for index, ch in enumerate(book.chapter_list, start=1):
                state.current = index
                try:
                    soup = BeautifulSoup(
                        await fetch_url(session, ch.url), "html.parser"
                    )
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
                except Exception as e:
                    print(f"Error when getting {ch.url}: {e}")
                    content += f"\n\n{'='*30} 本章擷取失敗 {'='*30}\n\n請至網站閱讀：{ch.url}"

        with open(f"./data/{book.code}.txt", "w", encoding="utf-8") as file:
            _s = (
                f"{book.title}\n"
                f"連結：https://czbooks.net/n/{book.code}\n"
                f"作者：{book.author.text}\n"
                f"總章數：{state.total}\n"
                f"總字數：{word_count}\n"
                f"{content}"
            )
            file.write(_s)
        book.word_count = word_count
        book.content_cache = True
        book._overview_embed_cache = None
        state.finished = True
        return content, word_count

    @classmethod
    def start(cls: "GetContent", book: "Novel") -> GetContentState:
        state = GetContentState(None, None, 0, len(book.chapter_list))
        task = asyncio.create_task(cls.get_content(cls, book, state))
        state.task = task

        return state
