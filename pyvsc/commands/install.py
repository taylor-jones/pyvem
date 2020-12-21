"""Install command implementation"""

import logging

import configargparse
from fuzzywuzzy import process

from pyvsc._command import Command
from pyvsc._config import _PROG
from pyvsc._help import Help
from pyvsc._util import delimit
from pyvsc._editor import SupportedEditorCommands, get_editors
from pyvsc._extension import get_extension
from pyvsc._logging import get_rich_logger


_FUZZY_SORT_CONFIDENCE_THRESHOLD = 85
_AVAILABLE_EDITOR_KEYS = SupportedEditorCommands.keys()
_AVAILABLE_EDITOR_VALUES = SupportedEditorCommands.values()
_LOGGER = get_rich_logger(__name__)


_HELP = Help(
    name='install',
    brief='Install extension(s) or editor(s)',
    synopsis=f'{_PROG} install (with no args, installs any .vsix in the current directory)\n'
             f'{_PROG} install <editor>\n'
             f'{_PROG} install <publisher>.<package>\n'
             f'{_PROG} install <publisher>.<package>[[@<version>]]\n'
             f'{_PROG} install </path/to/*.vsix>\n'
             f'{_PROG} install </path/to/directory>\n\n'
             f'[h2]aliases[/]: {_PROG} i, {_PROG} add\n'
             '[h2]common options[/]: [[-s, --source EDITOR]] [[-t, --target EDITOR]]\n'
             '\t\t\t\t[[--insiders]] [[--exploration]] [[--codium]]',
    description='This command installs an extension as well as any extensions that it depends on. '
                'This command can also be used to install any of the supported code editors.'
                '\n\n'
                'One or more extensions may be provided to the install command, using a '
                f'space-delimited list [example](e.g. {_PROG} install <ext1> <ext2>)[/]'
                '\n\n'
                'Notice in the synopsis that an extension is specified by both its publisher name '
                'and package name. Together, these make up the extension\'s unique id, which '
                'helps identify it within the VSCode Marketplace.'
                '\n\n'
                f'If a local file-system path is provided, {_PROG} will attempt to install the '
                'extension(s) at the provided path. Otherwise, the `install` command involves '
                'making a remote request to the VSCode Marketplace to download the .vsix '
                'extension(s).'
)


