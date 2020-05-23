from __future__ import print_function, absolute_import

import configargparse
from fuzzywuzzy import process
from beeprint import pp

from rich.console import Console
from rich.table import Table
from rich import box

from pyvsc._command import Command
from pyvsc._config import _PROG, rich_theme
from pyvsc._help import Help
from pyvsc._editor import SupportedEditorCommands, get_editors
from pyvsc._logging import get_rich_logger


_FUZZY_SORT_CONFIDENCE_THRESHOLD = 85
_AVAILABLE_EDITOR_KEYS = SupportedEditorCommands.keys()
_AVAILABLE_EDITOR_VALUES = SupportedEditorCommands.values()

_console = Console(theme=rich_theme)
_LOGGER = get_rich_logger(__name__, console=_console)

_HELP = Help(
    name='outdated',
    brief='Show extensions that can be updated',
    synopsis='{prog} outdated\n'
             '{prog} outdated [[<extension> ...]]\n'
             '{prog} outdated [[<extension> ...]] [[--<editor>]]\n'
             '{prog} outdated [[--<editor>]]\n'
             '{prog} outdated [[--editors]]\n'
             '{prog} outdated [[--all-editors]]\n\n'
             '[h2]aliases:[/h2] {prog} dated\n'.format(prog=_PROG),
    description='This command will check the VSCode Marketplace to see if '
                'any (or, specific) installed extensions have releases that '
                'are newer than the local versions.'
                '\n\n'
                'It also provides the ability to check if any (or, specific) '
                'supported code editors that have releases that are newer than '
                'the local versions.'
                '\n\n'
                'It will then print a list of results to stdout to indicate '
                'which extensions (and/or editors) have remote versions that '
                'are newer than the locally-installed versions.'
                '\n\n'
                'This command will not ever actually download or install '
                'anything. It\'s essentially a peek or dry-run to see what '
                'could be updated.',
    options='[h2]--<editor>[/]\n'
            '\t* Type: Code Editor {{{}}}\n'
            '\t* Default: code'
            '\n\n'
            'Sets the context for which Code Editor the outdated extensions '
            'check is for. If no extensions are specified, the '
            '[command]outdated[/] command will check all of the extensions '
            'installed to the specified Code Editor. If any extensions are '
            'specified, the [command]outdated[/] command will check for newer '
            'remote versions for only the specified extensions.'
            '\n\n'
            '[h2]--editors[/]\n'
            '\n'
            'If set, the [command]outdated[/] command will check for newer '
            'remote versions of Code Editors instead of extensions. This '
            'option will only check for newer versions of Code Editors that '
            'are currently installed.'
            '\n\n'
            '[h2]--all-editors[/]\n'
            '\n'
            'Similarly to [command]--editors[/], this option will check for '
            'newer remote versions of Code Editors instead of extensions. '
            'Unlike [command]--editors[/], this option will check for newer '
            'versions of all supported Code Editors, not just those that are '
            'currently installed.'.format('|'.join(_AVAILABLE_EDITOR_KEYS))
)


