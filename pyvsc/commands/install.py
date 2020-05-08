from __future__ import print_function, absolute_import
from pyvsc._command import Command
from pyvsc._config import _PROG
from pyvsc._colored import red, cyan, white, bold


_HELP = """
{NAME}
    install -- Install extension(s)

{SYNOPSIS}
    {prog} install (with no args, installs any .vsix in the current directory)
    {prog} install <editor>
    {prog} install <publisher>.<package>
    {prog} install </path/to/.vsix>
    {prog} install <folder>
    
    {aliases}: {prog} i, {prog} add

{DESCRIPTION}
    This command installs an extension as well as any extensions
    that it depends on. This command can also be used to install
    any of the supported code editors.

    One or more extensions may be provided to the `install` command,
    using a space-delimited list (e.g. {prog} install <ext1> <ext2>)
    
    Notice in the synopsis that an extension is specified by both its
    publisher name and package name. Together, these make up the 
    extension's unique id, which helps identify it within the VSCode
    Marketplace.

    If a local file-system path is provided, `{prog}` will attempt
    to install the extension(s) at the provided path. Otherwise,
    the `install` command involves making a remote request to the
    VSCode Marketplace to download the .vsix extension(s).

""".format(
    NAME=red('NAME'),
    SYNOPSIS=red('SYNOPSIS'),
    DESCRIPTION=red('DESCRIPTION'),
    prog=_PROG,
    aliases=cyan('aliases'),
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
