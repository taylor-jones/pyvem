"""
Exceptions used throughout the package
"""

from __future__ import absolute_import
from itertools import chain, groupby, repeat
import textwrap

def raise_argument_error(parser, argument, message):
    # type: (ArgParser, Argument, str) -> None
    """
    Raise an argument parsing error using parser.error().

    Args:
      parser: an ArgParser instance.
      argument: an Argument instance.
      message: the error text.
    """
    message = '{} error: {}'.format(argument, message)
    message = textwrap.fill(' '.join(message.split()))
    parser.error(message)



class VemError(Exception):
    """
    Base vem exception
    """

class CommandError(VemError):
    """
    Raised when there is an error in the command-line arguments.
    """

class ConnectionError(VemError):
    """
    Raised when there is an issue with the remote server connection.
    """

class DownloadError(VemError):
    """
    Raised when there is an issue while downloading an editor or extension.
    """

class LatestVersionAlreadyInstalled(VemError):
    """
    Raised when the most up-to-date version of an editor or package is
    already installed.
    """

class InstallationError(VemError):
    """
    Raised when there's a general issue while installing an editor or extension.
    """

