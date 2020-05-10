from __future__ import print_function, absolute_import
from pyvsc._command import Command
from pyvsc._config import _PROG
from pyvsc._help import Help


_HELP = Help(
    name='outdated',
    brief='Show extensions that can be updated',
    synopsis='' \
        '{prog} outdated\n' \
        '{prog} outdated [[<editor> ...]]\n' \
        '{prog} outdated [[<extension> ...]]\n' \
        ''.format(prog=_PROG),
    description='' \
        'This command will check the VSCode Marketplace to see if ' \
        'any (or, specific) installed extensions are currently outdated.' \
        '\n\n' \
        'It will also check if any (or, specific) installed code editors ' \
        'are currently outdated.' \
        '\n\n' \
        'It will then print a list of results to stdout to indicate which ' \
        'extensions (and/or editors) have remote versions that are newer ' \
        'than the locally-installed versions.' \
        '\n\n' \
        'This command will not ever actually download or install anything. ' \
        'It\'s essentially a peek or dry-run to see what could be updated. ' \
)


class OutdatedCommand(Command):
    def __init__(self, name, aliases=[]):
        super().__init__(name, _HELP, aliases=aliases)

    def run(self, *args, **kwargs):
        print('TODO: Imlement OutdatedCommand.run()')


outdated_command = OutdatedCommand(
    name='outdated',
    aliases=['outdated']
)
