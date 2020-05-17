from __future__ import print_function, absolute_import
import sys

from pyvsc._command import Command
from pyvsc._config import _PROG
from pyvsc._help import Help

# Import each of the other commands so their 'help' methods can be invoked
# from here. This is the only command that needs to import all of the other
# commands.
from pyvsc.commands.config import config_command
from pyvsc.commands.info import info_command
from pyvsc.commands.install import install_command
from pyvsc.commands.list import list_command
from pyvsc.commands.outdated import outdated_command
from pyvsc.commands.search import search_command
from pyvsc.commands.update import update_command
from pyvsc.commands.version import version_command


_HELP = Help(
    name='help',
    brief='Show help documentation',
    synopsis='{prog} help <command>'.format(prog=_PROG),
    description='' \
        'This command will show help documentation for other {prog} ' \
        'commands. If the provided [keyword]<command>[/] is not valid or no ' \
        'help documentation exists, the help command will display:\n' \
        '\t"No help documentation is available for the command ' \
        '[keyword]<command>[/]"' \
        '\n\n' \
        'If no command (or no valid command) is passed to the help command, ' \
        'then {prog}\'s default help output is printed to stdout.' \
        ''.format(prog=_PROG)
)


class HelpCommand(Command):
    """
    Inherits from the base Command class and overrides the `run` method
    to implement the Help functionality.
    """
    def __init__(self, name, aliases=[]):
        super().__init__(name, _HELP, aliases=aliases)

    def run(self, *args, **kwargs):
        """
        Implements the `help` commands functionality.
        """
        # If the `help` command didn't get any arguments, just show the
        # default vem help screen and then exit.
        args = Command.main_options.args
        if not args:
            Command.main_parser.print_help()
            sys.exit(1)

        # Otherwise, parse the command name.
        command_name = args[0]

        # command = getattr(sys.modules[__name__], '%s_command' % command_name)
        # command.show_help()

        try:
            command = getattr(
                sys.modules[__name__], '%s_command' % command_name)
            command.show_help()
        except Exception:
            self.console.print_exception()
            print('No help documentation is available for command: %s' \
                % command_name)


#
# Create the HelpCommand instance
#
help_command = HelpCommand(name='help', aliases=['help'])
