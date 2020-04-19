"""
Download and install the latest versions of 
VSCode extensions with cURL over a remote network.
"""

from __future__ import print_function

import os
import sys
import re
import platform
import logging
import configargparse
import coloredlogs

from time import time
from shutil import rmtree
from getpass import getuser
from pyvsc._tunnel import Tunnel


# TODO: Figure out how to change log formatting based on the verbosity level

LOGGER = logging.getLogger(__name__)
# logging.basicConfig(
#     level=logging.INFO,
#     format='%(asctime)s [%(levelname)s]\t%(module)s::%(funcName)s:%(lineno)d | %(message)s'
# )
coloredlogs.install(
    level='DEBUG',
    logger=LOGGER,
    fmt='%(asctime)s,%(msecs)03d %(name)s %(levelname)s %(message)s'
)


class Editors:
    """
    These represent the valid CLI interpreters for the different versions of
    supported VSCode editor variations.

    See:
    - https://code.visualstudio.com/docs/editor/command-line#_working-with-extensions
    - https://github.com/VSCodium/vscodium
    """
    code = 'code'
    codium = 'codium'
    insiders = 'code-insiders'


class ExtensionManager():
    def __init__(self, **kwargs):
        self.tunnel = kwargs.get('tunnel', None)
        self.dry_run = kwargs.get('dry_run', False)
        self.keep = kwargs.get('keep', False)
        self.extensions_dir = None

        # FIXME: Be more consistent with the option validations.
        # Some of them happen here, some happen in main().

        # determine which version of the editor to work with, and make
        # sure that version is installed and on the PATH
        self.insiders = kwargs.get('insiders', False)
        self.codium = kwargs.get('codium', False)

        # if either insiders or codium was explicitely specified, use that
        # editor for both the source and destination editors. Otherwise,
        # inspect both the source and destination editors individually to
        # determine which Code editors to use.
        if self.insiders:
            self.cmd_source = Editors.insiders
            self.cmd_dest = Editors.insiders
        elif self.codium:
            self.cmd_source = Editors.codium
            self.cmd_dest = Editors.codium
        else:
            self.cmd_source = self._get_editor_command(
                kwargs.get('source_editor'), Editors.code)
            self.cmd_dest = self._get_editor_command(
                kwargs.get('dest_editor'), Editors.code)

        # ensure the source & destination editors are installed on the system
        self._check_editors_are_installed([self.cmd_source, self.cmd_dest])

        # determine the output directory and specified extensions
        self.output = self._process_output_directory(kwargs.get('output_dir'))
        self.extensions = self._process_extensions(kwargs.get('extensions'))


    def _get_editor_command(self, command, default=None):
        """
        Parse a string to determine if a specific version of VS Code is present

        Arguments:
            command {str} -- the content to inspect

        Returns:
            {str|None} -- the editor command associated with the input,
                if found. Otherwise, the default value.
        """
        command = command.lower()

        if command in ['code-insiders', 'insiders', 'vscode-insiders']:
            return Editors.insiders
        elif command in ['codium', 'vscodium', 'vs-codium']:
            return Editors.codium
        elif command in ['code', 'vscode', 'vs-code']:
            return Editors.code
        return default


    def _check_editors_are_installed(self, editors):
        """
        Checks if the specified version of VS Code is installed.
        Raises an error if not.

        Arguments:
            editors {list} -- a list of {1,2} Code editors to validate the
                installation of.

        Returns:
            bool -- True, unless an exception is raised.
        """
        for editor in editors:
            try:
                self.version = os.popen('%s --version' % (
                editor)).read().splitlines()[0]
                return True
            except RuntimeError as e:
                LOGGER.error('The command "%s" is not on your path. Please ' \
                'make sure the correct version of VS Code is installed ' \
                'before running this program.' % (editor))
                sys.exit(1)


    def _get_valid_dir(self, directory, create_if_not_exists=False):
        """
        Attempts to validate a relative or absolute directory path. If a valid
        path is determined, the valid path is returned. If no valid directory
        path is able to be determined, None is returned.

        Arguments:
            directory {str} -- The path to a directory on the file system.

        Keyword Arguments:
            create_if_not_exists {bool} -- If True (and the directory does not
                yet exist) a directory will be created at the specified path
                (default: {False})

        Returns:
            {str|None}
        """
        d = os.path.expanduser(directory)
        d = os.path.abspath(d)
        dir_exists = os.path.isdir(d)

        # if we're only checking on the existence of the directory, then don't
        # try to create it and only return the dir path if it already existed.
        if not create_if_not_exists or self.dry_run == True:
            return d if dir_exists else None

        # otherwise, try to create the directory, and return the
        # absolute path if creation was successful.
        try:
            self._output_preexisted = dir_exists
            command = 'mkdir -p %s' % (d)
            os.system(command)
            self.tunnel.run(command)
            return d
        except Exception as e:
            LOGGER.error(
                'Could not validate directory: %s' % (d), 
                exc_info=self.verbose)
            sys.exit(1)


    def _get_directory_vsix_files(self, directory):
        """
        Returns a list of .vsix files from a specified directory
        
        Arguments:
            directory {str} -- The path to a directory in the file system.
        
        Returns:
            list -- A list of .vsix files in the directory.
        """
        return [f for f in os.listdir(directory) if f.endswith('.vsix')]


    def _get_vscode_url(self):
        """
        Returns a URL that can be used to download the latest version of
        the specified VS Code editor.
        """
        operating_system = platform.system()
        version = 'insider' if self.insiders else 'stable'
        url_base = 'https://update.code.visualstudio.com/latest'

        if operating_system == 'Linux':
            return '%s/linux-rpm-x64/%s' % (url_base, version)
        elif operating_system == 'Darwin':
            return '%s/darwin/%s' % (url_base, version)

        # Otherwise, it's an operating system that isn't currently supported
        LOGGER.error('Sorry, pyvsc doesn\'t currently support %s' % (
            operating_system), exc_info=self.verbose)
        sys.exit(1)


    def _get_vscode_curl_command(self, url):
        """
        Returns a cURL formatted command that can be executed
        to download the VS Code editor.
        """
        return 'cd %s && curl %s -O' % (self.output, url)


    def _get_vsix_curl_command(self, extension, url):
        """
        Returns a cURL command that can be used to download a specified
        VSCode extension, given the extension name and URL.
        """
        return 'curl %s -o %s/%s.vsix' % (url, self.output, extension)


    def _get_vsix_url(self, extension):
        """
        Builds the URL for a .vsix vscode extension, given the full 
        name of the extension in the format of {publisher}.{package}

        ex: ms-python.python

        Arguments:
            extension {str} -- the name of the extension

        Returns:
            {str}
        """
        publisher, package = extension.split('.')
        return 'https://%s.gallery.vsassets.io/_apis/public/gallery' \
            '/publisher/%s/extension/%s/latest/assetbyname' \
            '/Microsoft.VisualStudio.Services.VSIXPackage' % (
              publisher, publisher, package)

    # https://twxs.gallerycdn.vsassets.io/extensions/twxs/cmake/0.0.17/1488841920286/Microsoft.VisualStudio.Services.VSIXPackage
    # https://twxs.gallery.vsassets.io/_apis/public/gallery/publisher/twxs/extension/cmake/latest/assetbyname/Microsoft.VisualStudio.Services.VSIXPackage

    def cleanup_output_dir(self):
        """
        Removes downloaded extension files from the output directory, or if 
        the output directory wasn't pre-existing, removes the entire directory.

        If the output directory was pre-existing, we don't want to remove it
        (since there might be other content in there that the user does not
        want to remove), so we'll make sure to only remove the files associated
        with the extensions we've downloaded.
        
        If the output directory was not pre-existing (meaning we created it
        for the purpose of executing pyvsc), then we'll just remove the entire
        directory.
        """
        LOGGER.info('Cleaning up downloaded extensions.')

        if self._output_preexisted == True:
            for ext in self.extensions:
                try:
                    ext_name = '%s/%s.vsix' % (self.output, ext)
                    os.system('rm -f %s' % (ext_name))
                    LOGGER.debug('Removed file: %s' % (ext_name))
                except Exception as e:
                    LOGGER.error(
                        'Failed to remove file: %s' % (ext_name),
                        exc_info=self.verbose)
        else:
            try:
                rmtree(self.output)
                LOGGER.debug('Removed directory: %s' % (self.output))
            except IOError as e:
                LOGGER.error(
                    'Failed to remove directory: %s' % (self.output),
                    exc_info=self.verbose)


    def download(self):
        """
        Downloads all specified extensions over SSH and places them into
        the directory specified by the configuration options.
        """
        if self.extensions == None:
            LOGGER.error(
                'No extensions have been specified.', exc_info=self.verbose)
            sys.exit(1)

        if self.output == None:
            LOGGER.error(
                'No output directory has been specified.',
                exc_info=self.verbose)
            sys.exit(1)

        LOGGER.info('Downloading %d extensions to %s' % (
            len(self.extensions), self.output))

        # download each extension to the output directory in the ssh tunnel.
        for extension in self.extensions:
            download_url = self._get_vsix_url(extension)
            curl_command = self._get_vsix_curl_command(extension, download_url)
            LOGGER.info('Downloading extension: %s' % (extension))

            # download the extension via the SSH tunnel
            self.tunnel.run(curl_command)

            # transfer the extension from the remote host to the local host
            ext_name = '%s/%s.vsix' % (self.output, extension)
            LOGGER.debug('Transferring %s from remote' % (ext_name))
            self.tunnel.get(ext_name, ext_name)

            # delete the extension from the remote host
            LOGGER.debug('Deleting %s from remote' % (ext_name))
            self.tunnel.run('rm -f %s' % (ext_name))

        # delete the remote directory
        self.tunnel.rmdir(self.output)


    def _install_extension(self, path):
        """
        Installs an individual VSIX extensions at a specified path.
        """
        try:
            extension_name = os.path.basename(path)
            LOGGER.info('Installing %s' % (extension_name))
            os.system('%s --install-extension %s --force' % (self.cmd_dest, path))
        except Exception as e:
            LOGGER.error(
                'Failed to install extension: %s' % (extension_name),
                exc_info=self.verbose)


    def install(self, extension_path=None):
        """
        Installs the extension at the specified path or all the
        extensions in the specified directory.
        """
        # if no extension_path was provided, assume we want to install the
        # extensions from the output directory.
        extension_path = extension_path or self.extensions_dir

        if os.path.isfile(extension_path):
            self._install_extension(extension_path)
        elif os.path.isdir(extension_path):
            for f in os.listdir(extension_path):
                self._install_extension('%s/%s' % (extension_path, f))
        else:
            LOGGER.error('Cannot install extension(s) from the path "%s".' % (
                extension_path), exc_info=self.verbose)
            sys.exit(1)


    def update(self):
        """
        Downloads the latest versions of all specified extensions
        to the output directory, and then passes the output directory
        as the source for extensions that should be installed.
        """
        self.download()
        self.install(self.output)


    def _process_output_directory(self, directory):
        """
        Resolves an absolute path to the specified extension output directory.
        
        Arguments:
            directory {str} -- The path to the output directory.
        
        Returns:
            str -- The absolute path to the output directory.
        """
        return self._get_valid_dir(directory, True)


    def _process_extensions(self, extensions):
        """
        Parses the extensions argument to determine which extensions should be
        processed.
        
        Arguments:
            extensions {str|list|None} -- The argued extension names to involve
        
        Returns:
            list -- A list of extension names that will be processed
        """
        # if the user did not specify any extensions, we'll assume that they
        # want to update all of their currently-installed extensions.
        if extensions is None or extensions == '':
            LOGGER.debug('Processing extensions from %s.' % (self.cmd_source))
            extensions = os.popen('%s --list-extensions' % (self.cmd_source)
            ).read().splitlines()

        # otherwise, if we were given a string of one or more extensions,
        # we need to determine if we were given a path to a directory of
        # extensions or a list of extension names.
        elif type(extensions) is str:
            # check if we were given a valid directory path
            directory = self._get_valid_dir(extensions)

            # if a valid directory was provided, then get a list of all the
            # extensions in the directory.
            if directory is not None:
                self.extensions_dir = directory
                extensions = self._get_directory_vsix_files(directory)

            # If a literal string of extension names was provided, convert the
            # string to a list of extensions.
            else:
                extensions = re.split(';|,', extensions)

        # make sure we're dealing with a list
        try:
            extensions = list(extensions)
            return extensions
        except TypeError as e:
            LOGGER.error(
                'Could not identify a list of extensions.',
                exc_info=self.verbose)
            sys.exit(1)



