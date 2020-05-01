from __future__ import print_function

import requests
import json
import re

from textwrap import dedent
from datetime import datetime
from functools import reduce
from pyvsc._models import (
    ExtensionQueryFilterType,
    ExtensionQueryFlags
)

from pyvsc._util import (
    dict_from_list_key,
    human_number_format,
    shell_dimensions
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


    def _rating(self, x):
        return '{:0.2f}'.format(dict_from_list_key(
            x['statistics'], 'statisticName', 'weightedRating')['value'])


    def _installs(self, x):
        return human_number_format(float(dict_from_list_key(
            x['statistics'], 'statisticName', 'install')['value']))


    def _format_search_results(self, search_results):
        """
        Formats the results of the search query to prepare them for output.

        Arguments:
            search_results {list} -- A list of search query results
        """
        def formatted_date(d):
            dt = datetime.strptime(d, '%Y-%m-%dT%H:%M:%S.%fZ')
            date = dt.date()
            date = datetime.strptime(str(date), '%Y-%m-%d')
            return date.strftime('%-m/%d/%y')

        def unique_id(x):
            return '%s.%s' % \
                (x['extensionName'], x['publisher']['publisherName'])

        def last_updated(x):
            return formatted_date(x['versions'][0]['lastUpdated'])

        return [
            {
                'NAME': unique_id(x),
                'VERSION': x['versions'][0]['version'],
                'LAST UPDATE': last_updated(x),
                'RATING': self._rating(x),
                'INSTALLS': self._installs(x),
                'DESCRIPTION': x['shortDescription']
            } for x in search_results
        ]


    def _show_no_results(self):
        print('Your search didn\'t match any extensions.')
        return None


    def _print_search_results(self, search_results):
        """
        Prints the search results to the console.

        Arguments:
            search_results {list} -- A list of search results
        """
        if not search_results:
            return self._show_no_results()

        shell_height, shell_width = shell_dimensions()
        column_widths = [
            36,     # extension name
            7,      # version
            11,     # last update
            6,      # rating
            8,      # install count
            # description width is determined by remaining witdth
        ]

        description_width = shell_width - sum(column_widths) - 11
        column_widths.append(description_width)
        headers = search_results[0].keys()
        padded_headers = zip(column_widths * len(headers), headers)
        line_format_string = '%-*s  %*s  %*s  %*s  %*s   %-.*s'

        # Print the headers
        print(line_format_string % tuple([
            item for list in padded_headers for item in list]))

        # Print the results
        for result in search_results:
            values = result.values()
            padded_values = zip(column_widths * len(values), values)
            print(line_format_string % tuple([
                result for list in padded_values for result in list]))


    def get_extension_info(
        self,
        unique_id,
        flags = [ExtensionQueryFlags.AllAttributes]
    ):
        x = self.get_extension(unique_id, flags=flags)
        if not x:
            return self._show_no_results()

        output = '''
        {:20} {:20}
        {:20} {:20}
        {:20} {:20}

        {:40}
        {:40}

        {}
        '''.format(
            'Name: %s' % x['displayName'],
            'Publisher: %s' % x['publisher']['publisherName'],
            'Version: %s' % x['versions'][0]['version'],
            'Releases: %s' % len(x['versions']),
            'Rating: %s' % self._rating(x),
            'Installs: %s' % self._installs(x),
            'Categories: %s' % ', '.join(x['categories']),
            'Tags: %s' % (', '.join(list(filter(lambda t: not t.startswith('__'), x['tags'])))),
            x['shortDescription']
        )

        print(dedent(output))


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

        # format the search results
        results = self._format_search_results(extensions)
        self._print_search_results(results)
        return results
