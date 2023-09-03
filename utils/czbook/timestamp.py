import time


def now_timestamp() -> float:
    return time.time()


def time_diff(start_timestamp: float, end_timestamp: float = None) -> float:
    return (end_timestamp or now_timestamp()) - start_timestamp
