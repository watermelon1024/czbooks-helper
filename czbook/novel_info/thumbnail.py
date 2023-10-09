import asyncio

from .. import color


class Thumbnail:
    def __init__(self, url: str) -> None:
        self.url = url
        self._theme_color: list[int] = None

    @property
    def theme_color(self) -> list[int]:
        if self._theme_color is None:
            self._theme_color = asyncio.run(_get_theme_colors())
        return self._theme_color

    def to_dict(self) -> dict:
        return {"url": self.url, "theme_color": self.theme_color}

    @classmethod
    def from_json(cls: "Thumbnail", data: dict) -> "Thumbnail":
        """
        Load from json format.
        JSON must be like {"url": ..., "theme_color": ...}
        """
        thumbnail = Thumbnail(data.get("url"))
        thumbnail._theme_color = data.get("theme_color")
        return thumbnail


async def _get_theme_colors(url: str) -> list[int]:
    return color.extract_theme_light_colors_hex(await color.get_img_from_url(url))
