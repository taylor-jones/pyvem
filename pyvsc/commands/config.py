from __future__ import print_function, absolute_import
from pyvsc._command import Command
from pyvsc._config import _PROG
from pyvsc._colored import red, cyan


_HELP = """
{NAME}
    config -- Manage the {prog} configuration file.

{SYNOPSIS}
    {prog} config set <key> <value>
    {prog} config get <key>
    {prog} config delete <key>
    {prog} config list
    {prog} config edit

    {aliases}: {prog} c

{DESCRIPTION}
    This command provides a means of managing {prog}'s .{prog}rc file.
    This allows for setting, getting, or updating the contents within
    the .{prog}rc.

    {SUBCOMMANDS}
        Config supports the following sub-commands:
        
        {SET_CMD}
            Sets the config key to the value. If no value is provided, 
            then it sets the value to "true".

        {GET_CMD}
            Prints the config value to stdout.
        
        {LIST_CMD}
            Prints all of the config settings to stdout.
        
        {DELETE_CMD}
            Deletes the key from the configuration file.
        
        {EDIT_CMD}
            Opens the config file in an editor.

""".format(
    NAME=red('NAME'),
    SYNOPSIS=red('SYNOPSIS'),
    DESCRIPTION=red('DESCRIPTION'),
    prog=_PROG,
    aliases=cyan('aliases'),
    SUBCOMMANDS=cyan('Sub-commands'),
    SET_CMD=red('set'),
    GET_CMD=red('get'),
    LIST_CMD=red('list'),
    DELETE_CMD=red('delete'),
    EDIT_CMD=red('edit'),
)


class ConfigCommand(Command):
    """
    Inherits from the base Command class and overrides the `run` method
    to implement the Config functionality.
    """
    def __init__(self, name, aliases=[]):
        super().__init__(name, _HELP, aliases=aliases)


    def run(self, args, parser, **kwargs):
        print('TODO: Implement config run()')



config_command = ConfigCommand(
    name='config',
    aliases=['config', 'c']
)
