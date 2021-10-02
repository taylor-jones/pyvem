"""Commands command implementation"""

import sys
from typing import List, Dict

from pyvem._command import Command
from pyvem._config import _PROG
from pyvem._help import Help
from pyvem._logging import get_rich_logger

from pyvem.commands.config import config_command
from pyvem.commands.help import help_command
from pyvem.commands.info import info_command
from pyvem.commands.install import install_command
from pyvem.commands.list import list_command
from pyvem.commands.outdated import outdated_command
from pyvem.commands.search import search_command
from pyvem.commands.update import update_command
from pyvem.commands.version import version_command


_LOGGER = get_rich_logger(__name__)
_HELP = Help(
    name='commands',
    brief=f'lists the supported {_PROG} commands',
    synopsis='',
    description=f'For detailed information about a specific command, use'
                f'[example]{_PROG} help <command>[/example]')


class CommandsCommand(Command):
    """
    The CommandsCommand class defines the "commands" command. This class
    inherits from the base Command class.
    """
    def __init__(self, name, aliases=None):
        super().__init__(name, _HELP, aliases=aliases or [])

    def get_command_parser(self, *args, **kwargs):
        pass

    def run(self, *args, **kwargs):
        """
        Print the supported commands and exit.
        """
        # Update the logger to apply the log-level from the main options
        self.apply_log_level(_LOGGER)

        for cmd in get_command_objs():
            print(cmd.help.heading)

        sys.exit(0)


#
# Create the VesionCommand instance
#
commands_command = CommandsCommand(name='commands')


def get_command_list():
    """
    Returns a list of all the filenames (without their extensions) from the
    commands/ directory, which represents the names of all the valid commands.

    Returns:
        list
    """
    from os import path, listdir
    here = path.dirname(__file__)
    cmds = [f.split('.')[0] for f in listdir(here) if not f.startswith('_')]
    return sorted(cmds)


def get_command_map():
    """
    Maps all command aliases to their command name.

    Returns:
        dict -- A flattened, 1D dict of all names and aliases.
    """
    mapped = dict()
    commands_and_keys = set()

    def map_aliases(obj):
        for x in obj.aliases:
            mapped[x] = obj.name
            commands_and_keys.add(x)

    for c in _COMMAND_NAMES:
        obj = getattr(sys.modules[__name__], '%s_command' % c)
        map_aliases(obj)

    return mapped, commands_and_keys


def resolved_command(command_name: str) -> str:
    """
    Returns the name of a registered command given a command name or alias
    to check against. If the input command does not match any registered
    command or alias, None is returned.

    Arguments:
        command_name {str}

    Returns:
        str -- The name of a registered command.
    """
    return _COMMAND_MAP.get(command_name, None)


def get_command_obj(command_name: str) -> Command:
    """
    Returns and instance of a registered command object associated with
    the command argument.

    Arguments:
        command_name {str}

    Returns:
        Command
    """
    if command_name == 'commands':
        return commands_command

    resolved_cmd_name = resolved_command(command_name)
    if resolved_cmd_name:
        return getattr(sys.modules[__name__], '%s_command' % resolved_cmd_name)


def get_command_objs() -> List[Command]:
    """
    Returns a list of all Command objects
    """
    return [get_command_obj(x) for x in get_command_list()]


_COMMAND_NAMES = sorted([x for x in get_command_list() if x])
_COMMAND_MAP, _COMMAND_NAMES_AND_ALIASES = get_command_map()
