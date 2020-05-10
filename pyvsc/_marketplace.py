from __future__ import print_function, absolute_import

import json
import re

from textwrap import dedent
from datetime import datetime
from functools import reduce
from rich.console import Console

from pyvsc._curler import CurledRequest
from pyvsc._models import (
    ExtensionQueryFilterType,
    ExtensionQueryFlags,
    ExtensionQuerySortByTypes,
)
from pyvsc._util import (
    dict_from_list_key,
    human_number_format,
    shell_dimensions,
)


_MARKETPLACE_BASE_URL = 'https://marketplace.visualstudio.com'
_MARKETPLACE_API_VERSION = '6.0-preview.1'
_MAERKETPLACE_DEFAULT_SEARCH_FLAGS = [
    ExtensionQueryFlags.AllAttributes,
    ExtensionQueryFlags.IncludeLatestVersionOnly,
]

_curled = CurledRequest()
_console = Console()

class Marketplace():
    def __init__(self, tunnel=None):
        self.tunnel = tunnel


    def _post(self, endpoint, data={}, headers={}, **kwargs):
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
        url = '%s/_apis/public%s' % (_MARKETPLACE_BASE_URL, endpoint)
        curl_request = _curled.post(url, data=data, headers=headers)
        return self.tunnel.run(curl_request)


    def _extension_query(
        self,
        page_number=1,
        page_size=1,
        flags=[],
        criteria=[],
        sort_by=ExtensionQuerySortByTypes.Relevance,
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
                'sortBy': sort_by,
            }],
            'flags': reduce((lambda a, b: a | b), flags) if flags else 0
        }

        headers = {
            'Accept': 'application/json;api-version=%s' % \
                _MARKETPLACE_API_VERSION,
            'Accept-Encoding': 'gzip',
            'Content-Type': 'application/json',
        }

        result = self._post(
            '/gallery/extensionquery',
            data=data,
            headers=headers,
            compressed=False
        )

        if result.exited == 0:
            parsed = json.loads(result.stdout)
            
            if isinstance(parsed, dict):
                return parsed['message']
            elif isinstance(parsed, list):
                return parsed['results'][0]['extensions']
        else:
            # check stderr
            print(result.stderr)
            return []


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

        extensions = self._extension_query(
            criteria=criteria,
            flags=flags or _MAERKETPLACE_DEFAULT_SEARCH_FLAGS
        )

        if isinstance(extensions, list):
            return extensions[0]
        elif isinstance(extensions, str):
            return extensions

        return None


    def _rating(self, x):
        return '{:0.2f}'.format(dict_from_list_key(
            x['statistics'], 'statisticName', 'weightedRating')['value'])


    def _rating_count(self, x):
        count = dict_from_list_key(
            x['statistics'],
            'statisticName',
            'ratingcount'
        )

        return count['value'] if count else 0


    def _engine(self, x):
        return '%s' % dict_from_list_key(
            x['versions'][0]['properties'],
            'key',
            'Microsoft.VisualStudio.Code.Engine'
        )['value']


    def _dependencies(self, x):
        key = dict_from_list_key(
            x['versions'][0]['properties'],
            'key',
            'Microsoft.VisualStudio.Code.ExtensionDependencies',
        )

        return (key['value'] or 'None') if key else None


    def _installs(self, x):
        return human_number_format(float(dict_from_list_key(
            x['statistics'], 'statisticName', 'install')['value']))


    def _formatted_date(self, d):
        try:
            dt = datetime.strptime(d, '%Y-%m-%dT%H:%M:%S.%fZ')
        except ValueError:
            try:
                dt = datetime.strptime(d, '%Y-%m-%dT%H:%M:%S:%fZ')
            except ValueError:
                dt = datetime.strptime(d, '%Y-%m-%dT%H:%M:%SZ')

        date = dt.date()
        date = datetime.strptime(str(date), '%Y-%m-%d')
        return date.strftime('%-m/%d/%y')


    def _format_search_results(self, search_results):
        """
        Formats the results of the search query to prepare them for output.

        Arguments:
            search_results {list} -- A list of search query results
        """
        def _unique_id(x):
            return '%s.%s' % \
                (x['publisher']['publisherName'], x['extensionName'])

        def _last_updated(x):
            return self._formatted_date(x['versions'][0]['lastUpdated'])

        def _description(x):
            key = 'shortDescription'
            return x[key] if key in x else ''

        return [
            {
                'EXTENSION ID': _unique_id(x),
                'VERSION': x['versions'][0]['version'],
                'LAST UPDATE': _last_updated(x),
                'RATING': self._rating(x),
                'INSTALLS': self._installs(x),
                'DESCRIPTION': _description(x),
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
            40,     # extension name
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
        print('')
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
        ex = self.get_extension(unique_id, flags=flags)
        if not ex:
            return self._show_no_results()
        elif isinstance(ex, str):
            return _console.print('[red]{text}[/red]'.format(text=ex))

        def _tags(x):
            return ', '.join(list(filter(
                lambda t: not t.startswith('__'), x['tags'])))

        # TODO: Implement a rich Table instance here

        output = '''
        {:30} {:30}
        {:30} {:30}
        {:30} {:30}
        {:30} {:25}

        {:60}
        {:60}

        {:60}
        {:60}

        {}
        '''.format(
            'Name: %s' % ex['displayName'],
            'Releases: %s' % len(ex['versions']),
            'Publisher: %s' % ex['publisher']['publisherName'],
            'Release Date: %s' % self._formatted_date(ex['releaseDate']),
            'Latest Version: %s' % ex['versions'][0]['version'],
            'Last Updated: %s' % self._formatted_date(ex['lastUpdated']),
            'Rating: %s (%s)' % (self._rating(ex), self._rating_count(ex)),
            'Installs: %s' % self._installs(ex),
            'Required VSCode Version: %s' % self._engine(ex),
            'Extension Dependencies: %s' % self._dependencies(ex),
            'Categories: %s' % ', '.join(ex['categories']),
            'Tags: %s' % _tags(ex),
            ex['shortDescription']
        )

        print(dedent(output))


    def search_extensions(
        self,
        search_text,
        page_size=15,
        sort_by=ExtensionQuerySortByTypes.Relevance,
        flags=[],
        **kwargs,
    ):
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

        # Add additional filters to the criteria based on arguments
        for category in kwargs.get('categories', []):
            criteria.append({
                'filterType': ExtensionQueryFilterType.Category,
                'value': category,
            })

        extensions = self._extension_query(
            criteria=criteria,
            flags=flags or _MAERKETPLACE_DEFAULT_SEARCH_FLAGS,
            page_size=page_size,
            sort_by=sort_by,
        )

        # format the search results
        results = self._format_search_results(extensions)
        self._print_search_results(results)
        return results
