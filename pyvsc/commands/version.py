from __future__ import print_function, absolute_import
import sys
from pyvsc._command import Command
from pyvsc._config import _PROG, _VERSION
from pyvsc._help import Help

_HELP = Help(
    name='version',
    brief='shows the {prog} version'.format(prog=_PROG),
    synopsis='' \
        '{prog} -V\n' \
        '{prog} --version\n\n' \
        '[h2]aliases[/]: {prog} version' \
        ''.format(prog=_PROG),
    description='' \
        'This command will print the current {prog} version to stdout.' \
        ''.format(prog=_PROG)
)


class VersionCommand(Command):
    """
    Inherits the base Command class and implements the Version
    command functionality.
    """
    def __init__(self, name, aliases=[]):
        super().__init__(name, _HELP, aliases=aliases)

    def run(self, *args, **kwargs):
        """
        Just print the program's version and exit.
        """
        print(_VERSION)
        sys.exit(0)


version_command = VersionCommand(
    name='version',
    aliases=['version'],
)
