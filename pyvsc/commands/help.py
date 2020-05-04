from __future__ import print_function, absolute_import

import sys

from pyvsc._command import Command
from pyvsc._config import _PROG
from pyvsc._colored import red, cyan, bold, white

from pyvsc.commands.config import config_command
from pyvsc.commands.info import info_command
from pyvsc.commands.install import install_command
from pyvsc.commands.list import list_command
from pyvsc.commands.outdated import outdated_command
from pyvsc.commands.search import search_command
from pyvsc.commands.update import update_command
from pyvsc.commands.version import version_command


_HELP = """
{NAME}
    help -- Show help documentation

{SYNOPSIS}
    {prog} help <command>

{DESCRIPTION}
    This command will show help documentation for other `{prog}`
    commands. If the provided <command> is not valid or no help
    documentation exists, the `help` command will display:
    "No help documentation is available for the command <command>"
    
    If no command (or no valid command) is passed to the `help`
    command, then {prog}'s default help output is printed to stdout.

""".format(
    NAME=red('NAME'),
    SYNOPSIS=red('SYNOPSIS'),
    DESCRIPTION=red('DESCRIPTION'),
    prog=_PROG
)


class HelpCommand(Command):
    """
    Inherits from the base Command class and overrides the `run` method
    to implement the Help functionality.
    """
    def __init__(self, name, aliases=[]):
        super().__init__(name, _HELP, aliases=aliases)

    def run(self, args, parser, **kwargs):
        """
        Implements the `help` commands functionality.

        Arguments:
            args {str} -- The name of the command to show help for
            parser {configargparse.ArgParser} -- ArgParser instance
        """
        # If the `help` command didn't get any arguments, just show the
        # default vem help screen and then exit.
        if not args:
            parser.print_help()
            sys.exit(1)

        # Otherwise, parse the command name.
        command_name = args[0]

        try:
            command = getattr(
                sys.modules[__name__], '%s_command' % command_name)
            command.show_help()
        except Exception:
            print('No help documentation is available for command: %s' \
                % command_name)



help_command = HelpCommand(
    name='help',
    aliases=['help']
)