from .. import color


class Thumbnail:
    """
    Thumbnail class.
    """

    def __init__(self, url: str) -> None:
        """
        Thumbnail class.

        :params url: the url of the thumbnail.
        :type url: str.
        """
        self._url = url
        self._theme_color: list[int] = None

    @property
    def url(self) -> str:
        """
        The url of the thumbnail.

        :type url: str.
        :rtype: str.
        """
        return self._url

    @property
    def theme_color(self) -> list[int]:
        """
        The theme color of the thumbnail.

        :raises RuntimeError: Raised when the theme color hasn't been gotten.

        :type theme_color: list[int].
        :rtype: list[int].
        """
        if self._theme_color is None:
            raise RuntimeError(
                "Theme color hasn't been gotten, please run 'get_theme_color' first"
            )
        return self._theme_color

    async def get_theme_colors(self) -> list[int]:
        """
        Get the theme color of the thumbnail.

        :type theme_color: list[int].
        :rtype: list[int].
        """
        self._theme_color = color.extract_theme_light_colors_hex(
            await color.get_img_from_url(self.url)
        )
        return self._theme_color

    def to_dict(self) -> dict:
        """
        Convert to dict.
        Dict be like: {"url": ..., "theme_color": ...}

        :returns: The dict of the thumbnail data.
        :rtype: dict.
        """
        return {"url": self.url, "theme_color": self.theme_color}

    @classmethod
    def from_json(cls: type["Thumbnail"], data: dict) -> "Thumbnail":
        """
        Load from json format.
        JSON must be like: {"url": ..., "theme_color": ...}

        :param data: The data of the thumbnail.
        :type data: dict.
        :returns: The thumbnail.
        :rtype: Thumbnail.
        """
        thumbnail = cls(data.get("url"))
        thumbnail._theme_color = data.get("theme_color")
        return thumbnail
