from os import getenv
from pyvsc._util import has_internet_connection


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
    elif bool(getenv('NO_REMOTE', False)):
        should_skip = True
        reason = 'NO_REMOTE env var was set'
    return should_skip, reason

