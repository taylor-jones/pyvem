from __future__ import print_function
from __future__ import absolute_import

import re
import os
import sys
import configargparse
import logging

from fuzzywuzzy import process
from rich.console import Console

from pyvsc._tunnel import Tunnel
from pyvsc._util import iso_now, resolved_path
from pyvsc._containers import AttributeDict
from pyvsc._editor import SupportedEditorCommands

from pyvsc.commands import _COMMAND_NAMES
from pyvsc.commands import _COMMAND_NAMES_AND_ALIASES
from pyvsc.commands import get_command_obj

from pyvsc._command import Command
from pyvsc._exceptions import raise_argument_error
from pyvsc._config import _PROG, rich_theme
from pyvsc._containers import parsed_connection_parts
from pyvsc._colored import red


_console = Console(theme=rich_theme)


def create_main_parser():
    """
    Creates and returns the main parser for vem's CLI

    Returns:
        ConfigArgParse.ArgParser
    """
    parser_kwargs = {
        'usage': '%s <command> [options]\n\nwhere <command> is one of:\n%s' \
            '\n\nFor help about a certain command:\n\t%s help <command>'% \
            (_PROG, '\t' + ', '.join(_COMMAND_NAMES), _PROG),
        'add_help': False,
        'default_config_files': ['.vemrc', '~/.vemrc', '~/.config/.vemrc'],
        'prog': _PROG,
    }

    parser = configargparse.ArgumentParser(**parser_kwargs)

    parser.add_argument(
        'command',
        nargs='?',
        choices=_COMMAND_NAMES.append(None),
        help='The main vem command to execute.'
    )

    parser.add_argument(
        'args',
        nargs='*',
        default=[],
        help='The command arguments.'
    )

    parser.add_argument(
        '--help',
        action='store_true',
        help='Show help.'
    )

    parser.add_argument(
        '-V', '--version',
        action='store_true',
        default=False,
        help='Show version and exit.'
    )

    parser.add_argument(
        '-h', '--ssh-host',
        default='',
        type=parsed_connection_parts,
        help='Specify a SSH host in the form [user@]server[:port].'
    )

    parser.add_argument(
        '-g', '--ssh-gateway',
        default='',
        type=parsed_connection_parts,
        help='Specify a SSH gateway in the form [user@]server[:port].'
    )


    #
    # Add verbosity argument option group
    #
    log_level = parser.add_mutually_exclusive_group()
    parser.set_defaults(log_level=logging.INFO)

    parser.add_argument(
        '-v', '--verbose',
        action='store_const',
        dest='log_level',
        const=logging.DEBUG,
        help='Show debug output.'
    )

    parser.add_argument(
        '-q', '--quiet',
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
    # print(args)

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
    if isinstance(command, Command):
        command.invoke(parser, args)
    elif args.help:
        parser.print_help()
    else:
        _console.print('[error]"{}" is not a valid {} command[/].\n'.format(
            args.command, _PROG))

        # Check for fuzzy-ish matches. Limit to 50% matches or greater.
        similar = [
            x[0] for x in process.extract(
                args.command,
                _COMMAND_NAMES_AND_ALIASES
            )if x[1] > 50
        ]

        # If any similar-enough matches were found, print those suggestions
        if similar:
            print('Maybe you meant one of these commands?\n%s\n' \
                % ', '.join(similar))

        parser.print_usage()
        print('')


if __name__ == "__main__":
    main()