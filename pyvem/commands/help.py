"""Help command implementation"""

import sys

from pyvem._command import Command
from pyvem._config import _PROG
from pyvem._help import Help
from pyvem._logging import get_rich_logger

# Import each of the other commands so their 'help' methods can be invoked
# from here. NOTE: Don't import the `commands_command` module, because that
# would introduce a circular dependency

# pylint: disable=unused-import
# flake8: noqa:401
from pyvem.commands.config import config_command
from pyvem.commands.info import info_command
from pyvem.commands.install import install_command
from pyvem.commands.list import list_command
from pyvem.commands.outdated import outdated_command
from pyvem.commands.search import search_command
from pyvem.commands.update import update_command
from pyvem.commands.version import version_command


_LOGGER = get_rich_logger(__name__)
_HELP = Help(
    name='help',
    brief='Show help documentation',
    synopsis=f'{_PROG} help <command>',
    description= \
        f'This command will show help documentation for other {_PROG} '
        f'commands. If the provided [keyword]<command>[/keyword] is not valid '
        'or no help documentation exists, the help command will display:'
        '\n\t'
        '[example]No help documentation is available for the command '
        '[keyword]<command>[/][/]'
        '\n\n'
        'If no command (or no valid command) is passed to the [example]help[/] '
        f'command, then {_PROG}\'s default help output is printed to stdout.'
)


class HelpCommand(Command):
    """
    Inherits from the base Command class and overrides the `run` method
    to implement the Help functionality.
    """
    def __init__(self, name, aliases=None):
        super().__init__(name, _HELP, aliases=aliases or [])

    def get_command_parser(self, *args, **kwargs):
        """No custom command parser implementation is needed."""
        return None

    # def run(self, *args, **kwargs):
    def run(self, *args, **kwargs) -> None:
        """Implements the `help` commands functionality."""
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
            # determine which command the user asked for help about.
            # Then invoke the help for that command.
            command = getattr(sys.modules[__name__], f'{command_name}_command')
            command.show_help()
        except AttributeError:
            _LOGGER.error('There is no help documentation is available for '
                          'the command: "%s"', command_name)


#
# Create the HelpCommand instance
#
help_command = HelpCommand(name='help', aliases=['help'])
