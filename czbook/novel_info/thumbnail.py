import asyncio

from .. import color


class Thumbnail:
    def __init__(self, url: str) -> None:
        self.url = url
        self._theme_colors = None

    @property
    def theme_color(self) -> list[int]:
        if self._theme_colors is None:
            self._theme_colors = asyncio.run(_get_theme_colors())
        return self._theme_colors


async def _get_theme_colors(url: str) -> list[int]:
    return color.extract_theme_light_colors_hex(await color.get_img_from_url(url))
