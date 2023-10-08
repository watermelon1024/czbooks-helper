from ..http import HyperLink


class Author(HyperLink):
    def __init__(self, name: str) -> None:
        self.name = name
        super().__init__(name, f"https://czbooks.net/a/{name}")
