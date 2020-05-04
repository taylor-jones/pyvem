"""
Package containing all vem commands
"""
from __future__ import print_function, absolute_import
from sys import modules

from pyvsc.commands.config import config_command
from pyvsc.commands.help import help_command
from pyvsc.commands.info import info_command
from pyvsc.commands.install import install_command
from pyvsc.commands.list import list_command
from pyvsc.commands.outdated import outdated_command
from pyvsc.commands.search import search_command
from pyvsc.commands.update import update_command
from pyvsc.commands.version import version_command


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
    mapped = {}
    
    def map_aliases(obj):
        for x in obj.aliases:
            mapped[x] = obj.name
    
    for c in _COMMAND_NAMES:
        obj = getattr(modules[__name__], '%s_command' % c)
        map_aliases(obj)

    return mapped



_COMMAND_NAMES = sorted(get_command_list())
_COMMAND_MAP = get_command_map()


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
