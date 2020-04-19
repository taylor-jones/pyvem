from __future__ import print_function
import re
import os
import logging

_LOGGER = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s]\t%(module)s::%(funcName)s:%(lineno)d | %(message)s'
)


_EXTENSION_ENGINE_RE = re.compile('^(?P<constraint>=|>=|<=|=>|=<|>|<|!=|~|~>|\^)?(?P<major>0|[1-9]\d*)\.(?P<minor>0|[1-9]\d*)\.(?P<patch>0|[1-9]\d*)(?:-(?P<prerelease>(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*)(?:\.(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*))*))?(?:\+(?P<buildmetadata>[0-9a-zA-Z-]+(?:\.[0-9a-zA-Z-]+)*))?$')



_EXT_EXT = 'vsix'


class Extension():
    def __init__(self, parsed_json):
        p = parsed_json

        self.extension_id = p['extensionId']
        self.extension_name = p['extensionName']
        self.publisher_name = p['publisherName']
        self.unique_id = '%s.%s' % (self.publisher_name, self.extension_name)
        self.description = p['shortDescription']
        self.stats = p['statistics']

        self.uri = {
            'asset': p['versions']['assetUri'],
            'asset_fallback': p['versions']['fallbackAssetUri'],
        }
    
    def _set_uid(self, ext_name, publisher_name):
        self.uid = '%s.%s' % ()




def get_directory_vsix_files(d):
    try:
        return [f for f in os.listdir(d) if f.endswith(_EXT_EXT)]
    except OSError:
        return []
    except Exception as e:
        _LOGGER.error(e)
