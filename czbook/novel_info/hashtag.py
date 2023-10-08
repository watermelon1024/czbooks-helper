from ..http import HyperLink


class Hashtag(HyperLink):
    def __init__(self, name: str) -> None:
        super().__init__(name, f"https://czbooks.net/hashtag/{name}")


class HashtagList(list[Hashtag]):
    def __init__(self, hashtag_list: list[Hashtag]) -> None:
        return super().__init__(hashtag_list)
