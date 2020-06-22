"""Logging helpers"""

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
    """
    Create and return a logger of a given name and logging level.

    Arguments:
        name {str} -- The name of the logger to return.

    Keyword Arguments:
        level {logging.level} -- A log level (default: {'DEBUG'})
        fmt {str} -- A logging format (default: {'%(message)s'})
        datefmt {str} -- A logging date format (default: {'[%X] '})
        console {rich.console} -- An optional rich console to use for the
        logging output (default: {None})

    Returns:
        logging.logger
    """
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
