from __future__ import print_function
from __future__ import absolute_import

import json
import os

from pyvsc._util import dict_from_list_key
from pyvsc._containers import AttributeDict
from pyvsc._machine import platform_query
from pyvsc._marketplace import Marketplace
from pyvsc._curler import CurledRequest
from pyvsc._logging import get_rich_logger



_GITHUB_API_ROOT_URI = 'https://api.github.com'
_GITHUB_ROOT_URI = 'https://github.com'


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

_LOGGER = get_rich_logger(__name__)
_curled = CurledRequest()


class Extension():
    """
    Extension base class
    """

    def __init__(self, tunnel=None, **kwargs):
        self.tunnel = tunnel
        self.unique_id = kwargs.get('unique_id')
        self.download_url = kwargs.get('download_url')
        self.should_download_from_marketplace = \
            self.unique_id not in _NON_MARKETPLACE_EXTENSIONS.keys()


    def download(self, remote_dir, local_dir):
        """
        Download the .vsix extension.

        Communicate to the tunnel instance to download the extension on the
        remote machine and then copy it to the specified location on the
        local machine.

        Arguments:
            remote_dir {str} -- Absolute path to the download directory on the
                remote host
            local_dir {str} -- Absolute path to the download directory on the
                local host.

        Returns
            str -- The absolute path to the downloaded file on the local
            machine (if sucessful). If unsuccessful, returns False.

        """
        downloaded_extension_paths = []

        # Check for extension dependencies and extension pack items.
        num_dependencies = len(self.extension_dependencies)
        num_extension_pack = len(self.extension_pack)

        # Process any extension dependencies before the current extension.
        if num_dependencies > 0:
            _LOGGER.info('{} has {} extension dependencies.'.format(
                self.unique_id, num_dependencies))

            for index, extension in enumerate(self.extension_dependencies):
                downloaded_extension_paths.extend(
                    extension.download(remote_dir, local_dir))

            _LOGGER.debug('All {} dependencies processed'.format(
                self.unique_id))

        # Process extension pack items before the current extension.
        if num_extension_pack > 0:
            _LOGGER.info('{} has {} extensions in extension pack.'.format(
                self.unique_id, num_extension_pack))

            for index, extension in enumerate(self.extension_pack):
                downloaded_extension_paths.extend(
                    extension.download(remote_dir, local_dir))

            _LOGGER.debug('All {} extension pack extensions processed'.format(
                self.unique_id))

        # Download the current extension.
        extension_name = self.unique_id
        _LOGGER.info('Downloading {}'.format(extension_name))

        # If a specific version of the extension is known, append that version
        # to the name of the extension (for added specificity).
        if hasattr(self, 'version'):
            extension_name = '{}-{}'.format(extension_name, self.version)

        # In any case, append the .vsix extension to the extension file name.
        # .vsix is universal to all VSCode extensions.
        extension_file = '{}.vsix'.format(extension_name)

        # Specify the paths to where we'll download the extension on the remote
        # system and where we'll transfer it to on the local system.
        remote_path = os.path.join(remote_dir, extension_file)
        local_path = os.path.join(local_dir, extension_file)

        # Build the curled request and send it through the tunnel.
        curled_request = _curled.get(self.download_url, output=remote_path)
        response = self.tunnel.run(curled_request)

        # If the download request had any issues, then we won't try to transfer
        # the extension from the remote machine to the local machine.
        if response.exited != 0:
            _LOGGER.error('Failed to download {}.'.format(extension_name))
            _LOGGER.error(response.stderr)
            return False

        # Otherwise, we assume the request succeeded, so we'll try to transfer
        # the extension file.
        self.tunnel.get(remote_path, local_path)

        # Append the current extension's local path to the list of downloaded
        # extension paths that we'll pass back to the caller.
        downloaded_extension_paths.append(local_path)
        return downloaded_extension_paths



