from __future__ import print_function, absolute_import
import configargparse

from pyvsc._command import Command
from pyvsc._config import _PROG
from pyvsc._colored import red, cyan
from pyvsc._models import ExtensionQuerySortByTypes

_SEARCH_CATEGORIES = [
    'Azure',
    'Debuggers',
    'Extension Packs',
    'Formatters',
    'Keymaps',
    'Language Maps',
    'Linters',
    'Others',
    'Programming Languages',
    'SCM Providers',
    'Snippets',
    'Themes'
]


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

    By default, up to 15 results are returned, but this default may be
    overriden using the {LIMIT} option.

    Available sorting options:
    --sort relevance (default)
    --sort installs
    --sort rating
    --sort updated

""".format(
    NAME=red('NAME'),
    SYNOPSIS=red('SYNOPSIS'),
    DESCRIPTION=red('DESCRIPTION'),
    prog=_PROG,
    aliases=cyan('aliases'),
    SORT_BY=red('--sort [COLUMN]'),
    LIMIT=red('--limit [NUMBER]'),
)


class SearchCommand(Command):
    def __init__(self, name, aliases=[]):
        super().__init__(name, _HELP, aliases=aliases)


    def get_command_parser(self, *args, **kwargs):
        parser_kwargs = {
            # 'usage': '%s <query> [options]' % self.name,
            'add_help': False,
            'prog': self.name,
        }

        parser = configargparse.ArgumentParser(**parser_kwargs)

        parser.add_argument(
            '--help',
            action='help',
            help='Show help.'
        )

        parser.add_argument(
            'query',
            nargs='+',
            default=[],
            help='The search text.'
        )

        parser.add_argument(
            '--sort',
            default='relevance',
            type=str,
            help='The column to sort the search results by.'
        )

        parser.add_argument(
            '--limit',
            default=15,
            type=int,
            help='The max number of search results to return.'
        )

        return parser


    def run(self, *args, **kwargs):
        # Create a new parser to parse the search command
        parser = self.get_command_parser()
        args, remainder = parser.parse_known_args()

        # Remove the leading "search" command from the arguments
        args.query = args.query[1:]

        if args.query:
            # build the query string
            query_string = ' '.join(args.query)

            # make sure there's a tunnel connection
            Command.tunnel.connect()

            # TODO: Implement passing sort option value to marketplace

            # send the query to the marketplace
            Command.marketplace.search_extensions(query_string)
        else:
            print(red('The "search" command expects a query.'))
            parser.print_usage()



search_command = SearchCommand(
    name='search',
    aliases=['search', 'find', 's']
)
