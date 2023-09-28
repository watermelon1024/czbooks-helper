import aiohttp


class Comment:
    def __init__(
        self,
        id: str,
        author: str,
        message: str,
        timestsmp: int,
        reply_to: str = None,
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
                    comment["id"],
                    comment["nickname"],
                    comment["message"],
                    comment["date"],
                    comment["replyId"] or None,
                )
                for comment in items
            ]

            if not (page := data.get("next")):
                break

    return comments
