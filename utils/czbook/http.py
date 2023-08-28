import asyncio

import aiohttp

from bs4 import BeautifulSoup

from .const import TIMEOUT, CRAWLER_HEADER
from .error import BookNotFoundError


class HyperLink:
    def __init__(self, text: str, url: str) -> None:
        self.text = text
        self.url = url

    def __str__(self) -> str:
        return f"[{self.text}]({self.url})"

    def to_dict(self) -> dict:
        return {
            "text": self.text,
            "url": self.url,
        }


async def get(url: str) -> str:
    async with aiohttp.request("GET", url) as response:
        return await response.text()


async def get_html(url: str) -> BeautifulSoup:
    async with aiohttp.request("GET", url) as response:
        if response.status == 404:
            raise BookNotFoundError()
        return BeautifulSoup(await response.text(), "html.parser")


async def fetch_url(session: aiohttp.ClientSession, url: str) -> str:
    async with session.get(url, timeout=TIMEOUT, headers=CRAWLER_HEADER) as response:
        if response.status == 429:
            await asyncio.sleep(1)
            return await fetch_url(session, url)
        return await response.text()
