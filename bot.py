import os
from typing import Any
import logging

import discord

from dotenv import load_dotenv

import czbook
from czbook.utils import is_out_of_date

import db
from utils.czbook import (
    Novel,
    hashtag_list_to_str,
    hashtag_str_to_list,
    chapter_list_to_str,
    chapter_str_to_list,
)
from utils.logger import new_logger

load_dotenv()


class DataBase(db.DataBase):
    cache: dict[str, Novel] = {}

    # czbook function #
    def add_or_update_cache(self, novel: Novel) -> None:
        # cache
        self.cache[novel.id] = novel

        # database
        category, _ = self.CategoryModule.get_or_create(
            name=novel.category.name, url=novel.category.url
        )
        self.NovelModule.insert(
            novel_id=novel.id,
            titel=novel.title,
            description=novel.description,
            thumbnail=novel.thumbnail.to_dict() if novel.thumbnail else None,
            author=novel.author.name,
            state=novel.state,
            last_update=novel.last_update,
            views=novel.views,
            category=category,
            hashtags=hashtag_list_to_str(novel.hashtags),
            chapter_list=chapter_list_to_str(novel.chapter_list),
            word_count=novel.word_count,
        ).on_conflict("replace").execute()

    def get_cache(self, id: str) -> Novel | None:
        if novel := self.cache.get(id):
            return novel
        if data := self.NovelModule.get_or_none(self.NovelModule.novel_id == id):
            return self._db_data_to_novel_class(data)

        return None

    async def fetch_novel(self, id: str, first: bool = True) -> Novel:
        return Novel.from_original_novel(await czbook.fetch_novel(id, first))

    async def get_or_fetch_novel(self, id: str, update_when_out_of_date: bool = True) -> Novel:
        if novel := self.get_cache(id):
            if update_when_out_of_date and is_out_of_date(novel.last_fetch_time, 3600):
                await novel.update()
                self.add_or_update_cache(novel)
            return novel
        self.add_or_update_cache(novel := await self.fetch_novel(id))
        return novel

    def _db_data_to_novel_class(self, data: db.NovelType) -> Novel:
        return Novel(
            id=data.novel_id,
            info=czbook.NovelInfo(
                id=data.novel_id,
                title=data.titel,
                description=data.description,
                thumbnail=(czbook.Thumbnail.from_json(data.thumbnail) if data.thumbnail else None),
                author=czbook.Author(data.author),
                state=data.state,
                last_update=data.last_update,
                views=data.views,
                category=czbook.Category(data.category.name, data.category.url),
                hashtags=hashtag_str_to_list(data.hashtags),
            ),
            chapter_list=chapter_str_to_list(data.chapter_list),
            comment=czbook.CommentList(data.novel_id),
            word_count=data.word_count,
        )


class Bot(discord.Bot):
    def __init__(self, description=None, *args, **options):
        super().__init__(description, *args, **options)
        self.get_content_msg: set = set()
        self.db = DataBase()
        self._logger = new_logger("bot", level="DEBUG")

        for k, v in self.load_extension("cogs", recursive=True, store=True).items():
            if v is True:
                self.logger.debug(f"Loaded extension {k}")
            else:
                self.logger.error(f"Failed to load extension {k} with exception: {v}")

    @property
    def logger(self) -> logging.Logger:
        return self._logger

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
        print("Closing the bot...")
        await super().close()
        print("Bot is offline.")

    def run(self, token: str) -> None:
        """
        Starts the bot.
        """
        print("Starting the bot...")
        super().run(token)


class BaseCog(discord.Cog):
    def __init__(self, bot: Bot, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.bot: Bot = bot

    @property
    def logger(self) -> logging.Logger:
        return self.bot.logger


if __name__ == "__main__":
    bot = Bot()
    bot.run(os.getenv("TOKEN"))
