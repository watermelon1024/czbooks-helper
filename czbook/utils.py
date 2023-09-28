from .http import HyperLink

# flake8: noqa: F401
from .timestamp import now_timestamp, is_out_of_date


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
        text_len += len(text_ := f"{hyper_link}{comma}")
        if text_len > max_len:
            text += f"{ellipsis}{comma}"
            break
        text += text_

    return text + text_end
