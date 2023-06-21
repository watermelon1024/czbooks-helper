import os

import discord

from dotenv import load_dotenv

# 載入.env檔案中的環境變數
load_dotenv()


class BaseCog(discord.Cog):
    def __init__(self, bot: discord.Bot) -> None:
        self.bot = bot


bot = discord.Bot()

bot.load_extension("cogs", recursive=True)


@bot.event
async def on_ready():
    print(f"We have logged in as {bot.user}")


if __name__ == "__main__":
    bot.run(os.getenv("TOKEN"))
