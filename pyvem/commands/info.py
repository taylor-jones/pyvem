"""Info command implementation"""

from pyvem._command import Command
from pyvem._config import _PROG
from pyvem._help import Help
from pyvem._logging import get_rich_logger


_LOGGER = get_rich_logger(__name__)
_HELP = Help(
    name='info',
    brief='Show extension details',
    synopsis=f'{_PROG} info <extension>\n'
             f'{_PROG} info <extension>[[@<version>]]\n\n'
             f'[h2]aliases[/]: {_PROG} show, {_PROG} view',
    description='This command shows data about an extension from the VSCode Marketplace. '
                'The default extension version is "latest", unless otherwise specified. '
                'The info command accepts 1+ extension at a time.'
)


class InfoCommand(Command):
    """
    The InfoCommand class defines the "info" command. This class
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

        # Make sure we got the correct number of arguments.
        args = Command.main_options.args
        arg_count = len(args)

        if arg_count:
            Command.tunnel.connect()
            for arg in args:
                Command.marketplace.get_extension_info(arg)
        else:
            self.show_error(f'The [i]"info"[/] command expects 1+ arguments ({arg_count} given).')


#
# Create the InfoCommand instance
#
info_command = InfoCommand(name='info', aliases=['info', 'show', 'view'])