class GithubExtension(Extension):
    """
    GitHub extension class that inherits from Extension base class,
    but represents an extensions which has a GitHub download source.
    """
    def __init__(self, owner, repo, asset_name, release='latest',
                 prerelease=False, unique_id=None, tunnel=None):
        self.tunnel = tunnel
        self.unique_id = unique_id
        self.owner = owner
        self.repo = repo
        self.asset_name = asset_name
        self.release = release
        self.prerelease = prerelease
        self.download_url = (
            self._download_url_from_latest() if release == 'latest'
            else self._download_url_from_args())

        super().__init__(
            unique_id=self.unique_id,
            download_url=self.download_url,
            tunnel=self.tunnel,
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


    def _download_url_from_latest(self):
        """
        Get the download URL for the latest version of this extension.

        Build the extension download url by finding the latest extension that
        matches the system platform and release specifications.

        Returns:
            str -- The direct url from which the extension can be downlaoded
        """
        if not self.prerelease:
            # By default, GitHub's API only shows non-prerelease assets at the
            # 'latest' endpoint, so if we don't allow pre-releases, we can just
            # append 'latest' to our API URL and use the resulting asset.
            query_endpoint = '/repos/{}/{}/releases/{}?per_page=1'.format(
                self.owner, self.repo, self.release)
        else:
            # If we DO want to allow pre-release assets, we won't add 'latest'
            # to the end of our query URL, which will allow a prerelease asset
            # to be the first item in the list (if, in fact, a prerelease asset
            # exists and is the latest asset).
            #
            # Note that this will still fetch a non-prerelease/stable asset if
            # the latest asset is non-prerelsease/stable.
            query_endpoint = '/repos/{}/{}/releases?per_page=1'.format(
                self.owner, self.repo)

        # Build the query complete URL and the cURLed GET request, then
        # send the request via the tunnel connection provided to the extension.
        query_url = '{}{}'.format(_GITHUB_API_ROOT_URI, query_endpoint)
        curled_request = _curled.get(query_url)
        response = self.tunnel.run(curled_request)

        # If the GET request was successful, then parse the JSON response and
        # parse the asset's download URL.
        if response.exited == 0:
            response = json.loads(response.stdout)
            response_obj = response[0] if self.prerelease else response
            asset_list = response_obj['assets']
            return self._get_download_url_from_asset_list(asset_list)

        # Tunnel run request did not exit 0.
        _LOGGER.error(response.stderr)
        return None


    def _download_url_from_args(self):
        """
        Build the extension download url by joining the class arguments.

        Returns:
            str -- The direct url from which the extension can be downlaoded
        """
        query_endpoint = '/{}/{}/releases/download/{}/{}'.format(
            self.owner, self.repo, self.release, self.asset_name)
        return '{}{}'.format(_GITHUB_ROOT_URI, query_endpoint)



class MarketplaceExtension(Extension):
    """
    Marketplace extension class that inherits from Extension base class, but
    represents an extensions which has a VSCode Marketplace download source.
    """
    def __init__(self, parsed_marketplace_response, tunnel=None):
        # abbreviate the parsed response to make it easier to reference.
        p = parsed_marketplace_response

        # Keep a reference to the provided tunnel connection.
        self.tunnel = tunnel

        # Get references to the extension attributes we need.
        self.extension_id = p['extensionId']
        self.extension_name = p['extensionName']
        self.display_name = p['displayName']
        self.publisher_name = p['publisher']['publisherName']
        self.unique_id = '%s.%s' % (self.publisher_name, self.extension_name)
        self.description = p['shortDescription']
        self.stats = p['statistics']

        # Some attributes are nested. We don't need to store these nested
        # objects directly, but we need them to find the values of other
        # attributes that we do want to store.
        version = p['versions'][0]
        files = version['files']
        properties = version['properties']

        # TODO: We may not need all this URI information.
        self.uri = AttributeDict({
            'asset': version['assetUri'],
            'asset_fallback': version['fallbackAssetUri'],
            'manifest': self._manifest_url(files),
            'vsix_package': self._vsix_package_uri(files),
        })

        # The version of the extension, itself.
        self.version = version['version']

        # The code engine specifies the minimum version of VSCode that this
        # extension is specified to work on.
        self.code_engine = self._code_engine(properties)

        # Find out if this is an extension pack. If so, we'll need to download
        # each of the extensions in the pack whenever this extension downloads.
        self.extension_pack = self._extension_pack(properties)

        # Find out if this extension has dependencis. If so, we'll need to
        # download and install each of the dependencies before we download/
        # install this extension.
        self.extension_dependencies = self._extension_dependencies(properties)

        super().__init__(
            unique_id=self.unique_id,
            download_url=self.uri.vsix_package,
            tunnel=self.tunnel
        )


    def _manifest_url(self, files):
        """
        Read the extension files to determine the URI to the manifset
        file for this extension. If desired, an additional request could
        be made to the manifest_url to get additional informatino about the
        extension.

        Arguments:
            files {list} -- A list of extension files associated with this
            extension. This comes from the JSON response that resulted from
            querying this extension in the VSCode Extension Marketplace.

        Returns:
            str -- The URI of the manifest file for the current extension.
        """
        key = 'assetType'
        value = 'Microsoft.VisualStudio.Code.Manifest'
        match = dict_from_list_key(files, key, value)
        return match['source'] if match else None


    def _vsix_package_uri(self, files):
        """
        Read the extension files to determine the URI to the .VSIXPackage
        file (which is an alias for the .vsix) for this extension. This is
        the URI of where the extension can be downloaded.

        Arguments:
            files {list} -- A list of extension files associated with this
            extension. This comes from the JSON response that resulted from
            querying this extension in the VSCode Extension Marketplace.

        Returns:
            str -- The URI of where the .vsix can be downloaded from the
            VSCode Marketplace.
        """
        key = 'assetType'
        value = 'Microsoft.VisualStudio.Services.VSIXPackage'
        match = dict_from_list_key(files, key, value)
        return match['source'] if match else None


    def _code_engine(self, properties):
        """
        Read the extension properties to determine which VSCode engine
        is required for this extension (at it's current/specified version).

        Arguments:
            properties {list} -- A list of extension properties from the
            JSON response that resulted from querying this extension in
            the VSCode Extension Marketplace

        Returns:
            str -- The version of VSCode required for this extension.
        """
        key = 'key'
        value = 'Microsoft.VisualStudio.Code.Engine'
        match = dict_from_list_key(properties, key, value)
        return match['value'] if match else None


    def _extension_pack(self, properties):
        """
        Read the extension properties to determine which VSCode extensions are
        included in this extension pack (if any). Return a list of Extension
        objects corresponding to each of the extensions in the extension pack.

        NOTE: Only Extensions which are extension packs will have any value
        here.

        Arguments:
            properties {list} -- A list of extension properties from the
            JSON response that resulted from querying this extension in
            the VSCode Extension Marketplace

        Returns:
            list -- A list of Extension objects, one for each named extension
            in the extension pack property value for this extension.
        """

        key = 'key'
        value = 'Microsoft.VisualStudio.Code.ExtensionPack'
        match = dict_from_list_key(properties, key, value)
        extension_pack = []

        if match:
            extension_pack_string = match['value']
            extension_names = [x for x in extension_pack_string.split(',') if x]

            # Create a new Extension instance for each of the extensions in the
            # extension pack and append those Extension objects to the
            # extension_pack list.
            for name in extension_names:
                extension_pack.append(get_extension(name, self.tunnel))

        return extension_pack


    def _extension_dependencies(self, properties):
        key = 'key'
        value = 'Microsoft.VisualStudio.Code.ExtensionDependencies'
        match = dict_from_list_key(properties, key, value)
        dependencies = []

        if match:
            dependencies_string = match['value']
            extension_names = [x for x in dependencies_string.split(',') if x]

            # Create a new Extension instance for each of the extensions and 
            # append those Extension objects to the dependencies list.
            for name in extension_names:
                dependencies.append(get_extension(name, self.tunnel))

        return dependencies




def get_extension(
    unique_id,
    tunnel=None,
    release='latest',
    use_marketplace_only=False
):
    """
    Creates an Extension instance, using either the VSCode Marketplace or
    GitHub, depending on the appropriate extension source.

    Arguments:
        unique_id {str} -- The unique id of the extension, which includes the
            publisher and package in the format of {publisher}.{package}
        tunnel {Tunnel} -- SSH Tunnel instance
        release {str} -- The desired release version (default: 'latest')

    Returns:
        Extension -- An instance of an Extension, either a GithubExtension or
        a MarketplaceExtension
    """
    non_marketplace_extension = _NON_MARKETPLACE_EXTENSIONS.get(unique_id)

    if non_marketplace_extension is None or use_marketplace_only:
        return MarketplaceExtension(
            Marketplace(tunnel=tunnel).get_extension(unique_id),
            tunnel=tunnel
        )

    return GithubExtension(
        owner=non_marketplace_extension.owner,
        repo=non_marketplace_extension.repo,
        asset_name=non_marketplace_extension.asset_name,
        unique_id=unique_id,
        release=release,
        tunnel=tunnel,
    )
