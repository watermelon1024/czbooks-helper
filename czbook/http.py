import asyncio

from aiohttp import ClientSession, ClientResponse

from bs4 import BeautifulSoup

from .const import DEFAULT_TIMEOUT, CRAWLER_HEADER
from .error import NotFoundError, TooManyRequestsError


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


async def _fetch_url(
    session: ClientSession,
    url: str,
    max_retry: int,
    now_retry: int,
) -> ClientResponse:
    try:
        async with session.get(
            url, headers=CRAWLER_HEADER, timeout=DEFAULT_TIMEOUT
        ) as response:
            if response.status == 404:
                raise NotFoundError("404 Not found")
            if response.status == 429:
                raise TooManyRequestsError("429 Too many requests")
            return response
    except NotFoundError as e:
        raise e
    except Exception as e:
        if now_retry < max_retry:
            await asyncio.sleep(now_retry)
            return await _fetch_url(session, url, max_retry, now_retry + 1)
        raise e


async def fetch_url(
    session: ClientSession,
    url: str,
    max_retry: int = 3,
) -> ClientResponse:
    return await _fetch_url(session, url, max_retry, 0)


async def fetch_as_text(url: str, session: ClientSession = None) -> str:
    if session:
        return await (await fetch_url(session, url)).text()
    async with ClientSession() as session:
        return await (await fetch_url(session, url)).text()


async def fetch_as_json(url: str, session: ClientSession = None) -> dict:
    if session:
        return await (await fetch_url(session, url)).json()
    async with ClientSession() as session:
        return await (await fetch_url(session, url)).json()


async def fetch_as_html(url: str, session: ClientSession = None) -> BeautifulSoup:
    return BeautifulSoup(await fetch_as_text(url, session), "html.parser")
