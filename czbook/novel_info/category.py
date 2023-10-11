from ..http import HyperLink


class Category(HyperLink):
    def __init__(self, name: str, url: str) -> None:
        super().__init__(name, url)

    @property
    def name(self) -> str:
        return self.text
