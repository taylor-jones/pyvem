from __future__ import print_function, absolute_import

import configargparse
from fuzzywuzzy import process
from beeprint import pp

from pyvsc._command import Command
from pyvsc._config import _PROG
from pyvsc._help import Help
from pyvsc._util import props
from pyvsc._editor import SupportedEditorCommands, get_editors

_FUZZY_SORT_CONFIDENCE_THRESHOLD = 85
_AVAILABLE_EDITOR_KEYS = SupportedEditorCommands.keys()
_AVAILABLE_EDITOR_VALUES = SupportedEditorCommands.values()

_HELP = Help(
    name='install',
    brief='Install extension(s) or editor(s)',
    synopsis='{prog} install (with no args, installs any .vsix in the current '
             'directory)\n'
             '{prog} install <editor>\n'
             '{prog} install <publisher>.<package>\n'
             '{prog} install <publisher>.<package>[[@<version>]]\n'
             '{prog} install </path/to/*.vsix>\n'
             '{prog} install </path/to/directory>\n\n'
             '[h2]aliases[/]: {prog} i, {prog} add\n'
             '[h2]common options[/]: '
             '[[-s, --source EDITOR]] '
             '[[-t, --target EDITOR]]\n'
             '\t\t\t\t[[--insiders]] '
             '[[--exploration]] '
             '[[--codium]] '
             ''.format(prog=_PROG),
    description='This command installs an extension as well as any extensions '
                'that it depends on. This command can also be used to install '
                'any of the supported code editors.'
                '\n\n'
                'One or more extensions may be provided to the install '
                'command, using a space-delimited list [example](e.g. {prog} '
                'install <ext1> <ext2>)[/]'
                '\n\n'
                'Notice in the synopsis that an extension is specified by '
                'both its publisher name and package name. Together, these '
                'make up the extension\'s unique id, which helps identify it '
                'within the VSCode Marketplace.'
                '\n\n'
                'If a local file-system path is provided, {prog} will attempt '
                'to install the extension(s) at the provided path. Otherwise, '
                'the `install` command involves making a remote request to '
                'the VSCode Marketplace to download the .vsix extension(s).'
                ''.format(prog=_PROG)
)


class InstallCommand(Command):
    def __init__(self, name, aliases=[]):
        super().__init__(name, _HELP, aliases=aliases)


    def _parse_editors_from_extensions(self, items):
        """
        Inspect a list of presumed code editors and/or extensions and
        separates them into two separate sets of items.

        Arguments:
            items {list} -- A list of editors and/or extensions, provided in
            the "install" command from the CLI

        Returns:
            editors, extensions -- Two sets of items -- a set of editors and
            a set of extensions.
        """
        editors = set()
        extensions = set()

        for item in items:
            # find the single best match from the list of known, supported
            # code editors (that matches above the specified threshold)
            try:
                match, _ = process.extractOne(
                    item,
                    choices=_AVAILABLE_EDITOR_VALUES,
                    score_cutoff=_FUZZY_SORT_CONFIDENCE_THRESHOLD)

                # Get the corresponding key
                match = next(k for k in SupportedEditorCommands
                             if SupportedEditorCommands[k] == match)

            # If we couldn't find a match using the editor values themselves,
            # we'll check for a fuzzy match using the supported editor keys
            except TypeError:
                try:
                    match, _ = process.extractOne(
                        item,
                        choices=_AVAILABLE_EDITOR_KEYS,
                        score_cutoff=_FUZZY_SORT_CONFIDENCE_THRESHOLD)

                # If we still couldn't find a match, then we'll assume this
                # list item represents an extension as opposed to an editor.
                except TypeError:
                    extensions.add(item)
                    continue

            # Add the match to the running set of matched editors
            editors.add(match)

        editors = editors if bool(editors) else None
        extensions = extensions if bool(extensions) else None
        return editors, extensions


    def _get_dest_editors(self, target_arg=[]):
        """
        Inspects the target/destination of the command argument to determine
        which VSCode-like editor(s) are the intended target install location
        for any extensions that should are to be installed as a result of this
        command. In most cases, the user will probably only care to have one
        target editor, but this allows the opportunity for the user to specify
        multiple destination editors in a single command.

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
                    target,
                    choices=_AVAILABLE_EDITOR_VALUES,
                    score_cutoff=_FUZZY_SORT_CONFIDENCE_THRESHOLD)

            # If we couldn't find a match using the editor values themselves,
            # we'll check for a fuzzy match using the supported editor keys
            except TypeError:
                try:
                    match, _ = process.extractOne(
                        target,
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


    def run(self, *args, **kwargs):
        """
        Implements the "install" command's functionality. Overrides the
        inherited run() method in the parent Command class.
        """
        # build a parser that's specific to the 'install' command and parse the
        # 'install' command arguments.
        parser = self.get_command_parser()
        args = parser.parse_args()

        # Remove the leading "install" command from the arguments
        args.extensions_or_editors = args.extensions_or_editors[1:]

        # Make sure we've gotten a request to install something
        if args.extensions_or_editors:
            requested_editors = None
            requested_extensions = None
            requested_dest_editors = None

            # pp(vars(args))
            # pp(vars(Command.main_options))

            # A user may request to install code editors and/or extensions.
            # Separate the editors from the extensions, so we can process them
            # differently.
            requested_editors, requested_extensions = \
                self._parse_editors_from_extensions(args.extensions_or_editors)

            # If any extensions were requested for install, we'll also need to
            # determine where those extensions should be installed.
            if requested_extensions:
                requested_dest_editors = self._get_dest_editors(args.target)

            # pp(requested_editors)
            # pp(requested_extensions)
            # pp(requested_dest_editors)

            #
            # Now we know all the components that should be installed.
            #

            # get a tunnel connection
            Command.tunnel.connect()

            # get a handle to the current system editors
            editors = get_editors(Command.tunnel)
            pp(editors)

            remote_output_dir = Command.main_options.remote_output_dir
            local_output_dir = Command.main_options.output_dir

            # make sure the output directory exists
            if not self.ensure_output_dirs_exist():
                self.log.error('Could not ensure the existence of the '
                               'required output directories.')

            # First, install any editors. Check if the desired editors are
            # already installed with the latest version.
            for e in requested_editors:
                current_editor = editors[e]
                id = current_editor.editor_id

                if current_editor.can_update:
                    downloaded_path = current_editor.download(
                        remote_output_dir, local_output_dir)
                    self.store_temporary_file_path(downloaded_path)
                else:
                    self.log.info('{} is already up-to-date.'.format(id))

            # After installing the editors, we'll need to inspect the target
            # destination editors to ensure they're available on the PATH.
            #
            # The reason this should be done after installing the editors is
            # because the user may want to install extensions to an editor that
            # was not installed prior to running the "install" command.
            for e in requested_dest_editors:
                current_editor = editors[e]
                id = current_editor.editor_id
                if not current_editor.installed:
                    self.log.error('Can use destination editor "{}". It\'s '
                                   'either not installed or not on the PATH.'
                                   ''.format(id))

            # Then, install eny extensions.
            # TODO: Figure out which extensions are not already the latest.

        else:
            self.log.error('The "install" command expects 1 or more arguments.')
            parser.print_usage()


install_command = InstallCommand(
    name='install',
    aliases=['install', 'i', 'add']
)
