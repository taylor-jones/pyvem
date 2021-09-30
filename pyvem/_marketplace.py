"""Connect to and query the VSCode marketplace."""

import json
from textwrap import dedent
from datetime import datetime
from functools import reduce

from rich.console import Console

from pyvem._logging import get_rich_logger
from pyvem._curler import CurledRequest
from pyvem._models import ExtensionQueryFilterType, ExtensionQueryFlags, ExtensionQuerySortByTypes
from pyvem._util import dict_from_list_key, human_number_format


_MARKETPLACE_BASE_URL = 'https://marketplace.visualstudio.com'
_MARKETPLACE_API_VERSION = '6.0-preview.1'
_MAERKETPLACE_DEFAULT_SEARCH_FLAGS = [
    ExtensionQueryFlags.AllAttributes,
    ExtensionQueryFlags.IncludeLatestVersionOnly,
]

_curled = CurledRequest()
_console = Console()
_LOGGER = get_rich_logger(__name__, console=_console)


class Marketplace():
    """
    The Marketplace class queries the VSCode Marketplace.
    """
    def __init__(self, tunnel=None):
        self.tunnel = tunnel


    def _post(self, endpoint, data=None, headers=None):
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
        curl_request = _curled.post(url, data=data or {}, headers=headers or {})
        return self.tunnel.run(curl_request)


    def _extension_query(
            self,
            page_number=1,
            page_size=1,
            flags=None,
            criteria=None,
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
                'criteria': criteria or [],
                'sortBy': sort_by,
            }],
            'flags': reduce((lambda a, b: a | b), flags) if flags else 0
        }

        headers = {
            'Accept': f'application/json;api-version={_MARKETPLACE_API_VERSION}',
            'Accept-Encoding': 'gzip',
            'Content-Type': 'application/json',
        }

        result = self._post('/gallery/extensionquery', data=data, headers=headers)

        if result.exited == 0:
            parsed = json.loads(result.stdout)
            target_property = 'results'

            if target_property in parsed.keys():
                return parsed[target_property][0]['extensions']
            return parsed['message']

        # check stderr
        _LOGGER.error(result.stderr)
        return []


    def get_extension(self, unique_id, flags=None, filters=None):
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
            }
        ]

        # Append any additional filters that were provided.
        for query_filter in filters or []:
            criteria.append(query_filter)

        extensions = self._extension_query(
            criteria=criteria,
            flags=flags or _MAERKETPLACE_DEFAULT_SEARCH_FLAGS
        )

        if isinstance(extensions, list) and len(extensions) > 0:
            return extensions[0]
        return extensions


    @staticmethod
    def _rating(result):
        return '{:0.2f}'.format(dict_from_list_key(
            list_to_search=result['statistics'],
            key='statisticName',
            value='weightedRating'
        )['value'])


    @staticmethod
    def _rating_count(result):
        count = dict_from_list_key(
            list_to_search=result['statistics'],
            key='statisticName',
            value='ratingcount'
        )
        return count['value'] if count else 0


    @staticmethod
    def _engine(result):
        return '%s' % dict_from_list_key(
            list_to_search=result['versions'][0]['properties'],
            key='key',
            value='Microsoft.VisualStudio.Code.Engine'
        )['value']


    @staticmethod
    def _dependencies(result):
        key = dict_from_list_key(
            list_to_search=result['versions'][0]['properties'],
            key='key',
            value='Microsoft.VisualStudio.Code.ExtensionDependencies'
        )
        return (key['value'] or 'None') if key else None


    @staticmethod
    def _extension_pack(result):
        key = dict_from_list_key(
            list_to_search=result['versions'][0]['properties'],
            key='key',
            value='Microsoft.VisualStudio.Code.ExtensionPack'
        )
        return (key['value'] or 'None') if key else None


    @staticmethod
    def _installs(result):
        return human_number_format(float(dict_from_list_key(
            list_to_search=result['statistics'],
            key='statisticName',
            value='install'
        )['value']))


    @staticmethod
    def _formatted_date(unformatted_date):
        try:
            date_time = datetime.strptime(unformatted_date, '%Y-%m-%dT%H:%M:%S.%fZ')
        except ValueError:
            try:
                date_time = datetime.strptime(unformatted_date, '%Y-%m-%dT%H:%M:%S:%fZ')
            except ValueError:
                date_time = datetime.strptime(unformatted_date, '%Y-%m-%dT%H:%M:%SZ')

        date = date_time.date()
        date = datetime.strptime(str(date), '%Y-%m-%d')
        return date.strftime('%-m/%d/%y')


    def _format_search_results(self, search_results):
        """
        Formats the results of the search query to prepare them for output.

        Arguments:
            search_results {list} -- A list of search query results
        """
        def _unique_id(result):
            return f'{result["publisher"]["publisherName"]}.{result["extensionName"]}'

        def _last_updated(result):
            return self._formatted_date(result['versions'][0]['lastUpdated'])

        def _description(result):
            key = 'shortDescription'
            return result[key] if key in result else ''

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


    def _show_no_results(self, text='Your search matched 0 extensions.'):
        _console.print(text)


    def get_extension_latest_version(self, unique_id, engine_version):
        flags = [ExtensionQueryFlags.IncludeLatestVersionOnly]

        filters = [{
            'filterType': ExtensionQueryFilterType.InstallationTargetVersion,
            'value': engine_version,
        }]

        response = self.get_extension(unique_id, flags=flags, filters=filters)

        if not response:
            return self._show_no_results()

        if isinstance(response, str):
            _LOGGER.error(response)

        return response


    def get_extension_info(self, unique_id, flags=None):
        """
        Display information from the VSCode Marketplace about a specific extension.

        Args:
            unique_id (str): The extension unique id
            flags (list, optional): Search flags. Defaults to [ExtensionQueryFlags.AllAttributes].

        Returns:
            None:
        """
        e = self.get_extension(unique_id, flags=flags or [ExtensionQueryFlags.AllAttributes])

        if not e:
            return self._show_no_results()

        if isinstance(e, str):
            _LOGGER.error('Could not get info for extension "%s". %s', unique_id, e)
            return

        def _tags(x):
            """
            Filter the list of extension tags, removing any that have names beginning
            with leading double underscores.

            Args:
                x (dict): A dictionary with a 'tags' attribute

            Returns:
                str: A comma-delimited, filtered list of extension tags
            """
            return ', '.join(list(filter(lambda t: not t.startswith('__'), x['tags'])))

        output = '''
        {:30} {:30}
        {:30} {:30}
        {:30} {:30}
        {:30} {:25}

        {:60}
        {:60}
        {:60}

        {:60}
        {:60}

        {}
        '''.format(
            'Name: %s' % e['displayName'],
            'Releases: %s' % len(e['versions']),
            'Publisher: %s' % e['publisher']['publisherName'],
            'Release Date: %s' % self._formatted_date(e['releaseDate']),
            'Latest Version: %s' % e['versions'][0]['version'],
            'Last Updated: %s' % self._formatted_date(e['lastUpdated']),
            'Rating: %s (%s)' % (self._rating(e), self._rating_count(e)),
            'Installs: %s' % self._installs(e),
            'Required VSCode Version: %s' % self._engine(e),
            'Extension Dependencies: %s' % self._dependencies(e),
            'Extension Pack: %s' % self._extension_pack(e),
            'Categories: %s' % ', '.join(e['categories']),
            'Tags: %s' % _tags(e),
            e['shortDescription']
        )

        print(dedent(output))


    def search_extensions(
            self,
            search_text,
            page_size=15,
            sort_by=ExtensionQuerySortByTypes.Relevance,
            flags=None,
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

        # format and return the search results
        return self._format_search_results(extensions)
