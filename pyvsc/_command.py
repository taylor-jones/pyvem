from __future__ import print_function
from textwrap import dedent
from pyvsc._tunnel import Tunnel
from pyvsc._marketplace import Marketplace


class Command(object):
    """
    Abstract base command class from which all actionable commands inherit.
    """
    tunnel = Tunnel()
    marketplace = None
    parser = None
    options = None


    def __init__(self, name, help_, aliases=[]):
        self.name = name
        self.help_ = help_
        self.aliases = aliases


    def invoke(self, parser, options):
        """
        Prepares a Command object's static elements in order to make them
        available to all Command subclasses. Then invokes the run() command
        on the object to run the vem command that was actually called.

        Arguments:
            parser {[type]} -- [description]
            options {[type]} -- [description]
        """
        if not Command.options and not Command.parser:
            Command.parser = parser
            Command.options = options
            Command.tunnel.apply(
                ssh_host=options.ssh_host,
                ssh_gateway=options.ssh_gateway)
            Command.marketplace = Marketplace(
                tunnel=Command.tunnel)
            self.run()


    def show_help(self):
        print(dedent(self.help_))


    # This should be overriden in each of the sub-classes
    def run(self, *args, **kwargs):
        raise NotImplementedError