"""Update command implementation"""

import configargparse
from fuzzywuzzy import process

from rich.console import Console
from rich.table import Table
from rich import box

from pyvsc._command import Command
from pyvsc._config import _PROG, rich_theme
from pyvsc._editor import SupportedEditorCommands, get_editors
from pyvsc._help import Help
from pyvsc._logging import get_rich_logger


_FUZZY_SORT_CONFIDENCE_THRESHOLD = 85
_AVAILABLE_EDITOR_KEYS = SupportedEditorCommands.keys()
_AVAILABLE_EDITOR_VALUES = SupportedEditorCommands.values()

_console = Console(theme=rich_theme)
_LOGGER = get_rich_logger(__name__)
_HELP = Help(
    name='update',
    brief='Update extension(s) and editor(s)',
    synopsis=f'{_PROG} update\n'
             f'{_PROG} update [[<extension-1>..<extension-N>]]\n'
             f'{_PROG} update [[--<editor>]]\n'
             f'{_PROG} update [[--no-editor]]\n'
             f'{_PROG} update [[--all]]\n\n'
             f'[h2]aliases[/]: {_PROG} up, {_PROG} upgrade',
    description='This command will update extensions to their latest versions. If an explicit '
                'extension is passed to the [example]update[/] command and the extension is not '
                'yet installed, this command will install the extension.'
                '\n\n'
                f'If no arguments are provided to the [example]update[/] command, `{_PROG}` will '
                'default to updating all extensions for the current VSCode installation.\n'
                'In order to update all extensions for a different version of VSCode, instead, '
                'provide a `--<editor>` option to the `update` command. For example, to update all '
                'the extensions for VSCode Insiders, use the following command:\n'
                f'\t[example]{_PROG} update --insiders[/]'
                '\n\n'
                f'By default, {_PROG} will also look for an update to the code editor. In order '
                'to bypass this check, the [example]--no-editor[/] option can be provided.'
                '\n\n'
                'In order to check for update to all of the installed code editor on the local '
                'system as well as all of their extensions, use:\n'
                f'\t[example]{_PROG} update --all[/]'
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
        parser_kwargs = {'add_help': False, 'prog': '{} {}'.format(_PROG, self.name)}
        parser = configargparse.ArgumentParser(**parser_kwargs)

        parser.add_argument(
            '--help',
            action='help',
            help='Show help.'
        )

        parser.add_argument(
            'extensions',
            nargs='+',
            default=[],
            help='Extension id(s) to list information about.'
        )

        parser.add_argument(
            '--code',
            default=False,
            action='store_true',
            help='List VSCode extensions.'
        )

        parser.add_argument(
            '--codium',
            default=False,
            action='store_true',
            help='List VSCodium extensions.'
        )

        parser.add_argument(
            '--insiders',
            default=False,
            action='store_true',
            help='List VSCode Insiders extensions.'
        )

        parser.add_argument(
            '--all',
            default=False,
            action='store_true',
            help='List extensions for all installed code editors.'
        )


    def run(self, *args, **kwargs):
        # Update the logger to apply the log-level from the main options
        self.apply_log_level(_LOGGER)

        print('TODO: Implement UpdateCommand.run()')


#
# Create the UpdateCommand instance
#
update_command = UpdateCommand(
    name='update',
    aliases=['update', 'upgrade', 'up'],
)
