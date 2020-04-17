from __future__ import print_function
import os
import logging

_LOGGER = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s]\t%(module)s::%(funcName)s:%(lineno)d | %(message)s'
)


class AttributeDict(dict):
    """
    Simple dot.notation access to dictionary attributes
    """
    __getattr__ = dict.get
    __setattr__ = dict.__setitem__
    __delattr__ = dict.__delitem__


def dir_exists(d):
    try:
        d = os.path.expanduser(d)
        d = os.path.abspath(d)
        return os.path.isdir(d)
    except OSError as e:
        return False
    except Exception as e:
        _LOGGER.warning(e)

