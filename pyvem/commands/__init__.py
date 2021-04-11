"""
Package containing all vem commands
"""
from __future__ import print_function, absolute_import
from sys import modules

from pyvem.commands.config import config_command
from pyvem.commands.help import help_command
from pyvem.commands.info import info_command
from pyvem.commands.install import install_command
from pyvem.commands.list import list_command
from pyvem.commands.outdated import outdated_command
from pyvem.commands.search import search_command
from pyvem.commands.update import update_command
from pyvem.commands.version import version_command


def get_command_list():
    """
    Returns a list of all the filenames (without their extensions) from the
    commands/ directory, which represents the names of all the valid commands.

    Returns:
        list
    """
    from os import path, listdir
    d = path.dirname(__file__)
    return [f.split('.')[0] for f in listdir(d) if not f.startswith('_')]


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
        obj = getattr(modules[__name__], '%s_command' % c)
        map_aliases(obj)

    return mapped, commands_and_keys



_COMMAND_NAMES = sorted(get_command_list())
_COMMAND_MAP, _COMMAND_NAMES_AND_ALIASES = get_command_map()



def resolved_command(command):
    """
    Returns the name of a registered command given a command name or alias
    to check against. If the input command does not match any registered
    command or alias, None is returned.

    Arguments:
        command {str}

    Returns:
        str -- The name of a registered command.
    """
    return _COMMAND_MAP.get(command, None)


def get_command_obj(command):
    """
    Returns and instance of a registered command object associated with
    the command argument.

    Arguments:
        command {str}

    Returns:
        Command
    """
    cmd = resolved_command(command)
    if cmd:
        return getattr(modules[__name__], '%s_command' % cmd)
