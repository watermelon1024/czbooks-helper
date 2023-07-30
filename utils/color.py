import io

import aiohttp
import numpy as np

from PIL import Image
from sklearn.cluster import KMeans


def rgb_to_int_hex(rgb):
    r, g, b, *_ = rgb
    return (r << 16) + (g << 8) + b


def extract_theme_colors(
    image: Image.Image,
    num_colors=10,
) -> list[tuple[int, int, int, int]]:
    image_array = np.array(image.convert("RGBA"))

    # 3d -> 2d array
    flattened_image_array = image_array.reshape((-1, 4))

    # 使用K-means算法从图像中提取主题颜色
    k_means = KMeans(n_clusters=num_colors, n_init="auto", algorithm="lloyd")
    k_means.fit(flattened_image_array)

    # 获取聚类中心作为主题颜色
    return k_means.cluster_centers_.astype(int).tolist()


def get_main_colors(
    image: Image.Image,
    num_colors=10,
) -> list[tuple[int, int, int, int]]:
    base_colors = extract_theme_colors(image, num_colors)
    sorted_colors = sorted(
        list(
            filter(
                lambda x: x[4] > 400 and x[4] < 620,
                map(lambda x: (*x, sum(x)), base_colors),
            )
        )
    )
    return sorted_colors[-4:] if sorted_colors else base_colors


async def get_img_from_url(url: str) -> Image.Image:
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resopnse:
            return Image.open(io.BytesIO(await resopnse.read()))
