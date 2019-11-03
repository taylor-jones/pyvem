"""
Download and install the latest versions of 
VSCode extensions with cURL.
"""

import os
import re
import logging
import configargparse
from datetime import datetime
from pathlib import Path
from shutil import rmtree


_LOGGER = logging.getLogger(__name__)


class VscManager():
    def __init__(self, **kwargs):
        print(kwargs)

        self._output = None
        self._extensions = None
        self._extensions_dir = None

        # make sure VS Code is installed
        self._check_code_installed()

        # determine the output directory and specified extensions
        self.keep = kwargs.get('keep')
        self.output = kwargs.get('output')
        self.extensions = kwargs.get('extensions')

    def _check_code_installed(self):
        """
        Checks if VS Code is installed. Raises an error if not.
        """
        try:
            self.version = os.popen('code --version').read().splitlines()[0]
            return True
        except RuntimeError as e:
            logging.error('Please install VS Code before running this program.')
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
            print('just removing the files')
        else:
            try:
                rmtree(self._output)
                _LOGGER.info(f'Removed directory: {self._output}')
            except IOError as e:
                _LOGGER.error(f'Unable to remove directory: {self._output}')

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

        # download each of the extensions to the output directory
        for ext in self.extensions:
            url = self._vsix_url(ext)
            cmd = self._vsix_curl(ext, url)
            _LOGGER.info(f'Downloading {ext}')
            os.system(cmd)

    def _install_extension(self, path):
        """
        Installs an individual VSIX extensions at a specified path.
        """
        print(f'Installing {os.path.basename(path)}')
        os.system(f'code --install-extension {path}')

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
            d = f'/tmp/vsc-manager-{int(datetime.now().timestamp())}'
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
            # if the string represents a valid directory,
            # then get a list of all the extensions in the directory.
            d = self._valid_dir(exts)
            if d:
                self._extensions_dir = d
                exts = self._dirfiles(d)

            # If a literal string of extension names, 
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
    logging.basicConfig(level=logging.INFO, format='%(message)s')

    parser = configargparse.ArgParser(formatter_class=CustomFormatter)
    parser.add('command', nargs='?', help='The VSCode Extension Manager command to execute: [download|install|update]')
    parser.add('-c', '--config', is_config_file=True, help='config file path')
    parser.add('-o', '--output', help='The directory where the extensions will be downloaded.')
    parser.add('-e', '--extensions', help='A string, list, or directory of extensions to download/update/install')
    parser.add('--keep', default=False, action='store_true', help='If set, downloaded .vsix files will not be deleted')

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
    vsm = VscManager(
        extensions=options.extensions, 
        output=options.output,
        keep=cmd=='download' or cmd=='install' or options.keep
    )

    # perform the desired operation
    if cmd == 'download':
        vsm.download()
    elif cmd == 'install':
        vsm.install()
    elif cmd == 'update':
        vsm.update()
    else:
        print(parser.format_help())


if __name__ == "__main__":
    main()
