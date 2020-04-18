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
from pyvsc._machine import get_distribution_query, get_distribution_extension


_ENCODING = 'utf-8'
_EXTENSION_ATTRIBUTES_RE = re.compile('^(?P<id>.*?^(?P<publisher>.*?)\.(?P<package>.*))\@(?P<version>.*)')
_PLATFORM_QUERY = get_distribution_query()

_LOGGER = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)s]\t%(module)s::%(funcName)s:%(lineno)d | %(message)s'
)


class SupportedEditor(AttributeDict):
    """
    Defines the attributes of a supported code editor
    """
    __allowed = (
        'command',
        'remote_alias',
        'api_root_url',
        'home_dirname',
    )

    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            assert(k in self.__class__.__allowed)
            setattr(self, k, v)


    def get_extensions(self, force_recheck=False):
        """
        Builds a list of extensions for the current code editor, parsing each
        list item into a dict having the following format:
        {
            'id': <str>,
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

        if self.api_root_url.startswith('https://api.github.com/'):
            self._api_url = self.api_root_url
        else:
            query = os.path.join(_PLATFORM_QUERY, self.remote_alias, 'latest')
            self._api_url = os.path.join(self.api_root_url, query)
        return self._api_url

    @property
    def download_url(self):
        api_json = self._api_json or requests.get(self.api_url).json()

        if self.api_url.startswith('https://api.github.com/'):
            # if this editor uses the github api, we need to determine which
            # asset we're looking for and find the browser download url
            target_ext = get_distribution_extension()
            assets = api_json['assets']
            asset = next(x for x in assets if x['name'].endswith(target_ext))
            return asset['browser_download_url']
        elif self.api_root_url == 'https://update.code.visualstudio.com/api/update':
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

            local_name = output[0].decode(_ENCODING)
            local_version = output[1].decode(_ENCODING)
            
            # _LOGGER.debug('local_name: %s' % (local_name))
            # _LOGGER.debug('local_version: %s' % (local_version))

            # check the latest remote version
            self._api_json = requests.get(self.api_url).json()
            remote_name = self._api_json['name']
            remote_version = self._api_json['version']

            # _LOGGER.debug('remote_name: %s' % (remote_name))
            # _LOGGER.debug('remote_version: %s' % (remote_version))

            self._can_update = (
                local_name != remote_name 
                or local_version != remote_version)

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
        api_root_url='https://update.code.visualstudio.com/api/update',
    ),
    'insiders': SupportedEditor(
        command='code-insiders',
        home_dirname='.vscode-insiders',
        remote_alias='insider',
        api_root_url='https://update.code.visualstudio.com/api/update',
    ),
    'exploration': SupportedEditor(
        command='code-exploration',
        home_dirname='.vscode-exploration',
        remote_alias='exploration',
        api_root_url='https://update.code.visualstudio.com/api/update',
    ),
    'codium': SupportedEditor(
        command='codium',
        home_dirname='.vscode-oss',
        remote_alias='codium',
        api_root_url='https://api.github.com/repos/VSCodium/vscodium/releases/latest',
    )
})
