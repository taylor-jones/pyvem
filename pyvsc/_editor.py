from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals

import os
import re
import subprocess
import json

from distutils.spawn import find_executable
from pyvsc._util import expanded_path, truthy_list
from pyvsc._containers import AttributeDict
from pyvsc._compat import is_py3, popen, split
from pyvsc._machine import platform_query
from pyvsc._curler import CurledRequest
from pyvsc._logging import get_rich_logger


_ENCODING = 'utf-8'
_EXTENSION_ATTRIBUTES_RE = re.compile(
    '^(?P<unique_id>.*?^(?P<publisher>.*?)\.(?P<package>.*))\@(?P<version>.*)')

_GITHUB_EDITOR_UPDATE_ROOT_URL = 'https://api.github.com'
_MARKETPLACE_EDITOR_UPDATE_ROOT_URL = \
    'https://update.code.visualstudio.com/api/update'

# These represent the query patterns for the different vscode editors based
# on the system platform and architecture.
_MARKETPLACE_EDITOR_DISTRO_PATTERN = platform_query(
    windows='win32-x64',
    win32='win32',
    darwin='darwin',
    linux='linux-x64',
    linux32='linux-ia32',
    rpm='linux-rpm-64',
    rpm32='linux-rpm-ia32',
    deb='linux-deb-x64',
    deb32='linux-deb-ia32'
)

_LOGGER = get_rich_logger(__name__)
_curled = CurledRequest()


SupportedEditorCommands = AttributeDict({
    'code': 'code',
    'insiders': 'code-insiders',
    'exploration': 'code-exploration',
    'codium': 'codium',
})


