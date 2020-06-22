"""Update command implementation"""

from pyvsc._command import Command
from pyvsc._config import _PROG
from pyvsc._help import Help
from pyvsc._logging import get_rich_logger


_LOGGER = get_rich_logger(__name__)
_HELP = Help(
    name='update',
    brief='Update extension(s) and editor(s)',
    synopsis=f'{_PROG} update\n'
             f'{_PROG} update [[<extension-1>..<extension-N>]]\n'
             f'{_PROG} update [[--<editor>]]\n'
             f'{_PROG} update [[--no-editor]]\n'
             f'{_PROG} update [[*]]\n\n'
             f'[h2]aliases[/]: {_PROG} up, {_PROG} upgrade',
    description='This command will update all extensions listed to their latest versions. '
                'It will also install missing extensions, if the extension(s) given to the '
                '`update` command are not yet installed.'
                '\n\n'
                f'If no arguments are provided to the `update` command, `{_PROG}` will default '
                'to updating all extensions for the current VSCode installation.\n'
                'In order to update all extensions for a different version of VSCode, instead, '
                'provide a `--<editor` option to the `update` command. For example, to update all '
                'the extensions for VSCode Insiders, use the following command:\n'
                f'\t[example]{_PROG} update --insiders[/]'
                '\n\n'
                f'By default, {_PROG} will also look for an update to the code editor. In order '
                'to bypass this check, the [example]--no-editor[/] option can be provided.'
                '\n\n'
                'In order to check for update to all of the installed code editor on the local '
                'system as well as all of their extensions, use:\n'
                f'\t[example]{_PROG} update *[/]'
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
        No custom command parser implementation is needed for the Update command.
        """
        return None


    def run(self, *args, **kwargs):
        # Update the logger to apply the log-level from the main options
        self.apply_log_level(_LOGGER)

        print('TODO: Imlement UpdateCommand.run()')


#
# Create the UpdateCommand instance
#
update_command = UpdateCommand(
    name='update',
    aliases=['update', 'upgrade', 'up'],
)
