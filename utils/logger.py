import logging

from logging import StreamHandler, FileHandler, LogRecord, Formatter


class _CustomStreamHandler(StreamHandler):
    def __init__(self, formatter: Formatter = None, file_handler: FileHandler = None):
        super().__init__()
        self.file_handler = file_handler
        self.formatter = formatter

    def emit(self, record: LogRecord) -> None:
        try:
            super().emit(record)
            if self.file_handler is not None:
                self.file_handler.emit(record)
        except Exception:
            self.handleError(record)


def new_logger(
    name: str = None,
    level: str = "INFO",
    log_file_name: str = None,
    terminal_formatter: str = None,
    file_formatter: str = None,
) -> logging.Logger:
    """
    Create a new logger.

    :param name: logger name.
    :type name: str.
    :param level: logger level.
    :type level: str.
    :param log_file_name: log file name.
    :type log_file_name: str.
    :param terminal_formatter: terminal formatter.
    :type terminal_formatter: str.
    :param file_formatter: file formatter.
    :type file_formatter: str.

    :return: logger.
    :rtype: logging.Logger
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # handlers
    if log_file_name is not None:
        file_handler = FileHandler(log_file_name)
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(
            Formatter(file_formatter or "[%(asctime)s] [%(name)s/%(levelname)s]: %(message)s")
        )
    else:
        file_handler = None

    stream_handler = _CustomStreamHandler(
        Formatter(
            terminal_formatter or "[%(asctime)s] [%(name)s/%(levelname)s]: %(message)s", "%H:%M:%S"
        ),
        file_handler,
    )
    stream_handler.setLevel(logger.level)
    logger.addHandler(stream_handler)

    return logger
