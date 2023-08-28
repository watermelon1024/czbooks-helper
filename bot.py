import os
import json
from typing import Any

import discord

from dotenv import load_dotenv

from utils.czbook import Czbook, load_from_json

load_dotenv()

book_cache: dict[str, Czbook] = {}

with open("./data/books.json", "r", encoding="utf-8") as file:
    data: dict[str, dict] = json.load(file)
    book_cache = {code: load_from_json(detail) for code, detail in data.items()}


class Bot(discord.Bot):
    def __init__(self, description=None, *args, **options):
        super().__init__(description, *args, **options)
        self.book_cache = book_cache


class BaseCog(discord.Cog):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.bot = bot


bot = discord.Bot()

bot.load_extension("cogs", recursive=True)


@bot.event
async def on_ready():
    print(f"Login as {bot.user}")


if __name__ == "__main__":
    bot.run(os.getenv("TOKEN"))
