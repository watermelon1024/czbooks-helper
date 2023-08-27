import aiohttp

from discord import Embed

from .czbook import Czbook


class Comment:
    def __init__(
        self,
        id: int,
        author: str,
        message: str,
        timestsmp: int,
        reply_to: int = 0,
    ) -> None:
        self.id = id
        self.author = author
        self.message = message
        self.timestamp = timestsmp
        self.reply_to = reply_to

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "author": self.author,
            "message": self.message,
            "reply_to": self.reply_to,
            "date": self.timestamp,
        }


def comments_embed(book: Czbook) -> Embed:
    embed = Embed(
        title=f"{book.title}評論列表",
        url=f"https://czbooks.net/n/{book.code}",
        color=book.get_theme_color(),
    )
    for comment in book.comments:
        embed.add_field(
            name=comment.author,
            value=f"```{comment.message}```",
            inline=False,
        )
        if len(embed) > 6000:
            embed.remove_field(-1)
            break

    return embed


async def update_comments(code: str) -> list[Comment]:
    comments: list[Comment] = []
    page = 1
    async with aiohttp.ClientSession() as session:
        while True:
            async with session.get(
                f"https://api.czbooks.net/web/comment/list?novelId={code}&page={page}&cleanCache=true"  # noqa
            ) as response:
                data = await response.json()
                items = data["data"]["items"]
            comments += [
                Comment(
                    comment["nickname"],
                    comment["message"],
                    comment["date"],
                )
                for comment in items
            ]

            if not (page := data.get("next")):
                break

    return comments
