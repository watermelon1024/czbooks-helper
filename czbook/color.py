import io

import aiohttp
import numpy as np

from PIL import Image
from sklearn.cluster import KMeans


def rgb_to_hex(rgb: tuple[int, int, int]) -> int:
    r, g, b, *_ = rgb
    return (r << 16) + (g << 8) + b


def brightness(rgba: tuple[int, int, int, int]) -> float:
    r, g, b, a, *_ = rgba
    return (0.299 * r + 0.587 * g + 0.114 * b) * a / 65025


def extract_theme_colors(
    image: Image.Image,
    num_colors=10,
) -> list[tuple[int, int, int, int]]:
    image_array = np.array(image.convert("RGBA"))

    k_means = KMeans(n_clusters=num_colors, n_init="auto")
    k_means.fit(image_array.reshape((-1, 4)))

    return k_means.cluster_centers_.astype(int).tolist()


def extract_theme_light_colors(
    image: Image.Image,
    num_colors=10,
) -> list[tuple[int, int, int, int]]:
    base_colors = extract_theme_colors(image, num_colors)
    light_colors = sorted(
        filter(
            lambda x: x[4] < 0.9 and x[4] > 0.2,
            map(lambda x: (*x, brightness(x)), base_colors),
        ),
        key=lambda x: x[4],
        reverse=True,
    )
    return light_colors or base_colors


def extract_theme_light_colors_hex(
    image: Image.Image,
    num_colors=10,
) -> list[int]:
    return list(map(rgb_to_hex, extract_theme_light_colors(image, num_colors)))


async def get_img_from_url(url: str) -> Image.Image:
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resopnse:
            return Image.open(io.BytesIO(await resopnse.read()))
