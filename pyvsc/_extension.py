from __future__ import print_function
from __future__ import generators

import re
import os
import logging
import requests

from pyvsc._util import dict_from_list_key, AttributeDict
from pyvsc._machine import platform_query
from pyvsc._marketplace import Marketplace


_GITHUB_API_ROOT_URI = 'https://api.github.com'
_GITHUB_ROOT_URI = 'https://github.com'
_MARKETPLACE = Marketplace()

# NOTE: Active issue for better handling offline binaries installation
# https://github.com/microsoft/vscode-cpptools/issues/5290

# TODO: Check into options for things like:
# - platform-specified vsix extensions
# - check dependencies via the install.lock file (https://github.com/microsoft/vscode-cpptools/issues/4778#issuecomment-568125545)

_NON_MARKETPLACE_EXTENSIONS = AttributeDict({
    'ms-vscode.cpptools': AttributeDict({
        'owner': 'Microsoft',
        'repo': 'vscode-cpptools',
        'asset_name': platform_query(
            windows='cpptools-win32.vsix',
            darwin='cpptools-osx.vsix',
            linux64='cpptools-linux.vsix',
            linux32='cpptools-linux32.vsix'
        )
    })
})


class ExtensionSourceTypes:
    Undefined = 0
    Marketplace = 1
    GitHub = 2


class Extension():
    """
    Extension base class
    """
    def __init__(self, source_type=ExtensionSourceTypes.Undefined, **kwargs):
        self.source_type = source_type
        self.unique_id = kwargs.get('unique_id')
        self.download_url = kwargs.get('download_url')
        self.download_from_marketplace = \
            not self.unique_id in _NON_MARKETPLACE_EXTENSIONS.keys()


    def download(self, directory):
        ext_name = self.unique_id
        if hasattr(self, 'version'):
            ext_name = '%s-%s' % (ext_name, self.version)

        res = requests.get(self.download_url, allow_redirects=True)
        with open('%s/%s.vsix' % (directory, ext_name), 'wb') as f:
            f.write(res.content)
            f.close()



class GithubExtension(Extension):
    """
    GitHub extension class that inherits from Extension base class,
    but represents an extensions which has a GitHub download source.
    """
    def __init__(
        self,
        owner,
        repo,
        asset_name,
        release='latest',
        prerelease=False,
        unique_id=None,
    ):

        self.unique_id = unique_id
        self.owner = owner
        self.repo = repo
        self.asset_name = asset_name
        self.release = release
        self.prerelease = prerelease
        self.download_url = \
            self._from_latest() if release == 'latest' else self._from_args()

        super().__init__(
            source_type=ExtensionSourceTypes.GitHub,
            unique_id=self.unique_id,
            download_url=self.download_url
        )


    def _get_download_url_from_asset_list(self, asset_list):
        """
        Finds the asset from a list of GitHub API assets that corresponds the
        the current machine and returns the associated browser_download_url

        Arguments:
            asset_list {list} -- A list of assets (from the GitHub API)

        Returns:
            str -- The full URL where the asset can be downloaded
        """
        asset = dict_from_list_key(asset_list, 'name', self.asset_name)
        return asset['browser_download_url']


    def _from_latest(self):
        """
        Builds the extension download url by finding the latest extension that
        matches the system platform and release specifications.

        Returns:
            str -- The direct url from which the extension can be downlaoded
        """
        if not self.prerelease:
            # By default, GitHub's API only shows non-prerelease assets at the
            # 'latest' endpoint, so if we don't allow pre-releases, we can just
            # append 'latest' to our API URL and use the resulting asset.
            query_endpoint = '/repos/%s/%s/releases/%s?per_page=1' % \
                (self.owner, self.repo, self.release)
        else:
            # If we DO want to allow pre-release assets, we won't add 'latest'
            # to the end of our query URL, which will allow a prerelease asset
            # to be the first item in the list (if, in fact, a prerelease asset
            # exists and is the latest asset).
            #
            # Note that this will still fetch a non-prerelease/stable asset if
            # the latest asset is non-prerelsease/stable.
            query_endpoint = '/repos/%s/%s/releases?per_page=1' % \
                (self.owner, self.repo)

        query_url = '%s%s' % (_GITHUB_API_ROOT_URI, query_endpoint)
        request = requests.get(query_url)
        request.raise_for_status()
        response = request.json()
        response_obj = response[0] if self.prerelease else response
        asset_list = response_obj['assets']
        return self._get_download_url_from_asset_list(asset_list)


    def _from_args(self):
        """
        Builds the extension download url by joining the class arguments

        Returns:
            str -- The direct url from which the extension can be downlaoded
        """
        query_endpoint = '/%s/%s/releases/download/%s/%s' % \
            (self.owner, self.repo, self.release, self.asset_name)
        return '%s%s' % (_GITHUB_ROOT_URI, query_endpoint)



