from __future__ import print_function, absolute_import
from pyvsc._command import Command
from pyvsc._config import _PROG
from pyvsc._help import Help

_HELP = Help(
    name='update',
    brief='Update extension(s) and editor(s)',
    synopsis='' \
        '{prog} update\n' \
        '{prog} update [[<extension-1>..<extension-N>]]\n' \
        '{prog} update [[--<editor>]]\n' \
        '{prog} update [[--no-editor]]\n' \
        '{prog} update [[*]]\n\n' \
        '[h2]aliases[/]: {prog} up, {prog} upgrade' \
        ''.format(prog=_PROG),
    description='' \
        'This command will update all extensions listed to their latest ' \
        'versions. It will also install missing extensions, if the ' \
        'extension(s) given to the `update` command are not yet installed.' \
        '\n\n' \
        'If no arguments are provided to the `update` command, `{prog}`' \
        'will default to updating all extensions for the current VSCode ' \
        'installation.\n' \
        'In order to update all extensions for a different version of ' \
        'VSCode, instead, provide a `--<editor` option to the `update` ' \
        'command. For example, to update all the extensions for VSCode ' \
        'Insiders, use the following command:\n' \
        '\t[example]{prog} update --insiders[/]' \
        '\n\n'
        'By default, {prog} will also look for an update to the code editor.' \
        'In order to bypass this check, the [example]--no-editor[/] option can ' \
        'be provided.' \
        '\n\n' \
        'In order to check for update to all of the installed code editor ' \
        'on the local system as well as all of their extensions, use:\n' \
        '\t[example]{prog} update *[/]'
        ''.format(prog=_PROG)
)


class UpdateCommand(Command):
    def __init__(self, name, aliases=[]):
        super().__init__(name, _HELP, aliases=aliases)

    def run(self, *args, **kwargs):
        print('TODO: Imlement UpdateCommand.run()')


update_command = UpdateCommand(
    name='update',
    aliases=['update', 'upgrade', 'up'],
)
