"""Logging helpers"""

import logging

import rich.console
import rich.logging

from pyvem._config import rich_theme


def get_rich_logger(
    name: str,
    level: str = 'DEBUG',
    fmt: str = '%(message)s',
    datefmt: str = '[%X] ',
    console: rich.console.Console = rich.console.Console(theme=rich_theme),
) -> logging.Logger:
    """
    Create and return a logger of a given name and logging level.

    Arguments:
        name -- The name of the logger to return.

    Keyword Arguments:
        level {logging.level} -- A log level (default: {'DEBUG'})
        fmt {str} -- A logging format (default: {'%(message)s'})
        datefmt {str} -- A logging date format (default: {'[%X] '})
        console {rich.console} -- An optional rich console to use for the
        logging output (default: {None})

    Returns:
        logging.logger
    """
    log_level = logging.getLevelName(level)
    if log_level == f'Level {level}':
        log_level = logging.DEBUG

    formatter = logging.Formatter(fmt=fmt, datefmt=datefmt)
    handler = rich.logging.RichHandler(console=console)
    handler.setFormatter(formatter)

    logger = logging.getLogger(name)
    logger.handlers = [handler]
    logger.setLevel(log_level)

    return logger
