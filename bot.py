import os
import json
from typing import Any

import discord

from dotenv import load_dotenv

from utils.czbook import Czbook, load_from_json, fetch_book
from utils.timestamp import is_out_of_date

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
        self.get_content_msg: set = set()

    # bot event
    async def on_ready(self) -> None:
        """
        The event that is triggered when the bot is ready.
        """
        print(f"Login as {self.user} ({self.user.id}).")

    async def close(self) -> None:
        """
        Closes the bot.
        """
        print("Saving file...")
        self.save_cache_to_file()
        print("Closing the bot...")
        await super().close()
        print("Bot is offline.")

    def run(self, token: str) -> None:
        """
        Starts the bot.
        """
        print("Starting the bot...")
        super().run(token)

    # czbook func
    def add_cache(self, book: Czbook) -> None:
        self.book_cache[book.code] = book
        if now := is_out_of_date(self._last_save_cache_time, 60):
            self._last_save_cache_time = now
            self.save_cache_to_file()

    def get_cache(self, code: str) -> Czbook | None:
        return self.book_cache.get(code)

    async def get_or_fetch_book(
        self, code: str, update_when_out_of_date: bool = True
    ) -> Czbook:
        if book := self.get_cache(code):
            if update_when_out_of_date and (
                now := is_out_of_date(book.last_fetch_time, 600)
            ):
                book.last_fetch_time = now
                book_updated = await fetch_book(book.code, False)
                book_updated.thumbnail = book.thumbnail
                book_updated.theme_colors = book.theme_colors
                self.add_cache(book_updated)
            return book
        self.add_cache(book := await fetch_book(code))
        return book

    def save_cache_to_file(self) -> None:
        with open(BOOK_CACHE_FILE, "w", encoding="utf-8") as file:
            json.dump(
                self.book_cache, file, default=czbook_serializer, ensure_ascii=False
            )


class BaseCog(discord.Cog):
    def __init__(self, bot: Bot, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.bot: Bot = bot


bot = Bot()
bot.load_extension("cogs", recursive=True)


if __name__ == "__main__":
    bot.run(os.getenv("TOKEN"))
