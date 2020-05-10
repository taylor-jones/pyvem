from __future__ import print_function
from textwrap import dedent

import logging
from rich.console import Console
from rich.traceback import install as install_rich_traceback

from pyvsc._tunnel import Tunnel
from pyvsc._marketplace import Marketplace
from pyvsc._help import Help
from pyvsc._config import _PROG, rich_theme

# install_rich_traceback()


class Command(object):
    """
    Abstract base command class from which all actionable commands inherit.
    """
    console = Console(theme=rich_theme)
    tunnel = Tunnel()
    log = logging.getLogger('rich')
    marketplace = None
    main_parser = None
    main_options = None

    def __init__(self, name, help_, aliases=[]):
        self.name = name
        self.help = help_
        self.aliases = aliases

        # Ensure all sub-commands have instantiated a Help instance
        # for their 'help' attribute.
        assert(isinstance(self.help, Help))


    def invoke(self, main_parser, main_options):
        """
        Prepares a Command object's static elements in order to make them
        available to all Command subclasses. Then invokes the run() command
        on the object to run the vem command that was actually called.

        Arguments:
            main_parser {configargparse.ArgParser} -- The ArgParser from the
                top-level module.
            main_options {Namespace} -- The namespace object containing all of
                the argument options.
        """
        if not Command.main_options and not Command.main_parser:
            Command.main_parser = main_parser
            Command.main_options = main_options
            Command.tunnel.apply(
                ssh_host=main_options.ssh_host,
                ssh_gateway=main_options.ssh_gateway)
            Command.marketplace = Marketplace(tunnel=Command.tunnel)

        # Invoke the run() method on the called command
        self.run()


    def show_help(self):
        """
        Invokes the print() method on a Command's help object instance.

        NOTE: This expects that each Command sub-class implements a Help
        class instance
        """
        self.help.print_help()


    def show_error(self, text, **kwargs):
        """
        Prints a styled error message, entirely using the rich_theme error
        styling. This is suitable for text that is intended to all use the
        error style. For error messages that need for fine-grained output,
        it's probably better to write the custom message message 

        Arguments:
            text {str} -- The error message to output
        
        NOTE: **kwargs are passed to the console.print() method, so any named
        arguments that console.print() supports are supported here as well.
        """
        kwargs.setdefault('highlight', False)
        self.console.print(text, style=rich_theme.styles['error'], **kwargs)


    # This needs to be implemented in each of the sub-classes
    def get_command_parser(self, *args, **kwargs):
        raise NotImplementedError


    # This needs to be implemented in each of the sub-classes
    def run(self, *args, **kwargs):
        raise NotImplementedError