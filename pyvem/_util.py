"""Misc utility functions"""

import datetime
import math
import os
import socket
import subprocess
from typing import List, Dict, Any


def props(cls):
    """
    Return the non-local/non-"private" class key names.

    Returns:
        Class -- A class
    """
    return [i for i in cls.__dict__.keys() if i[:1] != '_']


def get_public_attributes(obj: Dict[str, Any]) -> Dict[str, Any]:
    """
    Return a dict containing only the non-underscored attributes from
    an object

    Arguments:
        obj {dict} -- A dict
    """
    attributes = {}
    for key, value in obj.__dict__.items():
        if not key.startswith('_'):
            attributes[key] = value
    return attributes


def resolved_path(path: str) -> str:
    """
    Resolve and normalize a path by:
    - handling tilde expansion
    - handling variable expansion
    - removing relative segments
    - resolving symbolic links

    Arguments:
        path -- A file-system path

    Returns:
        str
    """
    return os.path.realpath(os.path.expandvars(os.path.expanduser(path)))


def expanded_path(path: str) -> str:
    """
    Expand a path to resolve variables, home directory, and relative paths
    and returns an absolute path.

    Arguments:
        path -- A file-system path

    Returns:
        An expanded file-system path, regardless of whether or not the path
        actually exists.
    """
    return os.path.abspath(os.path.expandvars(os.path.expanduser(path)))


def has_internet_connection() -> bool:
    """Check if the system currently has a functioning internet connection"""
    try:
        host = socket.gethostbyname('1.1.1.1')
        sock = socket.create_connection((host, 80), 2)
        sock.close()
        return True
    except OSError:
        return False


def truthy_list(list_to_filter) -> List[Any]:
    """Removes "falsy" elements from a list"""
    return list(filter(None, list_to_filter))


def dict_from_list_key(list_to_search: List[Any], key: str, value: str,
                       default_response: Any = None) -> Dict[str, Any]:
    """
    Return the first item from a list of dicts where a specified key in the
    dict matches a specified value

    Arguments:
        list_to_search -- The list to search
        key -- The name of the key to check the value of
        value -- The matching key value to search for

    Keyword Arguments:
        default_response -- Value to return if no match is found

    Returns:
        dict -- The matching dict or None if not found
    """

    if not isinstance(list_to_search, List):
        raise AttributeError('Expected a list, got a '
                             f'{type(list_to_search).__name__}')

    try:
        return next(x for x in list_to_search if x.get(key) == value)
    except TypeError:
        return default_response
    except (KeyError, AttributeError, ValueError, StopIteration) as err:
        print(repr(err))
        return default_response


def human_number_format(number):
    """
    Format a number into a more human-friendly format (e.g. 1000 = 1K)

    Arguments:
        number {int} -- A numeric value to convert

    Returns:
        str -- The human-friendly-formatted string version of the number
    """
    units = ['', 'K', 'M', 'G', 'T', 'P']
    k = 1000.0
    magnitude = int(math.floor(math.log(number, k)))

    if magnitude == 0:
        return f'{number / k**magnitude}{units[magnitude]}'
    return f'{(number / k**magnitude):.1f}{units[magnitude]}'


def shell_dimensions():
    """
    Return the number of rows and columns visible in the current shell

    Returns:
        tuple(int, int)
    """
    with subprocess.Popen(['stty', 'size'],
                          stdout=subprocess.PIPE,
                          encoding='utf-8') as proc:
        rows, columns = proc.stdout.readline().split(' ')
        return int(rows), int(columns)


def iso_now(include_microseconds=False, format_for_path=True):
    """
    Return an ISO timestamp of the current local time.

    Arguments:
        include_microseconds {bool} -- whether or not to include microseconds
        in the returned timestamp.

    Returns:
        str
    """
    if include_microseconds:
        output = datetime.datetime.now().isoformat()
    else:
        output = datetime.datetime.now().replace(microsecond=0).isoformat()

    if format_for_path:
        output = output.replace(':', '')

    return output


def delimit(iterable, delimiter=', ', falsy_return_value=''):
    """
    Returns a delimited string from an iterable, if the iterable is able
    to be successfully delimited. If not, returns a default falsy return
    value.

    Arguments:
        iterable {Iterable} -- An iterable python type (e.g. list, set, etc.)

    Keyword Arguments:
        delimiter {str} -- The delimiter to use between items in the delimited
            string (default: {', '})
        falsy_return_value {str} -- The value to return if the iterable
            is not able to be delimited, is None or otherwise falsy
            (default: {''})

    Returns:
        str
    """
    try:
        return delimiter.join(iterable)
    except (TypeError, AttributeError):
        return falsy_return_value


def get_confirmation(question):
    """
    Prompts for a "yes" or "no" answer until one is received.

    Arguments:
        question {str} -- The prompt question

    Returns:
        bool -- True if the user answered "yes". False if "no"
    """
    question = f'{question} [y/n]: '
    answer = None
    while answer not in ['y', 'yes', 'n', 'no']:
        answer = str(input(question)).lower().strip()
    return answer[0] == 'y'


def get_response(prompt: str, default: str = None) -> str:
    """
    Prompts the user for a response.

    If a default value is provided, the user is allowed to provide an empty
    response, which will return the default. If no default value is provided,
    the function continues to prompt the user until a non-empty response is
    provided.

    Arguments:
        prompt -- The prompt text
        default -- The default value to include in the prompt, which will be
            the value returned if the user does not otherwise provde a response

    Returns:
        A non-empty response from the user
    """
    if default:
        prompt = f'{prompt} ({default}): '
    else:
        prompt = f'{prompt}: '

    answer = None
    while not answer or len(answer) == 0:
        answer = str(input(prompt)).strip() or default
    return answer
