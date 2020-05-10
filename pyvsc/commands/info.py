from __future__ import print_function, absolute_import
from pyvsc._command import Command
from pyvsc._config import _PROG
from pyvsc._help import Help


_HELP = Help(
    name='info',
    brief='Show extension details',
    synopsis='' \
        '{prog} info <extension>\n' \
        '{prog} info <extension>[@<version>]\n\n' \
        '[h2]aliases[/]: {prog} show, {prog} view' \
        ''.format(prog=_PROG),
    description='' \
        'This command shows data about an extension from the VSCode ' \
        'Marketplace. The default extension version is "latest", unless ' \
        'otherwise specified. The info command only accepts one extension ' \
        'at a time.'
)


class InfoCommand(Command):
    def __init__(self, name, aliases=[]):
        super().__init__(name, _HELP, aliases=aliases)

    def run(self, *args, **kwargs):
        args = Command.main_options.args
        arg_count = len(args)
        
        if arg_count == 1:
            Command.tunnel.connect()
            Command.marketplace.get_extension_info(args[0])
        else:
            self.show_error('The [i]"info"[/] command expects 1 argument ' \
                '({} given).'.format(arg_count))
            return False


info_command = InfoCommand(
    name='info',
    aliases=['info', 'show', 'view'],
)
