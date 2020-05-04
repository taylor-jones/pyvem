from __future__ import print_function, absolute_import
from pyvsc._command import Command
from pyvsc._config import _PROG
from pyvsc._colored import red, cyan


_HELP = """
{NAME}
    info -- Show extension details

{SYNOPSIS}
    {prog} info <extension>
    {prog} info <extension>[@<version>]

    {aliases}: {prog} show, {prog} view

{DESCRIPTION}
    This command shows data about an extension from the VSCode Marketplace.
    The default extension version is "latest", unless otherwise specified.
    The `info` command only accepts one extension at a time.

""".format(
    NAME=red('NAME'),
    SYNOPSIS=red('SYNOPSIS'),
    DESCRIPTION=red('DESCRIPTION'),
    prog=_PROG,
    aliases=cyan('aliases')
)


class InfoCommand(Command):
    def __init__(self, name, aliases=[]):
        super().__init__(name, _HELP, aliases=aliases)

    def run(self, args, parser, **kwargs):
        print('TODO: Imlement InfoCommand.run()')


info_command = InfoCommand(
    name='info',
    aliases=['info', 'show', 'view'],
)
