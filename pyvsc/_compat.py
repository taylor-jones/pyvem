"""
Functions for use in normalizing compatibility between python2 and python3
"""

from sys import version_info

_PY_VERSION = version_info[0]


def is_py3():
    """
    Returns True if Python3 is being used

    Returns:
        bool
    """
    return _PY_VERSION >= 3


def popen(args):
    """
    Abstracts a subprocess Popen call to normalize it for Python2 and Python3
    
    Arguments:
        args {list} -- A list of arguments to pass as the subprocess Popen args
    
    Returns:
        tuple (str, str) -- the stdout and stderr of the popen call
    """
    import subprocess

    if is_py3():
        stdout, stderr = subprocess.Popen(
            args,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            encoding='utf-8').communicate()
    else:
        stdout, stderr = subprocess.Popen(
            args,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE).communicate()
        
    return stdout, stderr


def split(string, delimiter):
    """
    Abstracts a <str> split method to normalize any unicode output for Python2
    and Python3.
    
    Arguments:
        string {str} -- The string to split
        delimiter {str} -- The character(s) on which to split the string

    Returns:
        list -- A list of the words in the string using the delimiter
    """
    if is_py3():
        return [x.split(delimiter) for x in string]
    else:
        import re
        return [re.split(delimiter, x) for x in string]


a = ''
a.split()