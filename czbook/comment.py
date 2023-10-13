import aiohttp

from .http import fetch_as_json


class Comment:
    def __init__(
        self,
        comment_id: str,
        author: str,
        message: str,
        timestsmp: int,
        reply_to: str = None,
    ) -> None:
        self.comment_id = comment_id
        self.author = author
        self.message = message
        self.timestamp = timestsmp
        self.reply_to = reply_to

    def to_dict(self) -> dict:
        return {
            "id": self.comment_id,
            "author": self.author,
            "message": self.message,
            "reply_to": self.reply_to,
            "date": self.timestamp,
        }


class CommentList(list[Comment]):
    def __init__(self, novel_id: str, comment_list: list[Comment] = []) -> None:
        self.novel_id = novel_id
        super().__init__(comment_list)

    async def update(self) -> None:
        self.clear()
        page = 1
        async with aiohttp.ClientSession() as session:
            while True:
                data = await fetch_as_json(
                    f"https://api.czbooks.net/web/comment/list?novelId={self.novel_id}&page={page}&cleanCache=true",  # noqa
                    session,
                )
                items = data["data"]["items"]
                self.extend(
                    [
                        Comment(
                            comment["id"],
                            comment["nickname"],
                            comment["message"],
                            comment["date"],
                            comment["replyId"] or None,
                        )
                        for comment in items
                    ]
                )

                if not (page := data.get("next")):
                    break
