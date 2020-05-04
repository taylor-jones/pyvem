from __future__ import print_function
from __future__ import absolute_import


def colored(content, ansi_begin, ansi_end='\u001b[0m'):
    return '%s%s%s' % (ansi_begin, content, ansi_end)

def red(content):
    return colored(content, '\u001b[31m')

def cyan(content):
    return colored(content, '\u001b[36m')

def white(content):
    return colored(content, '\u001b[37;1m')

def bold(content):
    return colored(content, '\u001b[1m')