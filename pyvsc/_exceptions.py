"""
Exceptions used throughout the package
"""

from __future__ import absolute_import
from itertools import chain, groupby, repeat


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

