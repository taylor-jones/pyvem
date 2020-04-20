from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals

import os
import re
import logging
import subprocess
import requests

from distutils.spawn import find_executable
from pyvsc._util import AttributeDict, expanded_path, truthy_list
from pyvsc._compat import is_py3, popen, split
from pyvsc._machine import Machine


_MACHINE = Machine()
_ENCODING = 'utf-8'
_EXTENSION_ATTRIBUTES_RE = re.compile(
    '^(?P<unique_id>.*?^(?P<publisher>.*?)\.(?P<package>.*))\@(?P<version>.*)')

_GITHUB_EDITOR_UPDATE_ROOT_URL = 'https://api.github.com'
_MARKETPLACE_EDITOR_UPDATE_ROOT_URL = 'https://update.code.visualstudio.com/api/update'

_LOGGER = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)s]\t%(module)s::%(funcName)s:%(lineno)d | %(message)s'
)


class SupportedEditor(AttributeDict):
    """
    Defines the attributes of a supported code editor
    """
    def __init__(
        self,
        command,
        remote_alias,
        home_dirname,
        api_root_url=_MARKETPLACE_EDITOR_UPDATE_ROOT_URL
    ):
        self.command = command
        self.remote_alias = remote_alias
        self.home_dirname = home_dirname
        self.api_root_url = api_root_url


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
            list -- A list of extension dict items
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
            path = '/%s/%s/latest' % (_MACHINE.distro_query, self.remote_alias)
            self._api_url = '%s%s' % (self.api_root_url, path)
        return self._api_url

    @property
    def download_url(self):
        api_json = self._api_json or requests.get(self.api_url).json()

        if self.api_url.startswith(_GITHUB_EDITOR_UPDATE_ROOT_URL):
            # if this editor uses the github api, we need to determine which
            # asset we're looking for and find the browser download url
            target_ext = _MACHINE.distro_extension
            assets = api_json['assets']
            asset = next(x for x in assets if x['name'].endswith(target_ext))
            return asset['browser_download_url']
        elif self.api_root_url == _MARKETPLACE_EDITOR_UPDATE_ROOT_URL:
            # if this editor uses the the visualstudio update api, then just
            # get the url key from the json result
            return api_json['url']

    @property
    def extensions_dir(self):
        if self._extensions_dir is None:
            self._extensions_dir = expanded_path(
                '$HOME/%s/extensions' % self.home_dirname)
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
            self._api_json = requests.get(self.api_url).json()
            remote_version = self._api_json['name']
            remote_hash = self._api_json['version']

            self._can_update = (
                self.version != remote_version 
                or self.hash != remote_hash)

        except Exception as e:
            _LOGGER.debug(e)
            self._can_update = False
        finally:
            return self._can_update


#
# Define the supported VSCode editor variations
#

Editors = AttributeDict({
    'code': SupportedEditor(
        command='code',
        home_dirname='.vscode',
        remote_alias='stable',
    ),
    'insiders': SupportedEditor(
        command='code-insiders',
        home_dirname='.vscode-insiders',
        remote_alias='insider',
    ),
    'exploration': SupportedEditor(
        command='code-exploration',
        home_dirname='.vscode-exploration',
        remote_alias='exploration',
    ),
    'codium': SupportedEditor(
        command='codium',
        home_dirname='.vscode-oss',
        remote_alias='codium',
        api_root_url='https://api.github.com/repos/VSCodium/vscodium/releases/latest',
    )
})



#######################################################################
# Test Commands -- 
#######################################################################

# from beeprint import pp
# pp(Editors.code.download_url, max_depth=8, indent=2, width=200, sort_keys=True)
# pp(Editors.codium.download_url, max_depth=8, indent=2, width=200, sort_keys=True)
