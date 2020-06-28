"""Code editor management module"""


from distutils.spawn import find_executable
import json
import os
import re
import subprocess

from cached_property import cached_property

from pyvsc._util import expanded_path
from pyvsc._containers import AttributeDict
from pyvsc._machine import platform_query
from pyvsc._curler import CurledRequest
from pyvsc._logging import get_rich_logger


_ENCODING = 'utf-8'
_EXTENSION_ATTRIBUTES_RE = re.compile(
    r'^(?P<unique_id>.*?^'
    r'(?P<publisher>.*?)\.'
    r'(?P<package>.*))\@(?P<version>.*)'
)

_GITHUB_EDITOR_UPDATE_ROOT_URL = 'https://api.github.com'
_MARKETPLACE_EDITOR_UPDATE_ROOT_URL = 'https://update.code.visualstudio.com/api/update'

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


    def install_extension(self, extension_path):
        try:
            ext_name = os.path.basename(extension_path)
            _LOGGER.info('Installing %s', ext_name)
            subprocess.Popen([self.command, '--install-extension', extension_path],
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE).wait()

        except Exception as err:
            _LOGGER.error('Failed to install extension: %d', ext_name)
            _LOGGER.debug(err)


    def get_extensions(self, force_recheck=False):
        """
        Builds a list of extensions for the current code editor, parsing each list item into
        a dict having the following format (which is based on _EXTENSION_ATTRIBUTES_RE):
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
            list -- A list of extension dict items representing the currently-installed
                extensions for this editor.
        """
        if not self.installed:
            return []

        # if a forced recheck is requested, deleted the current extensions cache
        # before rebuilding the extensions list
        if force_recheck:
            del self.__dict__['extensions']
        return self.extensions


    def download(self, remote_dir, local_dir):
        """
        Communicate to the tunnel instance to download the editor on the remote machine
        and then copy it to the specified location on the local machine.

        Arguments:
            remote_dir {str} -- Absolute path to the download directory on the remote host
            local_dir {str} -- Absolute path to the download directory on the local host.

        Returns:
            str -- The absolute path to the downloaded file on the local
            machine (if sucessful). If unsuccessful, returns False.
        """
        remote_fs_path = os.path.join(remote_dir, self.download_file_name)
        local_fs_path = os.path.join(local_dir, self.download_file_name)
        curl_request = _curled.get(self.download_url, output=remote_fs_path)

        response = self.tunnel.run(curl_request)
        if response.exited != 0:
            _LOGGER.error(response.stderr)
            return False

        _LOGGER.info(response.stdout)
        self.tunnel.get(remote_fs_path, local_fs_path)

        # return the path to the local file so we can keep track of it
        # and delete it once processing completes
        return local_fs_path


    @cached_property
    def engine(self):
        """
        Get the currently-installed version of this code editor.

        Returns:
            str|None -- The engine version of the editor (or None if the editor
            is not installed or not on the PATH).
        """
        try:
            # check the installed editor version. This will return 3 lines as follows:
            # 1) the installed editor engine version
            # 2) the installed editor hash
            # 3) installed editor architecture

            # Since we're only interested in the engine version, we'll return the
            # first line of the output value.
            installed_editor_info = subprocess.check_output([self.command, '--version'])
            installed_editor_engine = installed_editor_info.splitlines()[0].decode(_ENCODING)
            return installed_editor_engine

        # If the editor is not on
        except EnvironmentError:
            return None


    @cached_property
    def extensions(self):
        """
        Get a list of the extensions installed for the current editor.

        Returns:
            list
        """
        stdout, _ = subprocess.Popen([self.command, '--list-extensions', '--show-versions'],
                                     stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                     encoding='utf-8').communicate()

        # parse the extension results into a list of dicts of extension attributes
        return [_EXTENSION_ATTRIBUTES_RE.match(line).groupdict() for line in stdout.splitlines()]


    @cached_property
    def api_url(self):
        if self.api_root_url.startswith(_GITHUB_EDITOR_UPDATE_ROOT_URL):
            return self.api_root_url

        path = f'/{_MARKETPLACE_EDITOR_DISTRO_PATTERN}/{self.remote_alias}/latest'
        return f'{self.api_root_url}{path}'


    @cached_property
    def latest(self):
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
        curl_request = _curled.get(self.api_url)
        response = self.tunnel.run(curl_request)

        if response.exited == 0:
            return json.loads(response.stdout)

        _LOGGER.error(response.stderr)
        return None


    @cached_property
    def download_url(self):
        # if this editor uses the github api, we need to determine which asset we're looking
        # for and find the browser download url
        if self.api_url.startswith(_GITHUB_EDITOR_UPDATE_ROOT_URL):
            assets = self.latest['assets']
            asset = next(x for x in assets if x['name'].endswith(self.github_ext_pattern))
            return asset['browser_download_url']

        # if this editor uses the the visualstudio update api, get the url from the json result.
        if self.api_root_url == _MARKETPLACE_EDITOR_UPDATE_ROOT_URL:
            return self.latest['url']


    @property
    def download_file_name(self):
        return os.path.basename(self.download_url)


    @property
    def extensions_dir(self):
        return expanded_path(f'$HOME/{self.home_dirname}/extensions')


    @property
    def installed(self):
        return find_executable(self.command) is not None


    @property
    def latest_version(self):
        return self.latest.get('name')


    @property
    def can_update(self):
        installed_version = self.engine
        latest_version = self.latest_version

        # we can update the current editor if all of the following are true:
        # - we were able to connect to the remote marketplace to identify which version is the
        #   most-recently-released version of this editor.
        # - the currently-installed version is older than the latest version OR
        #   the editor is not currently installed.
        return latest_version is not None and (
            installed_version is None or installed_version != latest_version)


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

    Builds an AttributeDict of data about each of the support VSCode editor variations on the
    current system.

    Keyword Arguments:
        tunnel {Tunnel} -- An SSH tunnel connection, which is used to make remote requests as
            part of building the editor information (default: {None})

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
