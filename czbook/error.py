class NotFoundError(Exception):
    """
    404 Not found.
    """

    def __init__(self, *args: object) -> None:
        super().__init__(*args)


class TooManyRequestsError(Exception):
    """
    429 Too many requests.
    """

    def __init__(self, *args: object) -> None:
        super().__init__(*args)


class ChapterNoContentError(Exception):
    """
    Chapter hasn't had content.
    """

    def __init__(self, *args: object) -> None:
        super().__init__(*args)