class CustomFormatter(configargparse.HelpFormatter):
    def _format_action_invocation(self, action):
        if not action.option_strings:
            metavar, = self._metavar_formatter(action, action.dest)(1)
            return metavar
        else:
            parts = []
            # if the Optional doesn't take a value, format is:
            #    -s, --long
            if action.nargs == 0:
                parts.extend(action.option_strings)

            # if the Optional takes a value, format is:
            #    -s ARGS, --long ARGS
            # change to 
            #    -s, --long ARGS
            else:
                default = action.dest.upper()
                args_string = self._format_args(action, default)
                for option_string in action.option_strings:
                    parts.append('%s' % (option_string))
                parts[-1] += ' %s'%args_string

            return ', '.join(parts)



def validate_options(parser):
    """
    Validates the configuration options and returns the valid options.
    
    Arguments:
        parser {configargparse.ArgParser} -- The configuration options as
            specified from the command line and/or a configuration file.

    Returns:
        dict, unless the configuration options were found to be invalid,
            in which case an error is logged, and the program exits.
    """
    # TODO: Migrate code editor validations (and all the validations in this)
    # function into a better-structured class for validation.
    
    # parse the configuration options
    options = parser.parse_args()

    # if verbose mode was requested, update the logging level
    if options.verbose:
        LOGGER.setLevel(__debug__)
        opt_output = 'Configuration Options:\n'
        for key, value in vars(options).items():
            opt_output = '%s%16s: %s\n' % (opt_output, key, value)
        LOGGER.debug(opt_output)

    # ensure a valid action was provided
    if not options.action:
        LOGGER.error('Please specify an action to perform.')
        print(parser.format_help())
        sys.exit(1)
    elif options.action not in ['download', 'install', 'update']:
        LOGGER.error('"%s" is not a valid vsc action.' % (options.action))
        print(parser.format_help())
        sys.exit(1)

    # make sure we haven't specified to exclusively use more than one different
    # version of VS Code for both the source and destination editors.
    if options.insiders and options.codium:
        LOGGER.error(
            'You\'ve specified to use both VSCode Insiders and VS Codium.\n'
            'Only one of these options is allowed at a time, since using\n'
            'either of them overrides both the source and destination editors\n'
            'If you need to specify different code editors for the source and\n'
            'destination, you can do so using:\n\n'
            '-s, --source\n-d, --dest\n')
        sys.exit(1)

    # Keep downloaded files if any of the following are true:
    # - the keep options was explicitely provided
    # - the action is 'download'
    # - the action is 'install'
    options.keep = options.keep or options.action in ['download', 'install']

    return options


