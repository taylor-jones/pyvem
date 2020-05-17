import logging

from rich.console import Console
from rich.logging import RichHandler
from pyvsc._config import rich_theme

_console = Console(theme=rich_theme)


def get_rich_logger(
    name,
    level='DEBUG',
    fmt='%(message)s',
    datefmt='[%X] ',
    console=None,
):
    try:
        log_level = logging.getLevelName(level)
    except Exception as e:
        log_level = logging.DEBUG

    formatter = logging.Formatter(fmt=fmt, datefmt=datefmt)
    handler = RichHandler(console=console or _console)
    handler.setFormatter(formatter)

    logger = logging.getLogger(name)
    logger.handlers = [handler]
    logger.setLevel(log_level)

    return logger
