"""Search command implementation"""

import configargparse
from fuzzywuzzy import process
from rich.console import Console
from rich.table import Table
from rich import box

from pyvem._command import Command
from pyvem._config import _PROG
from pyvem._models import ExtensionQuerySortByTypes
from pyvem._help import Help
from pyvem._logging import get_rich_logger


# Reference Configurations
_FUZZY_SORT_CONFIDENCE_THRESHOLD = 70
_DEFAULT_SORT_BY_ARGUMENT_NAME = 'Relevance'
_DEFAULT_SORT_BY_ARGUMENT = ExtensionQuerySortByTypes[_DEFAULT_SORT_BY_ARGUMENT_NAME]
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

_console = Console()
_LOGGER = get_rich_logger(__name__, console=_console)

_HELP = Help(
    name='search',
    brief='Search the VSCode Marketplace',
    synopsis=f'{_PROG} search <term>\n'
             f'{_PROG} search <term> [[--sort-by [[COLUMN]]]]\n'
             f'{_PROG} search <term> [[--limit [[NUMBER]]]]\n\n'
             f'[h2]aliases:[/h2] {_PROG} s, {_PROG} find\n',
    description='This command searched the VSCode Marketplace for extensions matching the '
                'provided search terms. Additional search control is provided by specifying '
                'sorting options and/or specifying the amount of results to display.',
    options='[h2]--sort-by [[COLUMN]][/h2]\n'
            '\t* Type: String\n'
            '\t* Default: Relevance'
            '\n\n'
            'Sort the search results in descending order, based on a particular column value. '
            f'{_PROG} uses fuzzy matching to check if the provided [bold]--sort-by[/bold] value '
            'matches any of the known sort columns.'
            '\n\n'
            'Available sort columns include:\n'
            f'[example]{", ".join(_AVAILABLE_SORT_COLUMNS)}[/]'
            '\n\n'
            '[h2]--limit [[NUMBER]][/h2]\n'
            '\t* Type: Integer\n'
            '\t* Default: 15'
            '\n\n'
            'By default, up to 15 results are returned, but this default may be overriden to '
            'specify how many search results should be returned.'
)


class SearchCommand(Command):
    """
    The SearchCommand class defines the "search" command. This class
    inherits from the base Command class.
    """
    def __init__(self, name, aliases=None):
        super().__init__(name, _HELP, aliases=aliases or [])


    def get_command_parser(self, *args, **kwargs):
        """
        Builds and returns an argument parser that is specific to the "install"
        command.

        Returns:
            configargparse.ArgParser
        """
        parser_kwargs = {'add_help': False, 'prog': f'{_PROG} {self.name}'}
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
            help='Column to sort the results by.'
        )
        parser.add_argument(
            '--limit',
            default=15,
            metavar='NUMBER',
            type=int,
            help='Max number of results to return.'
        )

        return parser


    @staticmethod
    def _get_sort_query(sort_argument=None):
        """
        Determines the sort query component from the provided argument.

        Keyword Arguments:
            sort_argument {str} -- The sort argument provided in the search command (if any)

        Returns:
            tuple(str, int) -- The name of the column to sort by, the integer value to pass to the
            VSCode Marketplace so that it can register which column we want to sort by.
        """
        if sort_argument:
            match, confidence = process.extractOne(query=sort_argument,
                                                   choices=ExtensionQuerySortByTypes.keys())
            if confidence > _FUZZY_SORT_CONFIDENCE_THRESHOLD:
                return match, ExtensionQuerySortByTypes[match]
        return None, None


    @staticmethod
    def show_search_results(search_results):
        """
        Create and display a rich table of VSCode Marketplace marketplace results.

        Arguments:
            search_results {list} -- A list of search results
        """
        if search_results:
            table = Table(box=box.SQUARE)
            table.add_column('Extension ID', justify='left', no_wrap=True)
            table.add_column('Version', justify='right', no_wrap=True)
            table.add_column('Last Update', justify='right', no_wrap=True)
            table.add_column('Rating', justify='right', no_wrap=True)
            table.add_column('Installs', justify='right', no_wrap=True)
            table.add_column('Description', justify='left', no_wrap=False)

            for result in search_results:
                table.add_row(*result.values())
            _console.print(table)
        else:
            _console.print('Your search returned 0 results.')


    @staticmethod
    def process_search_request(args):
        """
        Process the search query and options, pass the processed search query to the VSCode
        Marketplace, and then display the results of the search query.

        Args:
            args (argparser.Namespace): input arguments sent to the SearchCommand
        """
        # build the query string
        query_string = ' '.join(args.query)
        sort_name, sort_num = SearchCommand._get_sort_query(args.sort_by)

        # If we couldn't reasonably fuzzy-match a sort column, log that
        # warning to the console and use the default sort column.
        if sort_num is None:
            _LOGGER.warning('"%s" did not match a known sort column.', args.sort_by)
            _LOGGER.debug('Available sort columns are: %s', ', '.join(_AVAILABLE_SORT_COLUMNS))
            _LOGGER.warning('Sorting by "%s"', _DEFAULT_SORT_BY_ARGUMENT_NAME)
            sort_by = _DEFAULT_SORT_BY_ARGUMENT
        else:
            _LOGGER.debug('Sorting by "%s"', sort_name)
            sort_by = sort_num

        # send the search query to the marketplace
        Command.tunnel.connect()
        search_results = Command.marketplace.search_extensions(search_text=query_string,
                                                               sort_by=sort_by,
                                                               page_size=args.limit)
        SearchCommand.show_search_results(search_results)


    def run(self, *args, **kwargs):
        """
        Implements the "search" command's functionality.
        """
        # Update the logger to apply the log-level from the main options
        self.apply_log_level(_LOGGER)

        # Create a new parser to parse the search command
        parser = self.get_command_parser()
        args, _ = parser.parse_known_args()

        # Remove the leading "search" command from the arguments
        args.query = args.query[1:]

        if args.query:
            SearchCommand.process_search_request(args)
        else:
            # If we received no search query, let the user know that we need one
            _LOGGER.error('The "search" command expects a query.')
            parser.print_usage()


#
# Create the SearchCommand instance
#
search_command = SearchCommand(name='search', aliases=['search', 'find', 's'])
