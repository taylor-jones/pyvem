from __future__ import print_function, absolute_import
from pyvsc._command import Command
from pyvsc._config import _PROG
from pyvsc._colored import red, cyan


_HELP = """
{NAME}
    search -- Search the VSCode Marketplace

{SYNOPSIS}
    {prog} search <term>
    {prog} search <term> [--sort-by {{rating|installs|name}}]
    {prog} search <term> [--amount [NUMBER]]
    
    {aliases}: {prog} s, {prog} find

{DESCRIPTION}
    This command searched the VSCode Marketplace for extensions matching
    the provided search terms. Additional search control is provided by
    specifying sorting options and/or specifying the amount of results to
    display. For instace:

    Search results may also be sorted using the {SORT_BY} option.

    By default, up to 20 results are returned, but this default may be
    overriden using the {AMOUNT} option.
    
    TODO: Better specify what is available, here.

""".format(
    NAME=red('NAME'),
    SYNOPSIS=red('SYNOPSIS'),
    DESCRIPTION=red('DESCRIPTION'),
    prog=_PROG,
    aliases=cyan('aliases'),
    SORT_BY=red('--sort-by [COLUMN]'),
    AMOUNT=red('--amount [NUMBER]'),
)


class SearchCommand(Command):
    def __init__(self, name, aliases=[]):
        super().__init__(name, _HELP, aliases=aliases)

    def run(self, *args, **kwargs):
        print('TODO: Imlement SearchCommand.run()')


search_command = SearchCommand(
    name='search',
    aliases=['search', 'find', 's']
)
