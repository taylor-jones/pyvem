"""Connect to and query the VSCode marketplace."""

import json
from textwrap import dedent
from datetime import datetime
from functools import reduce
from typing import Dict, List, Any
from numbers import Number

from rich.console import Console

from pyvem._logging import get_rich_logger
from pyvem._curler import CurledRequest
from pyvem._util import dict_from_list_key, human_number_format
from pyvem._models import (
    ExtensionQueryFilterType,
    ExtensionQueryFlags,
    ExtensionQuerySortByTypes
)

_MARKETPLACE_BASE_URL = 'https://marketplace.visualstudio.com'
_MARKETPLACE_API_VERSION = '6.0-preview.1'
_MARKETPLACE_DEFAULT_FLAGS = [
    ExtensionQueryFlags.AllAttributes,
    ExtensionQueryFlags.IncludeLatestVersionOnly,
]

_CONSOLE = Console()
_LOGGER = get_rich_logger(__name__, console=_CONSOLE)


class Marketplace():
    """The Marketplace class queries the VSCode Marketplace."""

    def __init__(self, tunnel=None):
        self.tunnel = tunnel
        self.request_curler = CurledRequest()


    def _post(self,
              endpoint: str,
              data: Dict[str, str] = None,
              headers: Dict[str, str] = None):
        """
        Performs a post request to the marketplace gallery.

        Arguments:
            endpoint -- The uri endpoint to append to the base url

        Keyword Arguments:
            data -- The data to pass in the post request
            headers -- The headers to pass in the post request

        Returns:
            Requests.response
        """
        url = f'{_MARKETPLACE_BASE_URL}/_apis/public{endpoint}'
        curl_req = self.request_curler.post(url, data=data or {},
                                            headers=headers or {})
        return self.tunnel.run(curl_req)


    def _extension_query(self,
                         page_number: int = 1,
                         page_size: int = 1,
                         flags: List[int] = None,
                         criteria=None,
                         sort_by: int = ExtensionQuerySortByTypes.Relevance):
        """
        Query the marketplace for extensions

        Arguments:
            page_number -- which page # of results to fetch
            page_size -- how many results to fetch
            flags -- list of ExtensionQueryFlags
            criteria -- list of filter criteria objects

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
            'Accept': 'application/json;api-version='
                      f'{_MARKETPLACE_API_VERSION}',
            'Accept-Encoding': 'gzip',
            'Content-Type': 'application/json',
        }

        result = self._post('/gallery/extensionquery', data=data,
                            headers=headers)

        if result.exited == 0:
            parsed = json.loads(result.stdout)
            target_property = 'results'

            if target_property in parsed.keys():
                return parsed[target_property][0]['extensions']
            return parsed['message']

        # check stderr
        _LOGGER.error(result.stderr)
        return []


    def get_extension(self,
                      unique_id: str,
                      flags: List[int] = _MARKETPLACE_DEFAULT_FLAGS,
                      filters: List[int] = None) -> Dict[str, Any]:
        """
        Get the marketplace response for a specific extension

        Arguments:
            unique_id -- The extension id

        Keyword Arguments:
            flags -- An optional list of ExtensionQueryFlags

        Returns:
            dict or None -- A dict from the JSON response of the HTTP request
                or None if no matching extension was found.
        """
        criteria = [{
            'filterType': ExtensionQueryFilterType.InstallationTarget,
            'value': 'Microsoft.VisualStudio.Code'
        }, {
            'filterType': ExtensionQueryFilterType.Name,
            'value': unique_id
        }]

        # Append any additional filters that were provided.
        for query_filter in filters or []:
            criteria.append(query_filter)

        extensions = self._extension_query(criteria=criteria, flags=flags)

        if isinstance(extensions, list) and len(extensions) > 0:
            return extensions[0]
        return extensions


    @staticmethod
    def _short_description(result: Dict[str, Any]) -> str:
        try:
            return result['shortDescription']
        except KeyError:
            return ''

    @staticmethod
    def _rating(result: Dict[str, Any]) -> Number:
        return '{:0.2f}'.format(dict_from_list_key(
            list_to_search=result['statistics'],
            key='statisticName',
            value='weightedRating'
        )['value'])

    @staticmethod
    def _rating_count(result: Dict[str, Any]) -> Number:
        count = dict_from_list_key(
            list_to_search=result['statistics'],
            key='statisticName',
            value='ratingcount'
        )
        return count['value'] if count else 0

    @staticmethod
    def _engine(result: Dict[str, Any]) -> str:
        return '%s' % dict_from_list_key(
            list_to_search=result['versions'][0]['properties'],
            key='key',
            value='Microsoft.VisualStudio.Code.Engine'
        )['value']

    @staticmethod
    def _dependencies(result: Dict[str, Any]) -> List[Dict[str, Any]]:
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
            date_time = datetime.strptime(unformatted_date,
                                          '%Y-%m-%dT%H:%M:%S.%fZ')
        except ValueError:
            try:
                date_time = datetime.strptime(unformatted_date,
                                              '%Y-%m-%dT%H:%M:%S:%fZ')
            except ValueError:
                date_time = datetime.strptime(unformatted_date,
                                              '%Y-%m-%dT%H:%M:%SZ')

        date = date_time.date()
        date = datetime.strptime(str(date), '%Y-%m-%d')
        return date.strftime('%-m/%d/%y')


    def _format_search_results(self, search_results):
        """
        Formats the results of the search query to prepare them for output.

        Arguments:
            search_results {list} -- A list of search query results
        """
        def _unique_id(ext):
            return f'{ext["publisher"]["publisherName"]}.{ext["extensionName"]}'

        def _last_updated(ext):
            return self._formatted_date(ext['versions'][0]['lastUpdated'])

        return [{
            'EXTENSION ID': _unique_id(x),
            'VERSION': x['versions'][0]['version'],
            'LAST UPDATE': _last_updated(x),
            'RATING': self._rating(x),
            'INSTALLS': self._installs(x),
            'DESCRIPTION': self._short_description(x),
        } for x in search_results]


    def get_extension_latest_version(self, unique_id: str, engine_version: str):
        flags = [ExtensionQueryFlags.IncludeLatestVersionOnly]
        filters = [{
            'filterType': ExtensionQueryFilterType.InstallationTargetVersion,
            'value': engine_version,
        }]

        response = self.get_extension(unique_id, flags=flags, filters=filters)

        if not response:
            _CONSOLE.print('Your search returned 0 extensions')
            return

        if isinstance(response, str):
            _LOGGER.error(response)

        return response


    def show_extension_info(self, unique_id: str,
                            flags: List[int] = [
                                ExtensionQueryFlags.AllAttributes]):
        """
        Display information from the VSCode Marketplace about an extension.

        Args:
            unique_id: The extension unique id
            flags: Search flags.

        Returns:
            None
        """
        ext = self.get_extension(unique_id, flags=flags)

        if not ext:
            _CONSOLE.print('Your search returned 0 extensions')
            return

        if isinstance(ext, str):
            _LOGGER.error('Could not get info for extension "%s". %s',
                          unique_id, ext)
            return

        def _tags(extension):
            """
            Filter the list of extension tags, removing any that have names
            beginning with leading double underscores.

            Args:
                x (dict): A dictionary with a 'tags' attribute

            Returns:
                str: A comma-delimited, filtered list of extension tags
            """
            try:
                return ', '.join(list(filter(lambda t: not t.startswith('__'),
                                            extension['tags'])))
            except KeyError:
                return ''

        name = 'Name: ' + ext['displayName']
        num_releases = 'Releases: ' + str(len(ext['versions']))
        publisher = 'Publisher: ' + ext['publisher']['publisherName']
        release_date = 'Release Date: ' + self._formatted_date(ext['releaseDate'])
        latest_version = 'Latest Version: ' + str(ext['versions'][0]['version'])
        last_updated = 'Last Updated: ' + self._formatted_date(ext['lastUpdated'])

        rating_value = str(self._rating(ext))
        num_ratings = str(self._rating_count(ext))
        rating = 'Rating: ' + rating_value + '(' + num_ratings + ')'

        installs = 'Installs: ' + str(self._installs(ext))
        required_engine = 'Required VSCode Engine: ' + self._engine(ext)
        dependencies = 'Extension Dependencies: ' + self._dependencies(ext)
        extension_pack = 'Extension Pack: ' + self._extension_pack(ext)
        categories = 'Categories: ' + ', '.join(ext['categories'])
        tags = 'Tags: ' + _tags(ext)
        description = self._short_description(ext)

        output = (
            f'{name:30} {num_releases:30}\n'
            f'{publisher:30} {release_date:30}\n'
            f'{latest_version:30} {last_updated:30}\n'
            f'{rating:30} {installs:25}\n'
            f'\n'
            f'{required_engine:60}\n'
            f'{dependencies:60}\n'
            f'{extension_pack:60}\n'
            f'\n'
            f'{categories:60}\n'
            f'{tags:60}\n'
            f'\n'
            f'{description}'
        )

        print(dedent(output).strip() + '\n')


    def search_extensions(self,
                          search_text: str,
                          page_size: int = 15,
                          sort_by: int = ExtensionQuerySortByTypes.Relevance,
                          flags: List[int] = _MARKETPLACE_DEFAULT_FLAGS,
                          **kwargs):
        """
        Gets a list of search results from the VSCode Marketplace.

        Arguments:
            search_text -- The text to use for searching

        Keyword Arguments:
            page_size -- The number of results to return
            flags -- A list of ExtensionQueryFlags

        Returns:
            list -- A list of extension result dicts
        """
        criteria = [{
            'filterType': ExtensionQueryFilterType.InstallationTarget,
            'value': 'Microsoft.VisualStudio.Code'
        }, {
            'filterType': ExtensionQueryFilterType.SearchText,
            'value': search_text
        }]

        # Add additional filters to the criteria based on arguments
        for category in kwargs.get('categories', []):
            criteria.append({
                'filterType': ExtensionQueryFilterType.Category,
                'value': category,
            })

        extensions = self._extension_query(criteria=criteria, flags=flags,
                                           page_size=page_size, sort_by=sort_by)

        # format and return the search results
        return self._format_search_results(extensions)