def main():
    # specify the parser
    parser = configargparse.ArgParser(
        add_help=False,
        formatter_class=CustomFormatter
    )

    # specify the parser options
    parser.add('action', nargs='?', help='The VSCode Extension Manager action to execute: [download|install|update]')
    parser.add_argument('--help', action="help", help="Show help message")
    parser.add_argument('-c', '--config', is_config_file=True, help='config file path')
    parser.add_argument('-d', '--dest-editor', default='', help='The editor where the extensions will be installed')
    parser.add_argument('-e', '--extensions', default='', help='A string, list, or directory of extensions to download/update/install')
    parser.add_argument('-g', '--ssh-gateway', help='IP Address or hostname of the SSH gateway')
    parser.add_argument('-h', '--ssh-host', help='IP Address or hostname of the SSH host')
    parser.add_argument('-k', '--keep', default=False, action='store_true', help='If set, downloaded .vsix files will not be deleted')
    parser.add_argument('-n', '--dry-run', default=False, action='store_true', help='Preview the action(s) that would be taken without actually taking them')
    parser.add_argument('-o', '--output-dir', default='/tmp/vsc-%d' % (time() * 1000), help='The directory where the extensions will be downloaded.')
    parser.add_argument('-p', '--ssh-port', default=22, help='SSH port for remote host connection')
    parser.add_argument('-s', '--source-editor', default='', help='The editor that will be used to identify extensions')
    parser.add_argument('-u', '--ssh-user', default=getuser(), help='Username for remote SSH host connection')
    parser.add_argument('-v', '--verbose', default=False, action='store_true', help='Display more program output')
    parser.add_argument('--insiders', default=False, action='store_true', help='Use VSCode Insiders as the source and destination editor')
    parser.add_argument('--codium', default=False, action='store_true', help='Use VSCodium as the source and destination editor')

    # validate the configuration options
    options = validate_options(parser)

    # Establish the tunnel connection
    tunnel = Tunnel(
        host=options.ssh_host,
        port=options.ssh_port,
        user=options.ssh_user,
        gateway=options.ssh_gateway,
        verbose=options.verbose,
        dry_run=options.dry_run,
    )

    # initialize an instance of the VSC Manager
    manager = ExtensionManager(
        extensions=options.extensions,
        output_dir=options.output_dir,
        source_editor=options.source_editor,
        dest_editor=options.dest_editor,
        dry_run=options.dry_run,
        ssh_host=options.ssh_host,
        ssh_gateway=options.ssh_gateway,
        ssh_port=options.ssh_port,
        ssh_user=options.ssh_user,
        tunnel=tunnel,
        keep=options.keep,
        insiders=options.insiders,
        codium=options.codium,
    )

    # TODO: Implement more thorough dry-run functionality.
    # if it's just a dry-run, don't perform the action
    if options.dry_run:
        LOGGER.info('Dry-run only. Exiting..')
        sys.exit(0)

    # perform the specified vsc action
    try:
        action = options.action
        getattr(manager, options.action)()
    except KeyboardInterrupt as e:
        pass
    except Exception as e:
        LOGGER.error(e)
    finally:
        if not options.keep:
            manager.cleanup_output_dir()

if __name__ == "__main__":
    main()
