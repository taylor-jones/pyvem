"""
Download and install the latest versions of 
VSCode extensions with cURL over a remote network.
"""

import os
import re
import platform
import logging
import configargparse

from datetime import datetime
from pathlib import Path
from shutil import rmtree
from getpass import getuser
from pyvsc.tunnel import Tunnel


_LOGGER = logging.getLogger(__name__)


class Manager():
    def __init__(self, **kwargs):
        self._output = None
        self._extensions = None
        self._extensions_dir = None

        # determine which version of the editor to work with, and make
        # sure that version is installed and on the PATH
        self.insiders = kwargs.get('insiders', False)
        self.cmd = 'code-insiders' if self.insiders else 'code'
        self._check_code_installed()

        # establish the ssh tunnel
        self.tunnel = Tunnel(
            host=kwargs.get('ssh_host'),
            port=kwargs.get('ssh_port'),
            user=kwargs.get('ssh_use')
        )

        # determine the output directory and specified extensions
        self.keep = kwargs.get('keep')
        self.output = kwargs.get('output_dir')
        self.extensions = kwargs.get('extensions')

    def _check_code_installed(self):
        """
        Checks if the specified version of VS Code is installed.
        Raises an error if not.
        """
        try:
            self.version = os.popen(f'{self.cmd} --version').read().splitlines()[0]
            return True
        except RuntimeError as e:
            logging.error(f'The command {self.cmd} is not on your path. ' \
                'Please make sure the correct version of VS Code is installed ' \
                'before running this program')
            exit(1)

    def _valid_dir(self, directory, create=False):
        d = os.path.expanduser(directory)
        d = os.path.abspath(d)

        # check whether or not the output directory existed
        # beforehand, so we know whether or not to delete the
        # entire directory when we're done or just the extensions.
        p = Path(d)

        # if we're only checking on the existence of the directory,
        # then don't try to create it and only return the directory
        # path if it already existed.
        if not create:
            if p.is_dir():
                return d
            return False
        
        # otherwise, try to create the directory, and return the
        # absolute path if creation was successful.
        else:
            self._output_preexisted = p.is_dir()

            # attempt to create the directory (if not exists)
            try:
                p.mkdir(parents=True, exist_ok=True)
                self.tunnel.send(f'mkdir -p {d}')
                return d
            except Exception as e:
                _LOGGER.error(f'Could not validate directory: {d}')
                exit(1)
                return False

    def _dirfiles(self, d):
        """
        Returns a list of only the files from a given directory.
        """
        return [f.name for f in os.scandir(d) if f.is_file()]

    def _vsc_url(self):
        """
        Returns a URL that can be used to download the latest version of
        the specified VS Code editor.
        """
        operating_system = platform.system()
        version = 'insider' if self.insiders else 'stable'

        if operating_system == 'Linux':
            return f'https://update.code.visualstudio.com/latest/linux-rpm-x64/{version}'
        elif operating_system == 'Darwin':
            return f'https://update.code.visualstudio.com/latest/darwin/{version}'
        else:
            print(f'Sorry, this program doesn\'t currently '
            f' support {operating_system}')
            exit(1)

    def _vsc_curl(self, url):
        """
        Returns a cURL formatted command that can be executed
        to download the VS Code editor.
        """
        return f'cd {self.output} && curl {url} -O'

    def _vsix_curl(self, extension, url):
        """
        Returns a cURL command that can be used to download a specified
        VSCode extension, given the extension name and URL.
        """
        return f'curl {url} -o {self.output}/{extension}.vsix'

    def _vsix_url(self, extension):
        """
        Builds the URL for a .vsix vscode extension, given the full 
        name of the extension in the format of {publisher}.{package}

        ex: ms-python.python
        """
        publisher, package = extension.split('.')
        return f'https://{publisher}.gallery.vsassets.io' \
            f'/_apis/public/gallery/publisher/{publisher}' \
            f'/extension/{package}/latest/assetbyname' \
            f'/Microsoft.VisualStudio.Services.VSIXPackage'

    def _cleanup(self):
        """
        Removes downloaded extension files from the output directory, or 
        if the output directory wasn't pre-existing, removes the entire dir.
        """
        _LOGGER.info('Cleaning up downloaded extensions.')

        if self._output_preexisted == True:
            # just remove the extension files
            for ext in self.extensions:
                try:
                    ext_name = f'{self.output}/{ext}.vsix'
                    os.system(f'rm -f {ext_name}')
                    _LOGGER.debug(f'Removed {ext_name}')
                except Exception as e:
                    _LOGGER.error(f'Failed to removed {ext_name}')
        else:
            # remove the whole directory.
            try:
                rmtree(self._output)
                _LOGGER.debug(f'Removed directory: {self._output}')
            except IOError as e:
                _LOGGER.error(f'Failed to remove directory: {self._output}')

    def __del__(self):
        if not self.keep:
            self._cleanup()

    def download(self):
        if self.extensions == None:
            _LOGGER.error('No extensions have been specified.')
            exit(1)

        if self.output == None:
            _LOGGER.error('No output directory has been specified.')
            exit(1)

        _LOGGER.info(f'Downloading extensions to {self.output}')

        # removes the .vsix from any extensions
        def no_vsix(ext):
            return ext.rstrip('.vsix')

        # download each of the extensions to the output 
        # directory in the ssh tunnel.
        for ext in self.extensions:
            url = self._vsix_url(ext)
            cmd = self._vsix_curl(ext, url)
            _LOGGER.info(f'Downloading {ext}')

            # download the extension
            self.tunnel.send(cmd)

            # transfer the extension
            ext_name = f'{self.output}/{ext}.vsix'
            _LOGGER.debug(f'Transferring {ext_name} from remote')
            self.tunnel.get(ext_name, ext_name)

            # delete the extension from the remote
            _LOGGER.debug(f'Deleting {ext_name} from remote')
            self.tunnel.send(f'rm -f {ext_name}')

        # delete the remote directory
        self.tunnel.rmdir(self.output)

    def _install_extension(self, path):
        """
        Installs an individual VSIX extensions at a specified path.
        """
        _LOGGER.info(f'Installing {os.path.basename(path)}')
        os.system(f'{self.cmd} --install-extension {path}')

    def install(self, path=None):
        """
        Installs the extension at the specified path or all the
        extensions in the specified directory.
        """
        # if no path was provided, assume we want to install the
        # extensions from the output directory.
        path = path or self._extensions_dir

        if os.path.isfile(path):
            self._install_extension(path)
        elif os.path.isdir(path):
            for f in os.listdir(path):
                self._install_extension(f'{path}/{f}')
        else:
            _LOGGER.error(f'Path {path} is invalid.')
            exit(1)

    def update(self):
        """
        Downloads the latest versions of all specified extensions
        to the output directory, and then passes the output directory
        as the source for extensions that should be installed.
        """
        self.download()
        self.install(self.output)

    @property
    def output(self):
        return self._output

    @output.setter
    def output(self, directory):
        # if no directorty was provided, use a default, auto-generated 
        # directory in tmp using a known prefix #nd a timestamp.
        if directory is None:
            d = f'/tmp/vscm-{int(datetime.now().timestamp())}'
        else:
            d = os.path.abspath(directory)

        # validate the output directory
        self._output = self._valid_dir(d, True)

    @property
    def extensions(self):
        return self._extensions

    @extensions.setter
    def extensions(self, exts):
        # if the user did not specify any extensions, we'll assume that
        # they want to update all of their currently installed extensions.
        if exts is None:
            exts = os.popen('code --list-extensions').read().splitlines()

        # otherwise, if we were given a string of one or more extensions, 
        # we need to first check if the string represents a directory.
        
        elif type(exts) is str:
            # if a valid directory was provided, then get a list 
            # of all the extensions in the directory.
            directory = self._valid_dir(exts)
            if directory:
                self._extensions_dir = directory
                exts = self._dirfiles(directory)

            # If a literal string of extension names was provided,
            # convert the string to a list of extensions.
            else:
                exts = re.split(';|,', exts)

        # make sure we're dealing with a list
        try:
            exts = list(exts)
        except TypeError as e:
            _LOGGER.error('Could not identify a list of extensions.')
            exit(1)

        # set the instance-level extensions
        self._extensions = exts


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
                    parts.append('%s' % option_string)
                parts[-1] += ' %s'%args_string
            return ', '.join(parts)


def main():
    # setup logging
    logging.basicConfig(level=logging.INFO, format='%(message)s')

    # specify the parser options
    parser = configargparse.ArgParser(formatter_class=CustomFormatter)
    parser.add('command', nargs='?', help='The VSCode Extension Manager command to execute: [download|install|update]')
    parser.add('-c', '--config', is_config_file=True, help='config file path')
    parser.add('-o', '--output-dir', help='The directory where the extensions will be downloaded.')
    parser.add('-e', '--extensions', help='A string, list, or directory of extensions to download/update/install')
    parser.add('--ssh-host', default='localhost', help='SSH Host IP or network name')
    parser.add('--ssh-port', default=22, help='SSH Port')
    parser.add('--ssh-user', default=getuser(), help='SSH username')
    parser.add('-k', '--keep', default=False, action='store_true', help='If set, downloaded .vsix files will not be deleted')
    parser.add('-i', '--insiders', default=False, action='store_true', help='Install extensions to VS Code Insiders')

    # parse the configuration options
    options = parser.parse_args()
    print(parser.format_values())

    # if no actionable command was provided, just print
    # the help output, but don't execute anything else.
    if not options.command:
        print(parser.format_help())
        return

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
