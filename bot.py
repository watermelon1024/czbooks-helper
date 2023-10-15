import os
from typing import Any

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

load_dotenv()

novel_cache: dict[str, Novel] = {}


class DataBase(db.DataBase):
    cache = novel_cache

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
            hashtags_str=hashtag_list_to_str(novel.hashtags),
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

    async def get_or_fetch_novel(
        self, id: str, update_when_out_of_date: bool = True
    ) -> Novel:
        if novel := self.get_cache(id):
            if update_when_out_of_date and (
                now := is_out_of_date(novel.last_fetch_time, 3600)
            ):
                novel.last_fetch_time = now
                updated_novel = await self.fetch_novel(novel.id, False)
                updated_novel.info.thumbnail = novel.info.thumbnail
                updated_novel.word_count = novel.word_count
                updated_novel.content_cache = novel.content_cache
                self.add_or_update_cache(updated_novel)
                return updated_novel
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
                thumbnail=(
                    czbook.Thumbnail.from_json(data.thumbnail)
                    if data.thumbnail
                    else None
                ),
                author=czbook.Author(data.author),
                state=data.state,
                last_update=data.last_update,
                views=data.views,
                category=czbook.Category(data.category.name, data.category.url),
                hashtags=hashtag_str_to_list(data.hashtags),
            ),
            content_cache=bool(data.word_count),
            word_count=data.word_count or 0,
            chapter_list=chapter_str_to_list(data.chapter_list),
            comment=czbook.CommentList(data.novel_id),
        )


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


class BaseCog(discord.Cog):
    def __init__(self, bot: Bot, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.bot: Bot = bot


bot = Bot()
bot.load_extension("cogs", recursive=True)


if __name__ == "__main__":
    bot.run(os.getenv("TOKEN"))
