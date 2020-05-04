from __future__ import print_function
from __future__ import absolute_import

import os
import sys

import logging
import configargparse
import coloredlogs

from fabric.util import get_local_user
from pyvsc._tunnel import Tunnel
from pyvsc._util import AttributeDict, iso_now, resolved_path
from pyvsc._editor import SupportedEditorCommands
from pyvsc.commands import (
    config_command,
    help_command,
    info_command,
    install_command,
    list_command,
    outdated_command,
    search_command,
    update_command,
    version_command,
)

from pyvsc.commands import _COMMAND_NAMES, get_command_obj
from pyvsc._config import _PROG

"""
Usage: vem <command> [args]

where <command> is one of:
...
...
...

**** commands I'd like to implement:
--------------------------------------------------------------------------
config -- manage the vem configuration files
help -- show help
info -- get info for a particular marketplace extension
install -- install extensions from the marketplace space-delimited
list (or ls) [editor] - list installed packages
outdated [editor] -- find all extensions that can be updated
search -- query the marketplace for matching extensions
update -- update extensions space-delimited   <-- would like to be able to update vem too
version -- show the vem version
"""

_LOGGER = logging.getLogger(__name__)
coloredlogs.install(
    level='DEBUG',
    logger=_LOGGER,
    fmt='%(asctime)s,%(msecs)03d %(name)s %(levelname)s %(message)s'
)


def get_commands():
    """
    Returns a list of all the filenames (without their extensions) from the
    commands/ directory, which represents the names of all the valid commands.

    Returns:
        list
    """
    from os import listdir
    d = os.path.dirname(__file__)
    p = os.path.join(d, 'commands')
    return [f.split('.')[0] for f in listdir(p) if f != '__init__.py']



_USAGE = '%s <command> [options]\n\nwhere <command> is one of:\n%s\n\nFor ' \
    'help about a certain command:\n\t%s help <command>'% \
        (_PROG, '\t' + ', '.join(_COMMAND_NAMES), _PROG)


def create_main_parser():
    """
    Creates and returns the main parser for vem's CLI

    Returns:
        ConfigArgParse.ArgParser
    """
    parser_kwargs = {
        'usage': _USAGE,
        'add_help': False,
        'default_config_files': ['.vemrc', '~/.vemrc', '~/.config/.vemrc'],
        'prog': _PROG,
    }

    parser = configargparse.ArgumentParser(**parser_kwargs)

    # Usual arguments which are applicable for the whole script / top-level args
    parser.add(
        'command',
        nargs='?',
        choices=_COMMAND_NAMES.append(None),
        help='The main vem command to execute.'
    )

    parser.add(
        'args',
        nargs='*',
        default=[],
        help='The command arguments.'
    )

    parser.add(
        '--help',
        action='help',
        help='Show help.'
    )

    parser.add(
        '-V',
        '--version',
        action='store_true',
        default=False,
        help='Show version and exit.'
    )

    parser.add(
        '-h',
        '--ssh-host',
        default='',
        help='Specify a SSH host in the form [user@]server[:port].'
    )

    parser.add(
        '-g',
        '--ssh-gateway',
        default='',
        help='Specify a SSH gateway in the form [user@]server[:port].'
    )


    #
    # Add verbosity argument option group
    #
    log_level = parser.add_mutually_exclusive_group()
    parser.set_defaults(log_level=logging.INFO)

    parser.add(
        '-v',
        '--verbose',
        action='store_const',
        dest='log_level',
        const=logging.DEBUG,
        help='Show debug output.'
    )

    parser.add(
        '-q',
        '--quiet',
        action='store_const',
        dest='log_level',
        const=logging.ERROR,
        help='Show only the minimally necessary output.'
    )


    #
    # Add the editor argument option group
    #
    editor = parser.add_mutually_exclusive_group()
    parser.set_defaults(editor=SupportedEditorCommands.code)

    editor.add_argument(
        '--code',
        action='store_const',
        dest='editor',
        const=SupportedEditorCommands.code,
        help='(default) Use VSCode as the target editor.'
    )

    editor.add_argument(
        '--insiders',
        action='store_const',
        dest='editor',
        const=SupportedEditorCommands.insiders,
        help='Use VSCode Insiders as the target editor.'
    )

    editor.add_argument(
        '--exploration',
        action='store_const',
        dest='editor',
        const=SupportedEditorCommands.code,
        help='Use VSCode Exploration as the target editor.'
    )

    editor.add_argument(
        '--codium',
        action='store_const',
        dest='editor',
        const=SupportedEditorCommands.codium,
        help='Use VSCodium as the target editor.'
    )

    return parser


def main():
    parser = create_main_parser()
    args, remainder = parser.parse_known_args()

    # For now, add any remainder arguments to the extra args that we store
    # in a list after plucking the command.
    args.args.extend(remainder)

    # If we got no command, make sure the user didn't just ask for the version,
    # which would be the only case where it's valid to provide an option
    # without providing a command. If this has happened, we'll set the command
    # to be 'version' so the command parser is satisfied and can pass that
    # command along to the VersionCommand handler.
    if not args.command:
        if args.version:
            args.command = 'version'
        else:
            parser.print_help()
            sys.exit(1)

    # Check if the provided command matches one of the registered commands.
    # If so, pass it along to that command object to run. Otherwise, print
    # an error message and exit.
    command = get_command_obj(args.command)
    if command:
        command.run(args.args, parser)
    else:
        _LOGGER.error('Could not parse command: %s' % args.command)


if __name__ == "__main__":
    main()