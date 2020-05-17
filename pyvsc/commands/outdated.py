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
from pyvsc._extension import get_extension
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
             ''.format(prog=_PROG),
    description='This command will check the VSCode Marketplace to see if '
                'any (or, specific) installed extensions are currently '
                'outdated.'
                '\n\n'
                'It will also check if any (or, specific) installed code '
                'editors are currently outdated.'
                '\n\n'
                'It will then print a list of results to stdout to indicate '
                'which extensions (and/or editors) have remote versions that '
                'are newer than the locally-installed versions.'
                '\n\n'
                'This command will not ever actually download or install '
                'anything. It\'s essentially a peek or dry-run to see what '
                'could be updated. '
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
        Builds and returns an argument parser that is specific to the "install"
        command.

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


    def _get_installed_editors(self):
        # return {v for k, v in self.system_editors if v.installed}
        # return self.system_editors.values()
        # TODO:


    def _get_outdated_extensions_for_editor(self, editor_id):
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

        for extension in editor.get_extensions():
            uid = extension['unique_id']
            _LOGGER.info('Checking {}...'.format(uid))

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


    def _get_outdated_extensions_for_editors(self, editor_ids):
        """
        Iterates over each of the target editors, inspects each of the
        extensions for that editor, then prints a rich table showing a list
        of outdated extensions for that editor.

        Arguments:
            editor_ids {list} -- A list of supported editor ids.
        """
        for id in editor_ids:
            table = Table(box=box.SQUARE, title=id)
            table.add_column('Extension ID', justify='left', no_wrap=True)
            table.add_column('Installed', justify='right', no_wrap=True)
            table.add_column('Latest', justify='right', no_wrap=True)
            table.add_column('Last Update', justify='right', no_wrap=True)

            outdated_extensions = self._get_outdated_extensions_for_editor(id)
            if outdated_extensions:
                for ext in outdated_extensions:
                    table.add_row(
                        ext['unique_id'],
                        ext['version'],
                        ext['latest'],
                        ext['last_updated'],
                    )

                _console.print(table)
            else:
                _LOGGER.info('All extensions are up to date!')


    def _get_outdated_editors(self, installed_editors):
        pp(installed_editors)



    def run(self, *args, **kwargs):
        # build a parser that's specific to the 'outdated' command and parse
        # the 'outdated' command arguments.
        parser = self.get_command_parser()
        args, remainder = parser.parse_known_args()
        args.target = [Command.main_options.target]

        # Remove the leading "outdated" command from the arguments
        args.extensions_or_editors = args.extensions[1:]

        # get a handle to the current system editors
        self.system_editors = get_editors(Command.tunnel)

        # Determine the target editors and validate that they're installed
        target_editors = self._get_dest_editors(args.target)
        target_editors = self._validate_target_editors(target_editors)

        # get a tunnel connection
        Command.tunnel.connect()

        # check for the flag indicating to check all editors but ONLY editors
        if args.editors:
            installed_editors = self._get_installed_editors()
            self._get_outdated_editors(installed_editors)
        else:
            # Get the outdated extensions
            self._get_outdated_extensions_for_editors(target_editors)

        # Print the results in a rich table



        # pp(args)
        # pp(remainder)
        # pp(Command.main_options)
        # pp(target_editors)



        # # check for the flag indicating to check all editors but ONLY editors
        # if args.editors:
        #     installed_editors = self._get_installed_editors(system_editors)

        # check for the target editors


        # check if any extensions were specified
        extensions = args.extensions


#
# Create the OutdatedCommand instance
#
outdated_command = OutdatedCommand(
    name='outdated',
    aliases=['outdated']
)
