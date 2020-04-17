from __future__ import print_function
import os
import logging

_LOGGER = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s]\t%(module)s::%(funcName)s:%(lineno)d | %(message)s'
)


_EXT_EXT = 'vsix'


def get_directory_vsix_files(d):
    try:
        return [f for f in os.listdir(d) if f.endswith(_EXT_EXT)]
    except OSError:
        return []
    except Exception as e:
        _LOGGER.error(e)
