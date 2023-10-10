import os
import json
from typing import Any

import discord

from dotenv import load_dotenv

import czbook
from czbook.utils import is_out_of_date

from utils.czbook import Novel

load_dotenv()

NOVEL_CACHE_FILE = "./data/novel.json"
novel_cache: dict[str, Novel] = {}

try:
    with open(NOVEL_CACHE_FILE, "r", encoding="utf-8") as file:
        data: dict[str, dict] = json.load(file)
        novel_cache = {id: Novel.load_from_json(detail) for id, detail in data.items()}
except Exception as e:
    print(f"error load db file, using empty cache.\n{e}")
    novel_cache = {}


def novel_serializer(obj):
    if isinstance(obj, Novel):
        return obj.to_dict()
    raise TypeError(f"Object of type {type(obj)} is not JSON serializable")


class Bot(discord.Bot):
    def __init__(self, description=None, *args, **options):
        super().__init__(description, *args, **options)
        self.novel_cache: dict[str, Novel] = novel_cache
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

    # czbook function #
    def add_cache(self, novel: Novel) -> None:
        self.novel_cache[novel.id] = novel
        if now := is_out_of_date(self._last_save_cache_time, 60):
            self._last_save_cache_time = now
            self.save_cache_to_file()

    def get_cache(self, id: str) -> Novel | None:
        return self.novel_cache.get(id)

    async def fetch_novel(self, id: str, first: bool = True) -> Novel:
        return Novel.from_original_novel(await czbook.fetch_novel(id, first))

    async def get_or_fetch_novel(
        self, id: str, update_when_out_of_date: bool = True
    ) -> Novel:
        if novel := self.get_cache(id):
            if update_when_out_of_date and (
                now := is_out_of_date(novel.last_fetch_time, 600)
            ):
                novel.last_fetch_time = now
                updated_novel = await self.fetch_novel(novel.id, False)
                updated_novel.info.thumbnail = novel.info.thumbnail
                self.add_cache(updated_novel)
        self.add_cache(novel := await self.fetch_novel(id))
        return novel

    def save_cache_to_file(self) -> None:
        with open(NOVEL_CACHE_FILE, "w", encoding="utf-8") as file:
            json.dump(
                self.novel_cache, file, default=novel_serializer, ensure_ascii=False
            )


class BaseCog(discord.Cog):
    def __init__(self, bot: Bot, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.bot: Bot = bot


bot = Bot()
bot.load_extension("cogs", recursive=True)


if __name__ == "__main__":
    bot.run(os.getenv("TOKEN"))
