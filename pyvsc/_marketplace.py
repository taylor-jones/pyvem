import requests
import json
import re

from functools import reduce
from pyvsc._models import ExtensionQueryFilterType, ExtensionQueryFlags

_MARKETPLACE_BASE_URL = 'https://marketplace.visualstudio.com'
_MARKETPLACE_API_VERSION = '6.0-preview.1'


class Marketplace():
    def __init__(
        self,
        base_url=_MARKETPLACE_BASE_URL,
        api_version=_MARKETPLACE_API_VERSION,
    ):
        self.base_url = base_url
        self.api_version = api_version
        self.default_flags = [
            ExtensionQueryFlags.AllAttributes,
            ExtensionQueryFlags.IncludeLatestVersionOnly,
        ]


    def _post(self, endpoint, data={}, headers={}):
        """
        Performs a post request to the marketplace gallery.
        
        Arguments:
            endpoint {str} -- The uri endpoint to append to the base url
        
        Keyword Arguments:
            data {dict} -- The data to pass in the post request
            headers {dict} -- The headers to pass in the post request
        
        Returns:
            Requests.response
        """
        url = '%s/_apis/public%s' % (self.base_url, endpoint)
        return requests.post(url, data=json.dumps(data), headers=headers)


    def extension_query(
        self,
        page_number=1,
        page_size=1,
        flags=[],
        criteria=[],
    ):
        """
        Query the marketplace for extensions

        Arguments:
            page_number {int} -- the which page of results to fetch
            page_size {int} -- how many results to fetch
            flags {list} -- list of ExtensionQueryFlags
            criteria {list} -- list of filter criteria objects

        Returns:
            list -- A list of extensions from the marketplace query
        """
        data = {
            'filters': [{
                'pageNumber': page_number,
                'pageSize': page_size,
                'criteria': criteria,
            }],
            'flags': reduce((lambda a, b: a | b), flags) if flags else 0
        }

        headers = {
            'Accept': 'application/json;api-version=%s' % (self.api_version),
            'Accept-Encoding': 'gzip',
            'Content-Type': 'application/json',
        }

        res = self._post('/gallery/extensionquery', data=data, headers=headers)
        if res.status_code != 200:
            return []

        parsed = res.json()
        return parsed['results'][0]['extensions']


    def get_extension(self, unique_id, flags=[]):
        """
        Get the marketplace response for a specific extension

        Arguments:
            unique_id {str} -- The extension id in the format of

        Keyword Arguments:
            flags {list} -- An optional list of ExtensionQueryFlags

        Returns:
            dict or None -- A dict from the JSON response of the HTTP request
                or None if no matching extension was found.
        """
        criteria = [
            {
                'filterType': ExtensionQueryFilterType.InstallationTarget,
                'value': 'Microsoft.VisualStudio.Code'
            },
            {
                'filterType': ExtensionQueryFilterType.Name,
                'value': unique_id
            },
        ]

        extensions = self.extension_query(
            criteria=criteria, flags=flags or self.default_flags)
        return extensions[0] if extensions else None


    def search_extensions(self, search_text, page_size=25, flags=[]):
        """
        Gets a list of search results from the VSCode Marketplace.
        
        Arguments:
            search_text {str} -- The text to use for searching
        
        Keyword Arguments:
            page_size {int} -- The number of results to return (default: {25})
            flags {list} -- A list of ExtensionQueryFlags
        
        Returns:
            list -- A list of extension result dicts
        """
        criteria = [
            {
                'filterType': ExtensionQueryFilterType.InstallationTarget,
                'value': 'Microsoft.VisualStudio.Code'
            },
            {
                'filterType': ExtensionQueryFilterType.SearchText,
                'value': search_text
            },
        ]

        extensions = self.extension_query(
            criteria=criteria,
            flags=flags or self.default_flags,
            page_size=page_size
        )

        return extensions



#######################################################################
# Test Commands
#######################################################################

from pyvsc._extension import Extension, MarketplaceExtension, GithubExtension
from beeprint import pp

m = Marketplace()

e = m.get_extension('twxs.cmake')

# e1 = m.get_extension('ms-azuretools.vscode-docker')        # has extensionDependencies
# e2 = m.get_extension('donjayamanne.python-extension-pack') # has extensionPath
# e3 = m.get_extension('ms-vscode.cpptools')

# e4 = m.search_extensions('cpptools', page_size=3)

# pp(e, max_depth=8, indent=2, width=200, sort_keys=True)

ext = MarketplaceExtension(e)
pp(ext, max_depth=8, indent=2, width=200, sort_keys=True)

