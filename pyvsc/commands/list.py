from __future__ import print_function, absolute_import
from pyvsc._command import Command
from pyvsc._config import _PROG
from pyvsc._colored import red, cyan


_HELP = """
{NAME}
    list -- List installed extension(s)

{SYNOPSIS}
    {prog} list (with no args, show all installed extensions for all
            installed, supported code editors)
    {prog} list <editor>
    {prog} list --<editor>
    {prog} list --editors
    
    {aliases}: {prog} ls, {prog} ll, {prog} la

{DESCRIPTION}
    This command will print to stdout all of the versions of extensions
    that are installed. If an editor name is provided, the output will
    be scoped to only print the versions of extensions installed to that
    particular editor.
    
    When run as `ll` or `la`, the output will show additional extension
    information, including:
    - installed date
    - ...maybe others??

""".format(
    NAME=red('NAME'),
    SYNOPSIS=red('SYNOPSIS'),
    DESCRIPTION=red('DESCRIPTION'),
    prog=_PROG,
    aliases=cyan('aliases'),
)


class ListCommand(Command):
    def __init__(self, name, aliases=[]):
        super().__init__(name, _HELP, aliases=aliases)

    def run(self, args, parser, **kwargs):
        print('TODO: Imlement ListCommand.run()')


list_command = ListCommand(
    name='list',
    aliases=['list', 'ls', 'll', 'la']
)
