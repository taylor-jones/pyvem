from __future__ import print_function, absolute_import
from pyvsc._command import Command
from pyvsc._config import _PROG
from pyvsc._colored import red


_HELP = """
{NAME}
    outdated -- Show extensions that can be updated

{SYNOPSIS}
    {prog} outdated
    {prog} outdated [<editor> ...]
    {prog} outdated [<extension> ...]

{DESCRIPTION}
    This command will check the VSCode Marketplace to see if any
    (or, specific) installed extensions are currently outdated.

    It will also check if any (or, specific) installed code editors
    are currently outdated.
    
    It will then print a list of results to stdout to indicate which
    extensions (and/or editors) have remote versions that are newer
    than the locally-installed versions.

    This command will not ever actually download or install anything.
    It's essentially a `peek` or `dry-run` to see what could be updated.
""".format(
    NAME=red('NAME'),
    SYNOPSIS=red('SYNOPSIS'),
    DESCRIPTION=red('DESCRIPTION'),
    prog=_PROG,
)


class OutdatedCommand(Command):
    def __init__(self, name, aliases=[]):
        super().__init__(name, _HELP, aliases=aliases)

    def run(self, args, parser, **kwargs):
        print('TODO: Imlement OutdatedCommand.run()')


outdated_command = OutdatedCommand(
    name='outdated',
    aliases=['outdated']
)
