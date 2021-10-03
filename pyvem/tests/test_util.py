"""Utility functions for other tests"""

import os
import requests

from pyvem._util import has_internet_connection
from pyvem._containers import ConnectionParts
from pyvem._tunnel import Tunnel


def should_skip_remote_testing():
    """
    If NO_REMOTE env variable is set to a truthy value OR no internet
    connection is found, we'll skip any testing that depends on reaching out
    to remote resources to validate URLs

    Returns:
        tuple (bool, str) -- The boolean represents whether or not remote
            testing should be skipped, and the string indicates the reasoining.
    """
    reason = ''
    should_skip = False

    if not has_internet_connection():
        should_skip = True
        reason = 'No internet connection'
    elif os.getenv('NO_REMOTE', None):
        should_skip = True
        reason = 'NO_REMOTE env var was set'
    return should_skip, reason


def github_get(url):
    """
    Simulates the expected behavior of a HEAD request, since GitHub doesn't
    allow HEAD requests (they just result in a status_code of 403).

    This function ensures we don't wait for the entire size response of making
    a full GET request to GitHub when we only want to test for URL validity.
    Instead, we just get a specified content size (or timeout, whichever
    happens first), since we really only care about the status code of the
    request, not the body of the response.

    Arguments:
        url {str} -- The URL to make the GET request to

    Returns:
        int -- The response status code
    """
    max_content_len = 1
    response = requests.get(url, stream=True)

    try:
        if int(response.headers.get('Content-Length')) > max_content_len:
            raise ValueError
    except ValueError:
        return response.status_code


def get_dummy_tunnel_connection(with_gateway=True) -> Tunnel:
    """
    Simulates a dummy tunnel connection using generic host and password.

    FIXME: right now, this is hard-coded to a local virtual environment with
    dummy configurations. Find a way to simulate this in a test env.
    """
    ssh_host = ConnectionParts(hostname='centos', password='pass')

    if not with_gateway:
        return Tunnel(ssh_host, None, True)

    ssh_gateway = ConnectionParts(hostname='centos2', password='pass')
    return Tunnel(ssh_host, ssh_gateway, True)
