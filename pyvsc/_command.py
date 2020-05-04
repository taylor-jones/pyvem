from __future__ import print_function
from textwrap import dedent

class Command(object):
    def __init__(self, name, help_, aliases=[]):
        self.name = name
        self.help_ = help_
        self.aliases = aliases

    def show_help(self):
        print(dedent(self.help_))

    # This should be overriden in the sub-classes
    def run(self, args, parser, **kwargs):
        print('Running %s with args: %s' % (self.name, ', '.join(args)))