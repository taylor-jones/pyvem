import requests
import json
import re

from functools import reduce
from pyvsc._models import (
    ExtensionQueryFilterType,
    ExtensionQueryFlags
)

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


    def get_extension(self, extensions_name, flags=[]):
        criteria = [
            {
                'filterType': ExtensionQueryFilterType.InstallationTarget,
                'value': 'Microsoft.VisualStudio.Code'
            },
            {
                'filterType': ExtensionQueryFilterType.Name,
                'value': extensions_name
            },
        ]

        extensions = self.extension_query(
            criteria=criteria, flags=flags or self.default_flags)
        return extensions[0] if extensions else None


    def search_extensions(self, search_text, page_size=25, flags=[]):
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




m = Marketplace()
e = m.get_extension('twxs.cmake')
# e = m.search_extensions('cpp')

from beeprint import pp
pp(e, max_depth=8, indent=2, width=200, sort_keys=True)
