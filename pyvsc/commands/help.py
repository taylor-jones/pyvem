"""Help command implementation"""

import sys

from pyvsc._command import Command
from pyvsc._config import _PROG
from pyvsc._help import Help
from pyvsc._logging import get_rich_logger

# Import each of the other commands so their 'help' methods can be invoked from here.
# This is the only command that needs to import all of the other commands.
# pylint: disable=unused-import
# flake8: noqa:401
from pyvsc.commands.config import config_command
from pyvsc.commands.info import info_command
from pyvsc.commands.install import install_command
from pyvsc.commands.list import list_command
from pyvsc.commands.outdated import outdated_command
from pyvsc.commands.search import search_command
from pyvsc.commands.update import update_command
from pyvsc.commands.version import version_command


_LOGGER = get_rich_logger(__name__)
_HELP = Help(
    name='help',
    brief='Show help documentation',
    synopsis=f'{_PROG} help <command>',
    description=f'This command will show help documentation for other {_PROG} commands. '
                'If the provided [keyword]<command>[/] is not valid or no help documentation '
                'exists, the help command will display:'
                '\n\t[example]No help documentation is available for the command '
                '[keyword]<command>[/][/]'
                '\n\n'
                'If no command (or no valid command) is passed to the help command, then '
                f'{_PROG}\'s default help output is printed to stdout.'
)


class HelpCommand(Command):
    """
    Inherits from the base Command class and overrides the `run` method
    to implement the Help functionality.
    """
    def __init__(self, name, aliases=None):
        super().__init__(name, _HELP, aliases=aliases or [])


    def get_command_parser(self, *args, **kwargs):
        """
        No custom command parser implementation is needed for the Help command.
        """
        return None


    def run(self, *args, **kwargs):
        """
        Implements the `help` commands functionality.
        """
        # Update the logger to apply the log-level from the main options
        self.apply_log_level(_LOGGER)

        # If the `help` command didn't get any arguments, just show the
        # default vem help screen and then exit.
        args = Command.main_options.args
        if not args:
            Command.main_parser.print_help()
            sys.exit(1)

        # Otherwise, parse the command name.
        command_name = args[0]

        try:
            # determine which command the user asked for help about. Then
            # invoke the help for that command.
            command = getattr(sys.modules[__name__], f'{command_name}_command')
            command.show_help()
        except AttributeError:
            _LOGGER.error('No help documentation is available for command: "%s"', command_name)


#
# Create the HelpCommand instance
#
help_command = HelpCommand(name='help', aliases=['help'])
