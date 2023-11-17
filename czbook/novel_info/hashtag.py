from ..http import HyperLink


class Hashtag(HyperLink):
    """
    Hashtag class.
    """

    def __init__(self, name: str) -> None:
        """
        Hashtag init.

        :param name: Hashtag name.
        :type name: str
        """
        super().__init__(name, f"https://czbooks.net/hashtag/{name}")

    @property
    def name(self) -> str:
        """
        Get the name of the hashtag.

        :return: Hashtag name.
        :rtype: str
        """
        return self.text


class HashtagList(list[Hashtag]):
    """
    Hashtag list class.
    """

    def __init__(self, hashtag_list: list[Hashtag] = []) -> None:
        """
        Hashtag list init.

        :param hashtag_list: Hashtag list.
        :type hashtag_list: list[Hashtag]
        """
        return super().__init__(hashtag_list)

    @classmethod
    def from_list(cls: type["HashtagList"], list_: list) -> "HashtagList":
        """
        Load from list.
        list must be like: ["name1", "name2", ...]

        :params list_: List.
        :type list_: list
        :return: Hashtag list.
        :rtype: HashtagList
        """
        return cls([Hashtag(name) for name in list_])

    @classmethod
    def from_json(cls: type["HashtagList"], data: list[dict]) -> "HashtagList":
        """
        Load frm json.
        JSON must be like: [{"text": "name1", "url": "url1"}, ...]

        :params data: JSON.
        :type data: list[dict]
        :return: Hashtag list.
        :rtype: HashtagList
        """
        return cls.from_list([datum.get("text") for datum in data])