class InstallCommand(Command):
    """
    The InstallCommand class defines the "install" command.
    """

    def __init__(self, name, aliases=None):
        self.system_editors = None
        super().__init__(name, _HELP, aliases=aliases or [])


    @staticmethod
    def _parse_editors_from_extensions(items):
        """
        Inspect a list of presumed code editors and/or extensions and
        separates them into two separate sets of items.

        Arguments:
            items {list} -- A list of editors and/or extensions, provided in
                the "install" command from the CLI

        Returns:
            editors, extensions -- Two sets of items -- a set of editors and a set of extensions.
        """
        editors = set()
        extensions = set()

        for item in items:
            # As a rule-of-thumb, we'll assume any item having a period in it's name is an
            # extension. It's possible that the user included a period in the name of an editor
            # they wish to install, but many extensions include names having patterns that would
            # otherwise match one of the editors if we don't assume periods are exclusive to
            # extension names.
            if '.' in item:
                extensions.add(item)
                continue

            # find the single best match from the list of known, supported
            # code editors (that matches above the specified threshold)
            try:
                match, _ = process.extractOne(query=item,
                                              choices=_AVAILABLE_EDITOR_VALUES,
                                              score_cutoff=_FUZZY_SORT_CONFIDENCE_THRESHOLD)

                # Get the corresponding key
                match = next(k for k in SupportedEditorCommands
                             if SupportedEditorCommands[k] == match)

            # If we couldn't find a match using the editor values themselves,
            # we'll check for a fuzzy match using the supported editor keys
            except TypeError:
                try:
                    match, _ = process.extractOne(query=item,
                                                  choices=_AVAILABLE_EDITOR_KEYS,
                                                  score_cutoff=_FUZZY_SORT_CONFIDENCE_THRESHOLD)
                # If we still couldn't find a match, then we'll assume this
                # list item represents an extension as opposed to an editor.
                except TypeError:
                    extensions.add(item)
                    continue

            # Add the match to the running set of matched editors
            editors.add(match)

        return editors, extensions


    def _get_dest_editors(self, target_arg=None):
        """
        Inspects the target/destination of the command argument to determine which VSCode-like
        editor(s) are the intended target install location for any extensions that are to be
        installed as a result of this command. In most cases, the user will probably only care to
        have one target editor, but this allows the opportunity for the user to specify multiple
        destination editors in a single command.

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
                match, _ = process.extractOne(query=target,
                                              choices=_AVAILABLE_EDITOR_VALUES,
                                              score_cutoff=_FUZZY_SORT_CONFIDENCE_THRESHOLD)

            # If we couldn't find a match using the editor values themselves,
            # we'll check for a fuzzy match using the supported editor keys
            except TypeError:
                try:
                    match, _ = process.extractOne(query=target,
                                                  choices=_AVAILABLE_EDITOR_KEYS,
                                                  score_cutoff=_FUZZY_SORT_CONFIDENCE_THRESHOLD)
                    match = SupportedEditorCommands[match]

                # If we still couldn't find a match, then we'll just move
                # on to the next item in the list of targets.
                except TypeError:
                    continue

            # Add the match to the running set of matched targets
            targets.add(match)
        return targets


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
            'extensions_or_editors',
            nargs='+',
            default=[],
            help='Extension id(s) or code editor(s) to install.'
        )

        parser.add_argument(
            '-s', '--source',
            default=None,
            metavar='EDITOR',
            type=str,
            help='A source editor from which to copy all extensions.'
        )

        parser.add_argument(
            '-t', '--target',
            nargs='+',
            default=[Command.main_options.target],
            metavar='EDITOR',
            type=str,
            help='The installation target editor(s).'
        )

        parser.add_argument(
            '--force',
            default=False,
            action='store_true',
            help='Force installation, even when already up-to-date.'
        )

        return parser


    def _validate_target_editors(self, requested_targets):
        """
        Check to make sure that each of the target editors is on the PATH.

        Arguments:
            requested_targets {set} -- set of requested editor names.
        """
        for req in requested_targets:
            target = self.system_editors[req]

            if not target.installed:
                _LOGGER.error('Cannot use destination editor "%s". It\'s either not installed '
                              'or not on the PATH.', target.editor_id)
                requested_targets.remove(req)
        return requested_targets


    def _install_editors(self, editors_to_install):
        """
        Install any requested editors. For each editor, check if it's already
        installed with the latest version.

        Arguments:
            editors_to_install {set} -- set of requested editor names.
        """
        remote_output = Command.main_options.remote_output_dir
        local_output = Command.main_options.output_dir

        for editor in editors_to_install:
            current_editor = self.system_editors[editor]

            if current_editor.can_update:
                downloaded_path = current_editor.download(remote_output, local_output)
                _LOGGER.info('Automated installation of editors isn\'t currently supported. Please'
                             ' install "%s" from "%s"', current_editor.editor_id, downloaded_path)
            else:
                _LOGGER.info('%s is already up-to-date.', current_editor.editor_id)


    def _install_extensions(self, target_editors, extensions):
        """
        Install any requested extensions.

        For each extension, download the extension, then install the extension
        to each of the target code editors.

        Arguments:
            target_editors {set} -- A set of the names of target editors.
            extensions {set} -- A set of extensions to download and install.
        """
        remote_output = Command.main_options.remote_output_dir
        local_output = Command.main_options.output_dir

        for req in extensions:
            ext = get_extension(req, tunnel=Command.tunnel)

            # get a list of any extension paths added as a result of downloading this extension.
            # This is a list an not a string, because the extension we download may have been an
            # extension pack or it may have dependencies. This means that mutliple downloads may
            # result from downloading this single extension. In that case, we'll need to install
            # each of the downloaded extensions.
            #
            # In the case that this is an extension with no dependencies, then we'll just
            # receive a list having one path in it.
            extension_paths = ext.download(remote_output, local_output)

            # Install the extension at each path to each of the target editors.
            for path in extension_paths:
                for editor_name in target_editors:
                    editor = self.system_editors[editor_name]
                    editor.install_extension(path)

                # add the extension to the list of temporary files to remove
                # once all processing has finished.
                self.store_temporary_file_path(path)


    def run(self, *args, **kwargs):
        """
        Implements the "install" command's functionality. Overrides the
        inherited run() method in the parent Command class.
        """
        # Update the logger to apply the log-level from the main options
        self.apply_log_level(_LOGGER)

        # build a parser that's specific to the 'install' command and parse the
        # 'install' command arguments.
        parser = self.get_command_parser()
        args, _ = parser.parse_known_args()

        # Remove the leading "install" command from the arguments
        args.extensions_or_editors = args.extensions_or_editors[1:]

        # Make sure we've gotten a request to install something
        if args.extensions_or_editors:
            editors_to_install = None
            extensions_to_install = None
            target_editors = None

            # A user may request to install code editors and/or extensions.
            # Separate the editors from the extensions, so we can process them differently.
            editors_to_install, extensions_to_install = \
                self._parse_editors_from_extensions(args.extensions_or_editors)

            if _LOGGER.isEnabledFor(logging.DEBUG):
                _LOGGER.debug('Editors to Install: %s', delimit(editors_to_install))
                _LOGGER.debug('Extensions to Install: %s', delimit(extensions_to_install))

            # If any extensions were requested for install, we'll also need to
            # determine where those extensions should be installed.
            if extensions_to_install:
                target_editors = self._get_dest_editors(args.target)

            # get a tunnel connection
            Command.tunnel.connect()

            # get a handle to the current system editors
            self.system_editors = get_editors(Command.tunnel)

            # make sure the output directory exists
            if not self.ensure_output_dirs_exist():
                _LOGGER.error('Could not ensure the existence of the required output directories.')

            # install any requested editors
            self._install_editors(editors_to_install)

            # validate any target editors
            if extensions_to_install:
                target_editors = self._validate_target_editors(target_editors)
                if _LOGGER.isEnabledFor(logging.DEBUG):
                    _LOGGER.debug('Target Editors: %s', delimit(target_editors))

                # install any requested extensions
                self._install_extensions(target_editors, extensions_to_install)
                return True
        else:
            _LOGGER.error('The "install" command expects 1 or more arguments.')
            parser.print_usage()


#
# Create the InstallCommand instance
#
install_command = InstallCommand(
    name='install',
    aliases=['install', 'i', 'add']
)
