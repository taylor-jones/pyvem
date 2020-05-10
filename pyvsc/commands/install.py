from __future__ import print_function, absolute_import
from pyvsc._command import Command
from pyvsc._config import _PROG
from pyvsc._help import Help


_HELP = Help(
    name='install',
    brief='Install extension(s)',
    synopsis='' \
        '{prog} install (with no args, installs any .vsix in the current ' \
            'directory)\n' \
        '{prog} install <editor>\n' \
        '{prog} install <publisher>.<package>\n' \
        '{prog} install </path/to/extension.vsix>\n' \
        '{prog} install </path/to/directory>\n\n' \
        '[h2]aliases[/]: {prog} show, {prog} view' \
        ''.format(prog=_PROG),
    description='' \
        'This command installs an extension as well as any extensions that ' \
        'it depends on. This command can also be used to install any of the ' \
        'supported code editors.' \
        '\n\n' \
        'One or more extensions may be provided to the install command, ' \
        'using a space-delimited list [example](e.g. {prog} install <ext1> ' \
            '<ext2>)[/]' \
        '\n\n' \
        'Notice in the synopsis that an extension is specified by both its ' \
        'publisher name and package name. Together, these make up the ' \
        'extension\'s unique id, which helps identify it within the VSCode ' \
        'Marketplace.' \
        '\n\n'
        'If a local file-system path is provided, {prog} will attempt ' \
        'to install the extension(s) at the provided path. Otherwise, ' \
        'the `install` command involves making a remote request to the' \
        'VSCode Marketplace to download the .vsix extension(s).' \
        ''.format(prog=_PROG)
)


class InstallCommand(Command):
    def __init__(self, name, aliases=[]):
        super().__init__(name, _HELP, aliases=aliases)

    def run(self, *args, **kwargs):
        print('TODO: Imlement InstallCommand.run()')


install_command = InstallCommand(
    name='install',
    aliases=['install', 'i', 'add']
)