class OutdatedCommand(Command):
    """
    The OutdatedCommand class defines the "outdated" command. This class
    inherits from the base Command class.
    """
    def __init__(self, name, aliases=[]):
        super().__init__(name, _HELP, aliases=aliases)


    def get_command_parser(self, *args, **kwargs):
        """
        Builds and returns an argument parser that is specific to the
        "outdated" command.

        Returns:
            configargparse.ArgParser
        """
        parser_kwargs = {
            'add_help': False,
            'prog': '{} {}'.format(_PROG, self.name)
        }

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
            help='Extension id(s) to check for newer versions of.'
        )

        parser.add_argument(
            '--editors',
            default=False,
            action='store_true',
            help='Check if any installed Code editors have remote updates.'
        )

        parser.add_argument(
            '--all-editors',
            default=False,
            action='store_true',
            help='Check if any Code editors have remote updates.'
        )

        return parser


    def _get_dest_editors(self, target_arg=[]):
        """
        Inspects the target/destination of the command argument to determine
        which VSCode-like editor(s) are the intended target for which to check
        for outdated extensions.

        This function uses fuzzy matching with a pre-determined threshold to
        find matching code editor names that match enough to be considered the
        intended target editor destinations. The purpose of this is to allow a
        small amount of leeway in what target names the user provides and how
        the program interprets them.

        For instance, with a fuzzy-matching threshold of 85% (the default), a
        user could provide an intended target of 'code', 'vscode', 'vs.code',
        or 'vs-code', and each of those values would resolve to the base
        Visual Studio Code editor.

        In the event that the target editor is not able to be resolved to the
        name of a known, supported code editor, then no value is added to the
        set of resolved targets.

        Keyword Arguments:
            target_arg {list} -- A list of strings to compare against the names
            of known, supported code editors. (default: [])

        Returns:
            set -- A unique set of matching code editor names.
        """
        targets = set()
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
        for req in requested_targets:
            target = self.system_editors[req]
            id = target.editor_id

            if not target.installed:
                _LOGGER.error('Cannot inspect editor "{}". It\'s either not '
                              'installed or not on the PATH.'.format(id))
                requested_targets.remove(req)
        return requested_targets


    def _get_outdated_extensions_for_editor(self, editor_id, extensions=[]):
        """
        Queries the VSCode marketplace to check for newer versions of any of
        the extensions installed for a given code editor.

        Arguments:
            editor_id {str} -- The name of a supported editor.

        Returns:
            list -- A list of outdated extensions with the current version,
                latest version, and last updated date.
        """
        editor = self.system_editors[editor_id]
        outdated = []

        # if no extensions were specified, check for updates to all of the
        # extensions for the current editor. Otherwise, just check for updates
        # to the specified extensions.
        all_extensions = editor.get_extensions()
        extensions_to_check = (
            all_extensions if not extensions
            else [x for x in all_extensions if x['unique_id'] in extensions])

        # Send a warning for any extensions that were specified but arent
        # installed to the current editor.
        for x in extensions:
            if x not in extensions_to_check:
                _LOGGER.warning('{} is not installed to {}'.format(
                    x, editor['editor_id']))

        # Check each of the determined extensions for newer remote versions
        # in the VSCode Marketplace.
        for extension in extensions_to_check:
            uid = extension['unique_id']
            _LOGGER.info('Checking extension: {}'.format(uid))

            installed_version = extension['version']
            response = Command.marketplace.get_extension_latest_version(
                uid, editor.get_engine())

            last_updated = response['lastUpdated']
            latest_version = response['versions'][0]['version']

            if latest_version > installed_version:
                extension['latest'] = latest_version
                extension['last_updated'] = last_updated
                outdated.append(extension)

        return outdated


    def _get_outdated_extensions_for_editors(self, editor_ids, extensions=[]):
        """
        Iterates over each of the target editors, inspects each of the
        extensions for that editor, then prints a rich table showing a list
        of outdated extensions for that editor.

        Arguments:
            editor_ids {list} -- A list of supported editor ids.
        """
        for id in editor_ids:
            table = Table(box=box.SQUARE, title=id, title_style='bold magenta')
            table.add_column('Extension ID', justify='left', no_wrap=True)
            table.add_column('Installed', justify='right', no_wrap=True)
            table.add_column('Latest', justify='right', no_wrap=True)
            table.add_column('Last Update', justify='right', no_wrap=True)

            outdated_extensions = \
                self._get_outdated_extensions_for_editor(id, extensions)

            if outdated_extensions:
                for ext in outdated_extensions:
                    table.add_row(
                        ext['unique_id'],
                        ext['version'],
                        ext['latest'],
                        ext['last_updated'])

                _console.print(table)
            else:
                _LOGGER.info('All installed extensions are up to date!')


    def _get_outdated_editors(self, show_non_installed=False):
        """
        Prints the Code editors that can be updated.

        Keyword Arguments:
            show_non_installed {bool} -- If true, this will also print
            code editors that are not installed. (default: {False})
        """
        outdated = []
        for editor in self.system_editors.values():
            if editor.can_update and (show_non_installed or editor.installed):
                outdated.append((
                    editor.editor_id,
                    editor.version or '---',
                    editor.latest_version))

        if outdated:
            # print the rich table of any outdated editors
            table = Table(box=box.SQUARE)
            table.add_column('Editor', justify='left', no_wrap=True)
            table.add_column('Installed', justify='right', no_wrap=True)
            table.add_column('Latest', justify='right', no_wrap=True)

            for i in outdated:
                table.add_row(*i)
            _console.print(table)


    def run(self, *args, **kwargs):
        # Update the logger to apply the log-level from the main options
        self.apply_log_level(_LOGGER)

        # build a parser that's specific to the 'outdated' command and parse
        # the 'outdated' command arguments.
        parser = self.get_command_parser()
        args, remainder = parser.parse_known_args()
        args.target = [Command.main_options.target]

        # Remove the leading "outdated" command from the arguments
        args.extensions = args.extensions[1:]

        # get a handle to the current system editors
        self.system_editors = get_editors(Command.tunnel)

        # Determine the target editors and validate that they're installed
        target_editors = self._get_dest_editors(args.target)
        target_editors = self._validate_target_editors(target_editors)

        # get a tunnel connection
        Command.tunnel.connect()

        # check for the flag indicating to check all editors but ONLY editors
        if args.editors or args.all_editors:
            self._get_outdated_editors(args.all_editors)
        else:
            # Get the outdated extensions
            self._get_outdated_extensions_for_editors(
                target_editors, args.extensions)


#
# Create the OutdatedCommand instance
#
outdated_command = OutdatedCommand(
    name='outdated',
    aliases=['outdated', 'dated']
)
