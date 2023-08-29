from datetime import datetime


def now_timestamp() -> float:
    return datetime.now().timestamp()


def time_diff(start_timestamp: float, end_timestamp: float = None) -> float:
    return (end_timestamp or now_timestamp()) - start_timestamp
