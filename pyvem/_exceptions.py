"""
Exceptions used throughout the package
"""


class VemError(Exception):
    """
    Base vem exception
    """


class CommandError(VemError):
    """
    Raised when there is an error in the command-line arguments.
    """


class TunnelError(VemError):
    """
    Raised when there is an issue with the remote server connection.
    """


class DownloadError(TunnelError):
    """
    Raised when there is an issue while downloading an editor or extension.
    """


class InstallationError(VemError):
    """
    Raised when there's a general issue while installing an editor or extension.
    """


class LatestVersionAlreadyInstalled(InstallationError):
    """
    Raised when the most up-to-date version of an editor or package is
    already installed.
    """
