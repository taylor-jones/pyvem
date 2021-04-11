"""Version command implementation"""

import sys

from pyvem._command import Command
from pyvem._config import _PROG, _VERSION
from pyvem._help import Help
from pyvem._logging import get_rich_logger


_LOGGER = get_rich_logger(__name__)
_HELP = Help(
    name='version',
    brief=f'shows the {_PROG} version',
    synopsis=f'{_PROG} -V\n'
             f'{_PROG} --version\n\n'
             f'[h2]aliases[/]: {_PROG} version',
    description=f'This command will print the current {_PROG} version to stdout.'
)


class VersionCommand(Command):
    """
    The VersionCommand class defines the "version" command. This class
    inherits from the base Command class.
    """
    def __init__(self, name, aliases=None):
        super().__init__(name, _HELP, aliases=aliases or [])


    def get_command_parser(self, *args, **kwargs):
        pass


    def run(self, *args, **kwargs):
        """
        Just print the program's version and exit.
        """
        # Update the logger to apply the log-level from the main options
        self.apply_log_level(_LOGGER)

        print(_VERSION)
        sys.exit(0)


#
# Create the VesionCommand instance
#
version_command = VersionCommand(
    name='version',
    aliases=['version', 'v'],
)