class MarketplaceExtension(Extension):
    """
    Marketplace extension class that inherits from Extension base class, but
    represents an extensions which has a VSCode Marketplace download source.
    """
    def __init__(self, parsed_marketplace_response):
        p = parsed_marketplace_response

        self.extension_id = p['extensionId']
        self.extension_name = p['extensionName']
        self.display_name = p['displayName']
        self.publisher_name = p['publisher']['publisherName']
        self.unique_id = '%s.%s' % (self.publisher_name, self.extension_name)
        self.description = p['shortDescription']
        self.stats = p['statistics']

        version = p['versions'][0]
        files = version['files']
        properties = version['properties']

        self.uri = AttributeDict({
            'asset': version['assetUri'],
            'asset_fallback': version['fallbackAssetUri'],
            'manifest': self._manifest_url(files),
            'vsix_package': self._vsix_package_uri(files),
        })

        self.version = version['version']
        self.code_engine = self._code_engine(properties)
        self.extension_pack = self._extension_pack(properties)
        self.extension_dependencies = self._extension_dependencies(properties)

        super().__init__(
            source_type=ExtensionSourceTypes.Marketplace,
            unique_id=self.unique_id,
            download_url=self.uri.vsix_package
        )

    # process extension attributes from the marketplace response

    def _manifest_url(self, files):
        key = 'assetType'
        value = 'Microsoft.VisualStudio.Code.Manifest'
        match = dict_from_list_key(files, key, value)
        return match['source'] if match else None

    def _vsix_package_uri(self, files):
        key = 'assetType'
        value = 'Microsoft.VisualStudio.Services.VSIXPackage'
        match = dict_from_list_key(files, key, value)
        return match['source'] if match else None

    def _code_engine(self, properties):
        key = 'key'
        value = 'Microsoft.VisualStudio.Code.Engine'
        match = dict_from_list_key(properties, key, value)
        return match['value'] if match else None

    def _extension_pack(self, properties):
        key = 'key'
        value = 'Microsoft.VisualStudio.Code.ExtensionPack'
        match = dict_from_list_key(properties, key, value)
        return match['value'] if match else None

    def _extension_dependencies(self, properties):
        key = 'key'
        value = 'Microsoft.VisualStudio.Code.ExtensionDependencies'
        match = dict_from_list_key(properties, key, value)
        return match['value'] if match else None



def get_extension(unique_id, release='latest'):
    """
    Creates an Extension instance, using either the VSCode Marketplace or
    GitHub, depending on the appropriate extension source.

    Arguments:
        unique_id {str} -- The unique id of the extension, which includes the
        publisher and package in the format of {publisher}.{package}

    Returns:
        Extension -- An instance of an Extension, either a GithubExtension or
        a MarketplaceExtension
    """
    e = _NON_MARKETPLACE_EXTENSIONS.get(unique_id)
    if e is None:
        return MarketplaceExtension(_MARKETPLACE.get_extension(unique_id))

    return GithubExtension(
        owner=e.owner,
        repo=e.repo,
        asset_name=e.asset_name,
        unique_id=unique_id,
        release=release
    )


# d = '/Users/taylor/Downloads/vsc-123'
# e = get_extension('twxs.cmake')

# e.download(d)