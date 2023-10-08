from ..http import HyperLink


class Category(HyperLink):
    def __init__(self, text: str, url: str) -> None:
        super().__init__(text, url)
