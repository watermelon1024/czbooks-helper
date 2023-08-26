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
