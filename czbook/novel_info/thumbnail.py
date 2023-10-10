from .. import color


class Thumbnail:
    def __init__(self, url: str) -> None:
        self.url = url
        self._theme_color: list[int] = None

    @property
    def theme_color(self) -> list[int]:
        if self._theme_color is None:
            raise RuntimeError(
                "Theme color hasn't been gotten, please run 'get_theme_color' first"
            )
        return self._theme_color

    async def get_theme_colors(self) -> None:
        self._theme_color = color.extract_theme_light_colors_hex(
            await color.get_img_from_url(self.url)
        )

    def to_dict(self) -> dict:
        return {"url": self.url, "theme_color": self.theme_color}

    @classmethod
    def from_json(cls: type["Thumbnail"], data: dict) -> "Thumbnail":
        """
        Load from json format.
        JSON must be like {"url": ..., "theme_color": ...}
        """
        thumbnail = cls(data.get("url"))
        thumbnail._theme_color = data.get("theme_color")
        return thumbnail
