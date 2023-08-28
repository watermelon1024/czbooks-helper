import os
import json
from typing import Any

import discord

from dotenv import load_dotenv

from utils.czbook import Czbook, load_from_json, fetch_book
from utils.timestamp import now_timestamp

load_dotenv()

BOOK_CACHE_FILE = "./data/books.json"
book_cache: dict[str, Czbook] = {}

with open(BOOK_CACHE_FILE, "r", encoding="utf-8") as file:
    data: dict[str, dict] = json.load(file)
    book_cache = {code: load_from_json(detail) for code, detail in data.items()}


def czbook_serializer(obj):
    if isinstance(obj, Czbook):
        return obj.to_dict()
    raise TypeError(f"Object of type {type(obj)} is not JSON serializable")


class Bot(discord.Bot):
    def __init__(self, description=None, *args, **options):
        super().__init__(description, *args, **options)
        self.book_cache = book_cache
        self._last_save_cache_time = 0

    def add_cache(self, book: Czbook) -> None:
        self.book_cache[book.code] = book
        now = now_timestamp()
        if now - self._last_save_cache_time > 300:
            self._last_save_cache_time = now
            self.save_cache_to_file()

    def get_cache(self, code: str) -> Czbook | None:
        return self.book_cache.get(code)

    async def get_or_fetch_book(self, code: str) -> Czbook:
        return self.get_cache(code) or await fetch_book(code)

    def save_cache_to_file(self) -> None:
        with open(BOOK_CACHE_FILE, "w", encoding="utf-8") as file:
            json.dump(
                self.book_cache, file, default=czbook_serializer, ensure_ascii=False
            )


class BaseCog(discord.Cog):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.bot: Bot = bot


bot = discord.Bot()

bot.load_extension("cogs", recursive=True)


@bot.event
async def on_ready():
    print(f"Login as {bot.user}")


if __name__ == "__main__":
    bot.run(os.getenv("TOKEN"))
