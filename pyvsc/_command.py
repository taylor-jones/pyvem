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
    main_parser = None
    main_options = None


    def __init__(self, name, help_, aliases=[]):
        self.name = name
        self.help_ = help_
        self.aliases = aliases


    def invoke(self, main_parser, main_options):
        """
        Prepares a Command object's static elements in order to make them
        available to all Command subclasses. Then invokes the run() command
        on the object to run the vem command that was actually called.

        Arguments:
            main_parser {[type]} -- [description]
            main_options {[type]} -- [description]
        """
        if not Command.main_options and not Command.main_parser:
            Command.main_parser = main_parser
            Command.main_options = main_options
            Command.tunnel.apply(
                ssh_host=main_options.ssh_host,
                ssh_gateway=main_options.ssh_gateway)
            Command.marketplace = Marketplace(tunnel=Command.tunnel)

            self.run()


    def show_help(self):
        print(dedent(self.help_))


    # This should be overriden in each of the sub-classes
    def get_command_parser(self, *args, **kwargs):
        raise NotImplementedError


    # This should be overriden in each of the sub-classes
    def run(self, *args, **kwargs):
        raise NotImplementedError