from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals

import re
import subprocess
import json
import logging

from distutils.spawn import find_executable
from pyvsc._util import expanded_path, truthy_list
from pyvsc._containers import AttributeDict
from pyvsc._compat import is_py3, popen, split
from pyvsc._machine import platform_query
from pyvsc._curler import CurledRequest


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

_LOGGER = logging.getLogger(__name__)
_curled = CurledRequest()


class SupportedEditorCommands:
    code = 'code'
    insiders = 'code-insiders'
    exploration = 'code-exploration'
    codium = 'codium'


class SupportedEditor(AttributeDict):
    """
    Defines the attributes of a supported code editor
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


    @property
    def api_url(self):
        if self._api_url is not None:
            return self._api_url
        if self.api_root_url.startswith(_GITHUB_EDITOR_UPDATE_ROOT_URL):
            self._api_url = self.api_root_url
        else:
            path = '/%s/%s/latest' % \
                (_MARKETPLACE_EDITOR_DISTRO_PATTERN, self.remote_alias)
            self._api_url = '%s%s' % (self.api_root_url, path)
        return self._api_url


    @property
    def latest(self):
        if self._latest is None:
            _LOGGER.debug('Latest {} attributes not yet discovered.'.format(
                self.editor_id))
            curl_request = _curled.get(self.api_url)
            response = self.tunnel.run(curl_request)

            if response.exited == 0:
                self._latest = json.loads(response.stdout)
            else:
                _LOGGER.error(response.stderr)
        else:
            _LOGGER.debug('Latest {} attributes already discovered.'.format(
                self.editor_id))

        return self._latest


    @property
    def download_url(self):
        if self.api_url.startswith(_GITHUB_EDITOR_UPDATE_ROOT_URL):
            # if this editor uses the github api, we need to determine which
            # asset we're looking for and find the browser download url
            assets = self.latest['assets']
            asset = next(x for x in assets if x['name'].endswith(
                self.github_ext_pattern))
            return asset['browser_download_url']

        elif self.api_root_url == _MARKETPLACE_EDITOR_UPDATE_ROOT_URL:
            # if this editor uses the the visualstudio update api,
            # then just get the url key from the json result.
            return self.latest['url']


    @property
    def extensions_dir(self):
        if self._extensions_dir is None:
            self._extensions_dir = \
                expanded_path('$HOME/%s/extensions' % self.home_dirname)
        return self._extensions_dir


    @property
    def installed(self):
        if self._installed is None:
            self._installed = find_executable(self.command) is not None
        return self._installed


    @property
    def can_update(self):
        if self._can_update is not None:
            return self._can_update
        elif not self.installed:
            self._can_update = True
            return self._can_update

        try:
            # check the installed version
            output = subprocess.check_output([
                self.command, '--version'
            ], shell=False).splitlines()

            self.version = output[0].decode(_ENCODING)
            self.hash = output[1].decode(_ENCODING)

            # check the latest remote version
            latest = self.latest
            remote_version = latest['name']
            remote_hash = latest['version']

            self._can_update = \
                self.version != remote_version or self.hash != remote_hash

        except Exception as e:
            self._can_update = False
        finally:
            return self._can_update



def get_editors(tunnel=None):
    """
    Builds an AttributeDict of data about each of the support VSCode editor
    variations on the current system.

    Keyword Arguments:
        tunnel {Tunnel} -- An SSH tunnel connection, which is used to make
        remote requests as part of building the editor information
        (default: {None})

    Returns:
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



#######################################################################
# Test Commands -- 
#######################################################################

# from beeprint import pp
# from pyvsc._tunnel import Tunnel
# from pyvsc._containers import ConnectionParts

# _ssh_host = ConnectionParts(hostname='centos', password='pass')
# _ssh_gateway = ConnectionParts(hostname='centos2', password='pass')
# _tunnel = Tunnel(_ssh_host, _ssh_gateway, True)


# editors = get_editors(_tunnel)

# pp(editors.code.download_url)
# pp(editors.code.can_update)

# pp(Editors.code.download_url, max_depth=8, indent=2, width=200, sort_keys=True)
# pp(Editors.codium.download_url, max_depth=8, indent=2, width=200, sort_keys=True)
