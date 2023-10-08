import aiohttp


class CommentField:
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


class Comment(list):
    def __init__(self, novel_code: str, comment_list: list[CommentField] = []) -> None:
        self.novel_code = novel_code
        super().__init__(comment_list)

    async def update(self) -> None:
        self: list[CommentField] = []
        page = 1
        async with aiohttp.ClientSession() as session:
            while True:
                async with session.get(
                    f"https://api.czbooks.net/web/comment/list?novelId={self.novel_code}&page={page}&cleanCache=true"  # noqa
                ) as response:
                    data = await response.json()
                    items = data["data"]["items"]
                self.extend(
                    [
                        CommentField(
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
