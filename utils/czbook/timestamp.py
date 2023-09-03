import time


def now_timestamp() -> float:
    return time.time()


def time_diff(start_timestamp: float, end_timestamp: float = None) -> float:
    return (end_timestamp or now_timestamp()) - start_timestamp


def is_out_of_date(timestamp: float, time_range: float) -> float | None:
    """
    Return then current timestamp if the timestamp given is out of range, else None.
    """

    if (now := now_timestamp()) - timestamp > time_range:
        return now
    return None
