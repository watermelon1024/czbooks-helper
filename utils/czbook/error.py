class BookNotFoundError(Exception):
    """
    Book not found.
    """

    def __init__(self, *args: object) -> None:
        super().__init__(*args)
