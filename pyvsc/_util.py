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


def get_public_attributes(obj):
    """
    Returns a dict containing only the non-underscored attributes from
    an object
    
    Arguments:
        obj {dict} -- A dict
    """
    attributes = {}
    for k, v in obj.__dict__.items():
        if not k.startswith('_'):
            attributes[k] = v
    return attributes


def expanded_path(p):
    """
    Expands a path to resolve variables, home directory, and relative paths
    and returns an absolute path.
    
    Arguments:
        p {str} -- A file-system path
    
    Returns:
        str -- An expanded file-system path, regardless of whether or not the
            path actually exists.
    """
    from os import path
    try:
        return path.abspath(path.expandvars(path.expanduser(p)))
    except Exception as e:
        _LOGGER.error(e)


def has_internet_connection():
    """
    Checks if the system currently has a functioning internet connection

    Returns:
        bool
    """
    import socket
    try:
        host = socket.gethostbyname('1.1.1.1')
        s = socket.create_connection((host, 80), 2)
        s.close()
        return True
    except OSError:
        return False
    except Exception as e:
        _LOGGER.error(e)


def truthy_list(the_list):
    """
    Removes "falsy" elements from a list, leaving only the elements that
    evaluate to True
    
    Arguments:
        the_list {list} -- The list to filter
    
    Returns:
        list -- The filtered list
    """
    return list(filter(None, the_list))