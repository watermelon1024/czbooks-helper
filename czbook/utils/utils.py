import re

from ..const import RE_BOOK_CODE
from ..http import HyperLink


def hyper_link_list_to_str(
    hyper_links: list[HyperLink],
    max_len: int = 1024,
    comma: str = ", ",
    ellipsis: str = "...",
) -> str:
    max_len -= len(f"{ellipsis}{comma}")
    text_len = len(
        text_end := comma.join(str(hyper_link) for hyper_link in hyper_links[-8:])
    )
    text = ""
    for hyper_link in hyper_links[:-8]:
        text_len += len(text_ := f"{str(hyper_link)}{comma}")
        if text_len >= max_len:
            text += f"{ellipsis}{comma}"
            break
        text += text_

    return text + text_end


def get_code(s: str) -> str | None:
    if match := re.search(RE_BOOK_CODE, s):
        return match.group(2)
    return None
