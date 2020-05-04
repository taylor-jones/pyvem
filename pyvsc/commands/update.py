from __future__ import print_function, absolute_import
from pyvsc._command import Command
from pyvsc._config import _PROG
from pyvsc._colored import red, cyan


_HELP = """
{NAME}
    update -- Update extension(s) and editor(s)

{SYNOPSIS}
    {prog} update
    {prog} update [<extension-1>..<extension-N>]
    {prog} update [--<editor>]
    {prog} update [--no-editor]
    {prog} update [*]

    {aliases}: {prog} up, {prog} upgrade

{DESCRIPTION}
    This command will update all extensions listed to their latest
    versions. It will also install missing extensions, if the extension(s) 
    given to the `update` command are not yet installed.

    If no arguments are provided to the `update` command, `{prog}` will
    default to updating all extensions for the current VSCode installation.
    In order to update all extensions for a different version of VSCode,
    instead, provide a `--<editor` option to the `update` command. For
    example, to update all the extensions for VSCode Insiders, use the
    following command:
        {prog} update {INSIDERS}
    
    By default, {prog} will also look for an update to the code editor.
    In order to bypass this check, the {NO_EDITOR} option can be provided.
    
    In order to check for update to all of the installed code editor on
    the local system as well as all of their extensions, use:
        {prog} update {ASTERISK}
""".format(
    NAME=red('NAME'),
    SYNOPSIS=red('SYNOPSIS'),
    DESCRIPTION=red('DESCRIPTION'),
    prog=_PROG,
    aliases=cyan('aliases'),
    INSIDERS=red('--insiders'),
    NO_EDITOR=red('--no-editor'),
    ASTERISK=red('*'),
)


class UpdateCommand(Command):
    def __init__(self, name, aliases=[]):
        super().__init__(name, _HELP, aliases=aliases)

    def run(self, args, parser, **kwargs):
        print('TODO: Imlement UpdateCommand.run()')


update_command = UpdateCommand(
    name='update',
    aliases=['update', 'upgrade', 'up'],
)
