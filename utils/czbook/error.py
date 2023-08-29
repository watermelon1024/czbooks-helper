class BookNotFoundError(Exception):
    """
    Book not found.
    """

    def __init__(self, *args: object) -> None:
        super().__init__(*args)


class TooManyRequestsError(Exception):
    """
    429 Too many requests.
    """

    def __init__(self, *args: object) -> None:
        super().__init__(*args)
