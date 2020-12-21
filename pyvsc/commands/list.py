"""List command implementation"""

import configargparse
from fuzzywuzzy import process

from rich.console import Console
from rich.table import Table
from rich import box

from pyvsc._command import Command
from pyvsc._config import _PROG, rich_theme
from pyvsc._editor import SupportedEditorCommands, get_editors
from pyvsc._help import Help
from pyvsc._logging import get_rich_logger


_FUZZY_SORT_CONFIDENCE_THRESHOLD = 85
_AVAILABLE_EDITOR_KEYS = SupportedEditorCommands.keys()
_AVAILABLE_EDITOR_VALUES = SupportedEditorCommands.values()

_console = Console(theme=rich_theme)
_LOGGER = get_rich_logger(__name__)
_HELP = Help(
    name='list',
    brief='List installed extension(s)',
    synopsis=f'{_PROG} list (with no args, show all installed extensions\n'
             '\t\t  for all installed, supported code editors) \n'
             f'{_PROG} list [[<extension>]]\n'
             f'{_PROG} list [[--<editor>]]\n\n'
             f'[h2]aliases[/]: {_PROG} ls, {_PROG} ll, {_PROG} la',
    description='This command will print to stdout all of the versions of extensions that are '
                'installed. If an editor name is provided, the output will be scoped to only '
                'print the versions of extensions installed to that particular editor.'
)


class ListCommand(Command):
    """
    The ListCommand class defines the "list" command. This class
    inherits from the base Command class.
    """

    def __init__(self, name, aliases=None):
        self.system_editors = None
        super().__init__(name, _HELP, aliases=aliases or [])


    def get_command_parser(self, *args, **kwargs):
        """
        provides a parser for the `list` command.
        """
        parser_kwargs = {'add_help': False, 'prog': '{} {}'.format(_PROG, self.name)}
        parser = configargparse.ArgumentParser(**parser_kwargs)

        parser.add_argument(
            '--help',
            action='help',
            help='Show help.'
        )

        parser.add_argument(
            'extensions',
            nargs='+',
            default=[],
            help='Extension id(s) to list information about.'
        )

        parser.add_argument(
            '--code',
            default=False,
            action='store_true',
            help='List VSCode extensions.'
        )

        parser.add_argument(
            '--codium',
            default=False,
            action='store_true',
            help='List VSCodium extensions.'
        )

        parser.add_argument(
            '--insiders',
            default=False,
            action='store_true',
            help='List VSCode Insiders extensions.'
        )

        parser.add_argument(
            '--all',
            default=False,
            action='store_true',
            help='List extensions for all installed code editors.'
        )

        return parser


    def _get_target_editors(self, target_arg=None):
        """
        Inspects the target/destination of the command argument to determine which VSCode-like
        editor(s) are the intended target for which to check for outdated extensions.

        This function uses fuzzy matching with a pre-determined threshold to find matching code
        editor names that match enough to be considered the intended target editor destinations.
        The purpose of this is to allow a small amount of leeway in what target names the user
        provides and how the program interprets them.

        For instance, with a fuzzy-matching threshold of 85% (the default), a user could provide
        an intended target of 'code', 'vscode', 'vs.code', or 'vs-code', and each of those values
        would resolve to the base Visual Studio Code editor.

        In the event that the target editor is not able to be resolved to the name of a known,
        supported code editor, then no value is added to the set of resolved targets.

        Keyword Arguments:
            target_arg {list} -- A list of strings to compare against the names
            of known, supported code editors. (default: [])

        Returns:
            set -- A unique set of matching code editor names.
        """
        targets = set()
        target_arg = target_arg or []
        for target in target_arg:
            # find the single best match from the list of known, supported
            # code editors (that matches above the specified threshold)
            try:
                match, _ = process.extractOne(
                    query=target,
                    choices=_AVAILABLE_EDITOR_VALUES,
                    score_cutoff=_FUZZY_SORT_CONFIDENCE_THRESHOLD)

                # We don't want the value in this instance, we want the key,
                # so find the key that's associated with the value match.
                match = list(SupportedEditorCommands.keys())[
                    list(SupportedEditorCommands.values()).index(match)]

            # If we couldn't find a match using the editor values themselves,
            # we'll check for a fuzzy match using the supported editor keys
            except TypeError:
                try:
                    match, _ = process.extractOne(
                        query=target,
                        choices=_AVAILABLE_EDITOR_KEYS,
                        score_cutoff=_FUZZY_SORT_CONFIDENCE_THRESHOLD)

                # If we still couldn't find a match, then we'll just move
                # on to the next item in the list of targets.
                except TypeError:
                    continue

            # Add the match to the running set of matched targets
            targets.add(match)
        return targets


    def _validate_target_editors(self, requested_targets):
        """
        Check to make sure that each of the target editors is on the PATH.

        Arguments:
            requested_targets {set} -- set of requested editor names.
        """
        valid_targets = set()

        for requested_target in requested_targets:
            target = self.system_editors[requested_target]

            if not target.installed:
                _LOGGER.warning('Cannot inspect editor "%s". It\'s either not installed or not '
                                'on the PATH.', target.editor_id)
            else:
                valid_targets.add(requested_target)

        return valid_targets



    def _get_extensions_for_editor(self, editor_id, extensions=None):
        """
        Retrieves information about installed extensions for the specified editor,
        optionally limiting the information to only a subset of installed extensions.

        Arguments:
            editor_id {str} -- The name of a supported editor.

        Returns:
            list -- A list of installed extensions
        """
        editor = self.system_editors[editor_id]
        editor_name = editor['editor_id']

        # if no extensions were specified, check for updates to all of the
        # extensions for the current editor. Otherwise, just check for updates
        # to the specified extensions.
        all_extensions = editor.get_extensions()
        extensions_to_list = (all_extensions if not extensions
                              else [x for x in all_extensions if x['unique_id'] in extensions])

        table = Table(box=box.SQUARE, title=editor_name, title_style='bold magenta')
        table.add_column('Extension ID', justify='left', no_wrap=True)
        table.add_column('Publisher', justify='left', no_wrap=True)
        table.add_column('Package', justify='left', no_wrap=True)
        table.add_column('Version', justify='right', no_wrap=True)

        for extension in extensions_to_list:
            table.add_row(extension['unique_id'],
                          extension['publisher'],
                          extension['package'],
                          extension['version'])

        _console.print(table)



    def run(self, *args, **kwargs):
        # Update the logger to apply the log-level from the main options
        self.apply_log_level(_LOGGER)

        # build a parser that's specific to the 'list' command and parse
        # the 'list' command arguments.
        parser = self.get_command_parser()
        args, _ = parser.parse_known_args()
        args.target = [Command.main_options.target]

        # Remove the leading "list" command from the arguments
        args.extensions = args.extensions[1:]

        # get a handle to the current system editors
        self.system_editors = get_editors(Command.tunnel)

        # Determine the target editors and validate that they're installed
        if (args.all):
            target_editors = set(list(SupportedEditorCommands.keys()))
        else:
            target_editors = self._get_target_editors(args.target)
        valid_editors = self._validate_target_editors(target_editors)

        for editor in valid_editors:
            self._get_extensions_for_editor(editor)


#
# Create the ListCommand instance
#
list_command = ListCommand(
    name='list',
    aliases=['list', 'ls', 'll', 'la']
)
