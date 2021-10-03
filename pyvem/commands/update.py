"""Update command implementation"""

import configargparse
from fuzzywuzzy import process

from rich.console import Console
from rich.table import Table
from rich import box

from pyvem._command import Command
from pyvem._config import _PROG, rich_theme
from pyvem._editor import SupportedEditorCommands, get_editors
from pyvem._help import Help
from pyvem._logging import get_rich_logger

_FUZZY_SORT_CONFIDENCE_THRESHOLD = 85
_AVAILABLE_EDITOR_KEYS = SupportedEditorCommands.keys()
_AVAILABLE_EDITOR_VALUES = SupportedEditorCommands.values()

_CONSOLE = Console(theme=rich_theme)
_LOGGER = get_rich_logger(__name__)
_HELP = Help(
    name='update',
    brief='Update extension(s) and editor(s)',
    synopsis=f'{_PROG} update\n'
             f'{_PROG} update [[<extension-1>..<extension-N>]]\n'
             f'{_PROG} update [[--<editor>]]\n'
             f'{_PROG} update [[--no-editor]]\n'
             f'{_PROG} update [[--all]]\n\n'
             f'[h2]aliases[/]: {_PROG} up, {_PROG} upgrade, {_PROG} u',
    description= \
        'This command will update extensions to the latest versions. If an '
        'explicit extension is passed to the [example]update[/] command and '
        'the extension is not yet installed, this command will install the '
        'extension.'
        '\n\n'
        'If no arguments are provided to the [example]update[/] command, '
        f'{_PROG} will default to updating all extensions for the current '
        'VSCode installation.'
        '\n\n'
        'To update all extensions for a different version of VSCode instead, '
        'provide a [example]--<editor>[/] option to the [example]update[/] '
        'command. For example, to update all the extensions for VSCode '
        'Insiders, use:'
        '\n\t'
        f'[example]{_PROG} update --insiders[/]'
        '\n\n'
        f'By default, {_PROG} will also look for an update to the code '
        'editor. In order to bypass this check, the [example]--no-editor[/] '
        'option can be provided.'
        '\n\n'
        'To check for updates for all of the installed code editors on your '
        'system as well as all of their extensions, use:'
        '\n\t'
        f'[example]{_PROG} update --all[/]'
)


class UpdateCommand(Command):
    """
    The UpdateCommand class defines the "update" command. This class
    inherits from the base Command class.
    """
    def __init__(self, name, aliases=None):
        super().__init__(name, _HELP, aliases=aliases or [])

    def get_command_parser(self, *args, **kwargs):
        """
        Provides a parser for the `update` command
        """
        parser_kwargs = {'add_help': False, 'prog': f'{_PROG} {self.name}'}
        parser = configargparse.ArgumentParser(**parser_kwargs)

        parser.add_argument('--help', action='help', help='Show help.')
        parser.add_argument('extensions', nargs='+', default=[],
                            help='Extension id(s) to list information about.')
        parser.add_argument('--code', default=False, action='store_true',
                            help='List VSCode extensions.')
        parser.add_argument('--codium', default=False, action='store_true',
                            help='List VSCodium extensions.')
        parser.add_argument('--insiders', default=False, action='store_true',
                            help='List VSCode Insiders extensions.')
        parser.add_argument('--all', default=False, action='store_true',
                            help='List all installed code editor extensions.')

    def run(self, *args, **kwargs):
        # Update the logger to apply the log-level from the main options
        self.apply_log_level(_LOGGER)

        # TODO:
        # 1) Check if an extension is installed
        # 2) Check if an extension is outdated
        # 3) Install/Update

        print('TODO: Implement UpdateCommand.run()')


#
# Create the UpdateCommand instance
#
update_command = UpdateCommand(name='update',
                               aliases=['update', 'upgrade', 'u'],)
