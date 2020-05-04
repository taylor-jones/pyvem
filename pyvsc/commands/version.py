from __future__ import print_function, absolute_import
import sys
from pyvsc._command import Command
from pyvsc._config import _PROG, _VERSION
from pyvsc._colored import red, cyan


_HELP = """
{NAME}
    version -- shows the {prog} version

{SYNOPSIS}
    {prog} -V
    {prog} --version

    {aliases}: {prog} version

{DESCRIPTION}
    This command will print the current {prog} version to stdout.
""".format(
    NAME=red('NAME'),
    SYNOPSIS=red('SYNOPSIS'),
    DESCRIPTION=red('DESCRIPTION'),
    prog=_PROG,
    aliases=cyan('aliases'),
)


class VersionCommand(Command):
    """
    Inherits the base Command class and implements the Version
    command functionality.
    """
    def __init__(self, name, aliases=[]):
        super().__init__(name, _HELP, aliases=aliases)

    def run(self, args, parser, **kwargs):
        """
        Just print the program's version and exit.
        """
        print(_VERSION)
        sys.exit(0)


version_command = VersionCommand(
    name='version',
    aliases=['version'],
)
