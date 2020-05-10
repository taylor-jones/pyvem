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


def resolved_path(p):
    """
    Resolves and normalizes a path by:
    - handling tilde expansion
    - handling variable expansion
    - removing relative segments
    - resolving symbolic links

    Arguments:
        p {str} -- A file-system path

    Returns:
        str
    """
    from os import path
    return path.realpath(path.normpath(path.expandvars(path.expanduser(p))))


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
    return path.abspath(path.expandvars(path.expanduser(p)))


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


def dict_from_list_key(the_list, key, value, default_response=None):
    """
    Returns the first item from a list of dicts where a specified key in the
    dict matches a specified value

    Arguments:
        the_list {list} -- The list to search
        key {str} -- The name of the key to check the value of
        value {str} -- The matching key value to search for

    Keyword Arguments:
        default_response {any} -- The prefered response to return if no match
            is found with the given arguments

    Returns:
        dict -- The matching dict or None if not found
    """
    data_type = type(the_list)
    if data_type is not list:
        raise AttributeError(
            'Expected a list, got a %s' % data_type.__name__)
    try:
        return next(x for x in the_list if x.get(key) == value)
    except TypeError:
        return default_response
    except Exception as e:
        print(e)
        return default_response


def human_number_format(number):
    """
    Formats a number into a more human-friendly format (e.g. 1000 = 1K)

    Arguments:
        number {int} -- A numeric value to convert

    Returns:
        str -- The human-friendly-formatted string version of the number
    """
    from math import log, floor
    units = ['', 'K', 'M', 'G', 'T', 'P']
    k = 1000.0
    magnitude = int(floor(log(number, k)))
    if magnitude == 0:
        return '%d%s' % (number / k**magnitude, units[magnitude])
    return '%.1f%s' % (number / k**magnitude, units[magnitude])


def shell_dimensions():
    """
    Returns the number of rows and columns visible in the current shell

    Returns:
        tuple(int, int)
    """
    from os import popen
    rows, columns = popen('stty size', 'r').read().split()
    return int(rows), int(columns)


def less(content):
    """
    Invokes a `less` subprocess, passing it content and receiving user
    stdin on the less process.

    Arguments:
        content {str} -- The content to display
    """
    from subprocess import Popen, PIPE
    process = Popen(["less"], stdin=PIPE)

    try:
        process.stdin.write(content)
        process.communicate()
    except TypeError:
        less(content.encode())


def iso_now(include_microseconds=False):
    """
    Returns an ISO timestamp of the current local time.
    
    Arguments:
        include_microseconds {bool} -- whether or not to include microseconds in
            the returned timestamp.

    Returns:
        str
    """
    from datetime import datetime
    if include_microseconds:
        return datetime.now().isoformat()
    return datetime.now().replace(microsecond=0).isoformat()
