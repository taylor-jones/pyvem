from __future__ import print_function, absolute_import

import configargparse
from fuzzywuzzy import process
from rich.console import Console
from rich.syntax import Syntax

from pyvsc._command import Command
from pyvsc._config import _PROG
from pyvsc._models import ExtensionQuerySortByTypes
from pyvsc._help import Help

# Reference Configurations
_FUZZY_SORT_CONFIDENCE_THRESHOLD = 70
_DEFAULT_SORT_BY_ARGUMENT = ExtensionQuerySortByTypes['Relevance']
_AVAILABLE_SORT_COLUMNS = sorted(list(ExtensionQuerySortByTypes.keys()))
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


_HELP = Help(
    name='search',
    brief='Search the VSCode Marketplace',
    synopsis='' \
        '{prog} search <term>\n' \
        '{prog} search <term> [[--sort-by [[COLUMN]]]]\n' \
        '{prog} search <term> [[--count [[NUMBER]]]]\n\n' \
        '[h2]aliases:[/h2] {prog} s, {prog} find\n' \
        ''.format(prog=_PROG),
    description='' \
        'This command searched the VSCode Marketplace for ' \
        'extensions matching the provided search terms. Additional search ' \
        'control is provided by specifying sorting options and/or ' \
        'specifying the amount of results to display.',
    options='' \
        '[h2]--sort-by [[COLUMN]][/h2]\n' \
        '\t* Type: String\n' \
        '\t* Default: Relevance' \
        '\n\n' \
        'Sort the search results in descending order, based on a particular ' \
        'column value. {prog} uses fuzzy matching to check if the provided ' \
        '[bold]--sort-by[/bold] value matches any of the known sort ' \
        'columns.'
        '\n\n' \
        'Available sort columns include:\n'
        '{sort_columns}' \
        '\n\n' \
        '[h2]--count [[NUMBER]][/h2]\n' \
        '\t* Type: Integer\n' \
        '\t* Default: 15' \
        '\n\n' \
        'By default, up to 15 results are returned, but this default may be ' \
        'overriden to specify how many search results should be returned.' \
        ''.format(prog=_PROG, sort_columns=', '.join(_AVAILABLE_SORT_COLUMNS),
    )
)


class SearchCommand(Command):
    def __init__(self, name, aliases=[]):
        super().__init__(name, _HELP, aliases=aliases)


    def get_command_parser(self, *args, **kwargs):
        parser_kwargs = {'add_help': False, 'prog': self.name}
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
            '--sort-by',
            default='relevance',
            metavar='COLUMN',
            type=str,
            help='The column to sort the search results by.'
        )

        parser.add_argument(
            '--count',
            default=15,
            metavar='INT',
            type=int,
            help='The max number of search results to return.'
        )

        return parser


    def _get_sort_query(self, sort_argument=None):
        if sort_argument:
            match, confidence = process.extractOne(
                sort_argument,
                ExtensionQuerySortByTypes.keys())
            
            if confidence > _FUZZY_SORT_CONFIDENCE_THRESHOLD:
                return match, ExtensionQuerySortByTypes[match]
        return None, None


    def run(self, *args, **kwargs):
        # Create a new parser to parse the search command
        parser = self.get_command_parser()
        args, remainder = parser.parse_known_args()

        # Remove the leading "search" command from the arguments
        args.query = args.query[1:]

        if args.query:
            # build the query string
            query_string = ' '.join(args.query)
            sort_name, sort_num = self._get_sort_query(args.sort_by)

            if sort_num is None:
                # If we couldn't reasonably fuzzy-match a sort column, log that
                # warning to the console and use the default sort column.
                sorted_sort_options = \
                    sorted(list(ExtensionQuerySortByTypes.keys()))

                self.log.warning('"{}" did not match a known sort column.' \
                    ''.format(args.sort_by))
                self.log.warn('Available sort columns:\n{}\n\n' \
                    ''.format(', '.join(sorted_sort_options)))

                sort_by = _DEFAULT_SORT_BY_ARGUMENT
            else:
                self.log.debug('Sorting by "{}"'.format(sort_name))
                sort_by = sort_num

            # send the query to the marketplace
            Command.tunnel.connect()
            Command.marketplace.search_extensions(
                query_string, sort_by=sort_by, page_size=args.count)

        else:
            self.log.error('The "search" command expects a query.')
            parser.print_usage()


search_command = SearchCommand(
    name='search',
    aliases=['search', 'find', 's']
)
