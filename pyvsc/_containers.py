from __future__ import print_function, absolute_import

import re
import base64
from uuid import uuid4
from cryptography.fernet import Fernet

from collections import namedtuple
from pyvsc._config import _DEFAULT_SSH_PORT, _DEFAULT_SSH_USER
from pyvsc._util import AttributeDict



# Regex pattern to parse the components of a SSH connection string.
CONNECTION_STRING_RE_PATTERN = re.compile(
    r'(?:(?P<username>.*?)'
    r'(?::(?P<password>.*?)|)@)?'
    r'(?P<hostname>[^:\/\s]+)'
    r'(?::(?P<port>\d+))?'
)

def ConnectionParts(hostname, username=None, port=None, password=None):
    """
    Wrapper around an AttributeDict that allows for mutable connection
    string components.

    Arguments:
        hostname {str} -- remote hostname

    Keyword Arguments:
        username {str} -- remote username (default: {None})
        port {str|int} -- remote connection port (default: {None})
        password {str} -- remote connection password (default: {None})

    Returns:
        AttributeDict
    """
    cipher = Fernet(Fernet.generate_key())
    
    return AttributeDict({
        'hostname': hostname,
        'username': username or _DEFAULT_SSH_USER,
        'port': port or _DEFAULT_SSH_PORT,
        'password': password,
        # 'password': cipher.encrypt(password) if password else None,
        # 'cipher': cipher,
    })


def parsed_connection_parts(connection_string):
    """
    Parses an SSH connection string into its named components (username,
    password, hostname, and port (if present). The host is mandatory. The
    username and port have default values if not present, and the password
    is completely optional.

    Arguments:
        connection_string {str} -- the string to parse.

    Returns:
        AttributeDict
    """
    try:
        username, password, hostname, port = \
            CONNECTION_STRING_RE_PATTERN.match(connection_string).groups()
        return ConnectionParts(
            hostname=hostname,
            username=username or _DEFAULT_SSH_USER,
            port=port or _DEFAULT_SSH_PORT,
            password=password,
        )
    except AttributeError:
        return None
