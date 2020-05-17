from __future__ import print_function, absolute_import
from pyvsc._command import Command
from pyvsc._config import _PROG
from pyvsc._help import Help


_HELP = Help(
    name='config',
    brief='Manage the {prog} configuration file.'.format(prog=_PROG),
    synopsis='\t{prog} config set <key> <value>\n'
             '\t{prog} config get <key>\n'
             '\t{prog} config delete <key>'
             '\t{prog} config list'
             '\t{prog} config edit'
             '\n\n'
             '\t[h2]aliases:[/h2] {prog} c'.format(prog=_PROG),
    description='This command provides a means of managing {prog}\'s '
                '.{prog}rc file. This allows for setting, getting, or '
                'updating the contents within the .{prog}rc.'.format(
                    prog=_PROG),
    sub_commands='Config supports the following sub-commands:'
                 '\n\n'
                 '[h2]set[/h2]\n'
                 '\t[example]{prog} config set <key> <value>[/]\n'
                 '\tSets the config key to the value.\n'
                 '\tIf the value is omitted, it\'s set to "true".\n\n'
                 '[h2]get[/h2]\n'
                 '\t[example]{prog} config get <key>[/]\n'
                 '\tPrints the config key value to stdout.\n\n'
                 '[h2]list[/h2]\n'
                 '\t[example]{prog} config list[/]\n'
                 '\tPrints all of the config settings to stdout.\n\n'
                 '[h2]delete[/h2]\n'
                 '\t[example]{prog} config delete <key>[/]\n'
                 '\tDeletes the key from the configuration file.\n\n'
                 ''.format(prog=_PROG)
)


class ConfigCommand(Command):
    """
    Inherits from the base Command class and overrides the `run` method
    to implement the Config functionality.
    """
    def __init__(self, name, aliases=[]):
        super().__init__(name, _HELP, aliases=aliases)

    def run(self, *args, **kwargs):
        print('TODO: Implement config run()')


#
# Create the ConfigCommand instance
#
config_command = ConfigCommand(
    name='config',
    aliases=['config', 'c']
)
