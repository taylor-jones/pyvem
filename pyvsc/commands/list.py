"""List command implementation"""

from pyvsc._command import Command
from pyvsc._config import _PROG
from pyvsc._help import Help
from pyvsc._logging import get_rich_logger


_LOGGER = get_rich_logger(__name__)
_HELP = Help(
    name='list',
    brief='List installed extension(s)',
    synopsis=f'{_PROG} list (with no args, show all installed extensions\n'
             '\t\t  for all installed, supported code editors) \n'
             f'{_PROG} list [[<extension>]]\n'
             f'{_PROG} list [[<editor>]]\n'
             f'{_PROG} list [[--<editor>]]\n\n'
             f'[h2]aliases[/]: {_PROG} ls, {_PROG} ll, {_PROG} la',
    description='This command will print to stdout all of the versions of extensions that are '
                'installed. If an editor name is provided, the output will be scoped to only '
                'print the versions of extensions installed to that particular editor.'
                '\n\n'
                '[todo]TODO -- NOT YET IMPLEMENTED\n'
                'When run as `ll` or `la`, the output will show additional extension information, '
                'including:\n'
                '\t- installed date\n'
                '\t- ...maybe others??'
                '[/]'
)


class ListCommand(Command):
    """
    The ListCommand class defines the "list" command. This class
    inherits from the base Command class.
    """
    def __init__(self, name, aliases=None):
        super().__init__(name, _HELP, aliases=aliases or [])


    def get_command_parser(self, *args, **kwargs):
        """
        No custom command parser implementation is needed for the Info command.
        """
        return None


    def run(self, *args, **kwargs):
        # Update the logger to apply the log-level from the main options
        self.apply_log_level(_LOGGER)

        print('TODO: Imlement ListCommand.run()')


#
# Create the ListCommand instance
#
list_command = ListCommand(
    name='list',
    aliases=['list', 'ls', 'll', 'la']
)