class SupportedEditor(AttributeDict):
    """
    Define the attributes of a supported code editor.
    """
    def __init__(
        self,
        command,
        editor_id,
        remote_alias,
        home_dirname,
        tunnel,
        api_root_url=_MARKETPLACE_EDITOR_UPDATE_ROOT_URL,
        github_ext_pattern=None,
    ):
        self.command = command
        self.editor_id = editor_id
        self.remote_alias = remote_alias
        self.home_dirname = home_dirname
        self.api_root_url = api_root_url
        self.github_ext_pattern = github_ext_pattern
        self.tunnel = tunnel

        '''
        Once set, "latest" has the following structure:

        latest <dict> {
            url: <str>,
            name: <str>,
            version: <str>
            productVersion: <str>,
            hash: <str>,
            timestamp: <int>,
            sha256hash: <str>,
        }
        '''
        self._latest = None


    def install_extension(self, extension_path):
        try:
            ext_name = os.path.basename(extension_path)
            _LOGGER.info('Installing {}'.format(ext_name))
            proc = subprocess.Popen([
                self.command,
                '--install-extension',
                extension_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE)
            proc.wait()

        except Exception as e:
            _LOGGER.error('Failed to install extension: {}'.format(ext_name))
            _LOGGER.debug(e)


    def get_extensions(self, force_recheck=False):
        """
        Builds a list of extensions for the current code editor, parsing each
        list item into a dict having the following format:
        {
            'unique_id': <str>,
            'publisher': <str>,
            'package': <str>,
            'version': <str>
        }

        Keyword Arguments:
            force_recheck {bool} -- If True, any previously-build extensions
            list will be ignored and a new one will be built (default: {False})

        Returns:
            list -- A list of extension dict items representing the currently-
            installed extensions for this editor.
        """
        if not self.installed:
            return []
        elif self._extensions is not None and not force_recheck:
            return self._extensions

        args = [self.command, '--list-extensions', '--show-versions']
        stdout, _ = popen(args)
        extensions = [
            _EXTENSION_ATTRIBUTES_RE.match(i).groupdict()
            for i in stdout.splitlines()
        ]

        self._extensions = extensions
        return self._extensions


    def download(self, remote_dir, local_dir):
        """
        Communicate to the tunnel instance to download the editor on the
        remote machine and then copy it to the specified location on the
        local machine.

        Arguments:
            remote_dir {str} -- Absolute path to the download directory on the
                remote host
            local_dir {str} -- Absolute path to the download directory on the
                local host.

        Returns:
            str -- The absolute path to the downloaded file on the local
            machine (if sucessful). If unsuccessful, returns False.
        """
        remote_path = os.path.join(remote_dir, self.download_file_name)
        local_path = os.path.join(local_dir, self.download_file_name)
        curled_request = _curled.get(self.download_url, output=remote_path)

        response = self.tunnel.run(curled_request)
        if response.exited != 0:
            _LOGGER.error(response.stderr)
            return False

        _LOGGER.info(response.stdout)
        self.tunnel.get(remote_path, local_path)

        # return the path to the local file so we can keep track of it
        # and delete it once processing completes
        return local_path


    def get_engine(self):
        """
        Get the currently-installed version of this code editor.

        Returns:
            str -- The engine version of the editor or None if the editor
            is not installed or not on the PATH.
        """
        try:
            # check the installed version
            output = subprocess.check_output([
                self.command, '--version'
            ], shell=False).splitlines()

            # format the info about the currently installed version
            return output[0].decode(_ENCODING)

        except Exception as e:
            return None


    @property
    def api_url(self):
        if self._api_url is not None:
            return self._api_url
        if self.api_root_url.startswith(_GITHUB_EDITOR_UPDATE_ROOT_URL):
            self._api_url = self.api_root_url
        else:
            path = '/{}/{}/latest'.format(
                _MARKETPLACE_EDITOR_DISTRO_PATTERN,
                self.remote_alias)
            self._api_url = '{}{}'.format(self.api_root_url, path)
        return self._api_url


    @property
    def latest(self):
        if self._latest is None:
            curl_request = _curled.get(self.api_url)
            response = self.tunnel.run(curl_request)

            if response.exited == 0:
                self._latest = json.loads(response.stdout)
            else:
                _LOGGER.error(response.stderr)

        return self._latest


    @property
    def download_url(self):
        if self._download_url is not None:
            return self._download_url

        if self.api_url.startswith(_GITHUB_EDITOR_UPDATE_ROOT_URL):
            # if this editor uses the github api, we need to determine which
            # asset we're looking for and find the browser download url
            assets = self.latest['assets']
            asset = next(x for x in assets if x['name'].endswith(
                self.github_ext_pattern))
            self._download_url = asset['browser_download_url']

        elif self.api_root_url == _MARKETPLACE_EDITOR_UPDATE_ROOT_URL:
            # if this editor uses the the visualstudio update api,
            # then just get the url key from the json result.
            self._download_url = self.latest['url']

        return self._download_url


    @property
    def download_file_name(self):
        return os.path.basename(self.download_url)


    @property
    def extensions_dir(self):
        if self._extensions_dir is None:
            self._extensions_dir = \
                expanded_path('$HOME/{}/extensions'.format(self.home_dirname))
        return self._extensions_dir


    @property
    def installed(self):
        return find_executable(self.command) is not None


    @property
    def can_update(self):
        # if we've already run this check, we don't need to do it again.
        if self._can_update is not None:
            return self._can_update

        try:
            self.version = ''
            if self.installed:
                # check the installed version
                output = subprocess.check_output([
                    self.command, '--version'
                ], shell=False).splitlines()

                # format the info about the currently installed version
                self.version = output[0].decode(_ENCODING)

            # check the latest remote version
            latest = self.latest
            self.latest_version = latest.get('name')

            _LOGGER.debug('{} | installed: {}, latest: {}'.format(
                self.editor_id, self.version, self.latest_version))

            # if the installed version doesn't match the latest remote version
            # or the installed hash doesn't match the latest remote hash,
            # we'll assume the editor can be updated.
            self._can_update = self.version != self.latest_version

        except (TypeError, ValueError) as e:
            _LOGGER.debug(e)
            self._can_update = False

        finally:
            return self._can_update



def set_tunnel_for_editors(tunnel, *editors):
    """
    Apply a tunnel object for all provided SupportedEditor instances.

    Arguments:
        tunnel {Tunnel} -- A Tunnel instance

    """
    for editor in editors:
        assert isinstance(editor, SupportedEditor)
        setattr(editor, 'tunnel', tunnel)


def get_editors(tunnel=None):
    """
    Get AttributeDict of SupportedEditors.

    Builds an AttributeDict of data about each of the support VSCode editor
    variations on the current system.

    Keyword Arguments:
        tunnel {Tunnel} -- An SSH tunnel connection, which is used to make
        remote requests as part of building the editor information
        (default: {None})

    Returns
        AttributeDict

    """
    return AttributeDict({
        'code': SupportedEditor(
            command=SupportedEditorCommands.code,
            editor_id='VSCode',
            home_dirname='.vscode',
            remote_alias='stable',
            tunnel=tunnel,
        ),
        'insiders': SupportedEditor(
            command=SupportedEditorCommands.insiders,
            editor_id='VSCode Insiders',
            home_dirname='.vscode-insiders',
            remote_alias='insider',
            tunnel=tunnel,
        ),
        'exploration': SupportedEditor(
            command=SupportedEditorCommands.exploration,
            editor_id='VSCode Exploration',
            home_dirname='.vscode-exploration',
            remote_alias='exploration',
            tunnel=tunnel,
        ),
        'codium': SupportedEditor(
            command=SupportedEditorCommands.codium,
            editor_id='VSCodium',
            home_dirname='.vscode-oss',
            remote_alias='codium',
            tunnel=tunnel,
            api_root_url='https://api.github.com/repos/VSCodium/vscodium/releases/latest',
            github_ext_pattern=platform_query(
                darwin='dmg',
                windows='exe',
                linux='AppImage',
                rpm='rpm',
                deb='deb'
            )
        )
    })
