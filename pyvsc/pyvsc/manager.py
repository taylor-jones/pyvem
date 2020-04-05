"""
Download and install the latest versions of 
VSCode extensions with cURL over a remote network.
"""

from __future__ import print_function

import os
import re
import platform
import logging
import configargparse

from time import time
from shutil import rmtree
from getpass import getuser
from glob import glob
from pyvsc.tunnel import Tunnel


LOGGER = logging.getLogger(__name__)
logging.basicConfig(
  level=logging.INFO, 
  format='%(asctime)s | %(module)s [%(levelname)s] - %(funcName)s:%(lineno)d - %(message)s'
)


class Manager():
    def __init__(self, **kwargs):
        self.extensions_dir = None

        # determine which version of the editor to work with, and make
        # sure that version is installed and on the PATH
        self.insiders = kwargs.get('insiders', False)
        self.cmd = 'code-insiders' if self.insiders else 'code'
        self._check_editor_is_installed()

        # establish the ssh tunnel
        self.tunnel = Tunnel(
            host=kwargs.get('ssh_host'),
            port=kwargs.get('ssh_port'),
            user=kwargs.get('ssh_user')
        )

        # determine the output directory and specified extensions
        self.keep = kwargs.get('keep')
        self.output = self._process_output_directory(kwargs.get('output_dir'))
        self.extensions = self._process_extensions(kwargs.get('extensions'))


    def _check_editor_is_installed(self):
        """
        Checks if the specified version of VS Code is installed.
        Raises an error if not.
        
        Returns:
            bool -- True, unless an exception is raised.
        """
        try:
            self.version = os.popen('%s --version' % (
              self.cmd)).read().splitlines()[0]
            return True
        except RuntimeError as e:
            LOGGER.error('The command "%s" is not on your path. Please ' \
              'make sure the correct version of VS Code is installed before ' \
              'running this program.' % (self.cmd))
            exit(1)


    def _get_valid_dir(self, directory, create_if_not_exists=False):
        d = os.path.expanduser(directory)
        d = os.path.abspath(d)
        dir_exists = os.path.isdir(d)

        # if we're only checking on the existence of the directory, then don't
        # try to create it and only return the dir path if it already existed.
        if not create_if_not_exists:
            return d if dir_exists else None

        # otherwise, try to create the directory, and return the
        # absolute path if creation was successful.
        try:
            self._output_preexisted = dir_exists
            command = 'mkdir -p %s' % (d)
            os.system(command)
            self.tunnel.send(command)
            return d
        except Exception as e:
          LOGGER.error('Could not validate directory: %s' % (d))
          LOGGER.exception(e)
          exit(1)


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
        else:
            LOGGER.error('Sorry, pyvsc doesn\'t currently support %s' % (
              operating_system))
            exit(1)


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
        """
        publisher, package = extension.split('.')
        return 'https://%s.gallery.vsassets.io/_apis/public/gallery' \
            '/publisher/%s/extension/%s/latest/assetbyname' \
            '/Microsoft.VisualStudio.Services.VSIXPackage' % (
              publisher, publisher, package)


    def _cleanup_output_dir(self):
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
            # just remove the extension files
            for ext in self.extensions:
                try:
                    ext_name = '%s/%s.vsix' % (self.output, ext)
                    os.system('rm -f %s' % (ext_name))
                    LOGGER.debug('Removed extension: %s' % (ext_name))
                except Exception as e:
                    LOGGER.error('Failed to remove extension: %s' % (ext_name))
        else:
            # remove the whole directory.
            try:
                rmtree(self.output)
                LOGGER.debug('Removed directory: %s' % (self.output))
            except IOError as e:
                LOGGER.error('Failed to remove directory: %s' % (self.output))


    def __del__(self):
        if not self.keep:
            self._cleanup_output_dir()


    def download(self):
        if self.extensions == None:
            LOGGER.error('No extensions have been specified.')
            exit(1)

        if self.output == None:
            LOGGER.error('No output directory has been specified.')
            exit(1)

        LOGGER.info('Downloading %d extensions to %s' % (
          len(self.extensions), self.output))

        # download each extension to the output directory in the ssh tunnel.
        for ext in self.extensions:
            url = self._get_vsix_url(ext)
            cmd = self._get_vsix_curl_command(ext, url)
            LOGGER.info('Downloading extension: %s' % (ext))

            # download the extension
            self.tunnel.send(cmd)

            # transfer the extension
            ext_name = '%s/%s.vsix' % (self.output, ext)
            LOGGER.debug('Transferring %s from remote' % (ext_name))
            self.tunnel.get(ext_name, ext_name)

            # delete the extension from the remote
            LOGGER.debug('Deleting %s from remote' % (ext_name))
            self.tunnel.send('rm -f %s' % (ext_name))

        # delete the remote directory
        self.tunnel.rmdir(self.output)


    def _install_extension(self, path):
        """
        Installs an individual VSIX extensions at a specified path.
        """
        LOGGER.info('Installing %s' % (os.path.basename(path)))
        os.system('%s --install-extension %s' % (self.cmd, path))


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
              extension_path))


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
        if extensions is None or extensions == '*':
            LOGGER.debug('No extensions specified. Finding all extensions')
            extensions = os.popen('code --list-extensions').read().splitlines()

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
        except TypeError as e:
            LOGGER.error('Could not identify a list of extensions.')
            exit(1)

        return extensions


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


def main():
    # setup logging
    logging.basicConfig(format='%(message)s', level=logging.INFO)

    # specify the parser options
    parser = configargparse.ArgParser(formatter_class=CustomFormatter)
    parser.add('command', nargs='?', help='The VSCode Extension Manager command to execute: [download|install|update]')
    parser.add('-c', '--config', is_config_file=True, help='config file path')
    parser.add('-o', '--output-dir', default='/tmp/vsc-%d' % (time() * 1000), help='The directory where the extensions will be downloaded.')
    parser.add('-e', '--extensions', default='*', help='A string, list, or directory of extensions to download/update/install')
    parser.add('-k', '--keep', default=False, action='store_true', help='If set, downloaded .vsix files will not be deleted')
    parser.add('-i', '--insiders', default=False, action='store_true', help='Install extensions to VS Code Insiders instead of VS Code')
    parser.add('-v', '--verbose', default=False, action='store_true', help='Display more program output')
    parser.add('--ssh-host', default='localhost', help='SSH Host IP or network name')
    parser.add('--ssh-port', default=22, help='SSH Port')
    parser.add('--ssh-user', default=getuser(), help='SSH username')

    # parse the configuration options
    options = parser.parse_args()

    # if verbose mode was requested, update the logging level
    if options.verbose:
        LOGGER.setLevel(__debug__)

    # if no actionable command was provided, just print
    # the help output, but don't execute anything else.
    if not options.command:
        print(parser.format_help())
        return

    # print startup config
    LOGGER.debug('vsc started with the following options:')
    for key,value in vars(options).items():
        LOGGER.debug('%12s: %s' % (key, value))

    # initialize an instance of the VSC Manager
    cmd = options.command
    manager = Manager(
        extensions=options.extensions, 
        output_dir=options.output_dir,
        ssh_host=options.ssh_host,
        ssh_port=options.ssh_port,
        ssh_user=options.ssh_user,
        keep=cmd=='download' or cmd=='install' or options.keep,
        insiders=options.insiders,
    )

    # perform the desired operation
    if cmd == 'download':
        manager.download()
    elif cmd == 'install':
        manager.install()
    elif cmd == 'update':
        manager.update()
    else:
        print(parser.format_help())


if __name__ == "__main__":
    main()
