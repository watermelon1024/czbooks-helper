from ..http import HyperLink


class Author(HyperLink):
    def __init__(self, name: str) -> None:
        super().__init__(name, f"https://czbooks.net/a/{name}")

    @property
    def name(self) -> str:
        return self.text
