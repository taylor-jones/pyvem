"""Abstract Command class from which all program command subclasses inheir"""

import os
import pathlib

from rich.console import Console

from pyvem._tunnel import Tunnel
from pyvem._marketplace import Marketplace
from pyvem._help import Help
from pyvem._config import rich_theme
from pyvem._logging import get_rich_logger


_console = Console(theme=rich_theme)
_LOGGER = get_rich_logger(__name__, console=_console)


class Command():
    """
    Abstract base command class from which all actionable commands inherit.
    """
    tunnel = Tunnel()
    marketplace = None
    main_parser = None
    main_options = None

    # Keep track of temporary files created during execution.
    # These will be removed at the end of processing.
    temporary_file_paths = []


    def __init__(self, name, help_, aliases=None):
        self.name = name
        self.help = help_
        self.aliases = aliases or []

        # Keep track of whether this program created the local output directory.
        # If we created it, we'll delete it. If we didn't create it, we won't delete it.
        self.created_local_output_dir = None

        # Ensure all sub-commands have instantiated a Help instance for their 'help' attribute.
        assert isinstance(self.help, Help)


    @staticmethod
    def store_temporary_file_path(path):
        """
        Adds a given file path to the list of temporary files that should be removed at the
        end of processing.

        Arguments:
            path {str} -- The absolute path to a file.
        """
        if path:
            Command.temporary_file_paths.append(path)


    @staticmethod
    def remove_temporary_files():
        """
        Remove all temporary files that were created during processing.
        """
        if not Command.main_options.no_cleanup:
            for tmp_file in Command.temporary_file_paths:
                os.remove(tmp_file)


    @staticmethod
    def apply_log_level(logger):
        """
        Update the logger to apply the log-level from the main options.
        NOTE: This isn't applied in the base Command class, but it's used by Command subclasses.

        Arguments:
            logger {logging.logger} -- The logger from a command.
        """
        logger.setLevel(Command.main_options.log_level)


    @staticmethod
    def show_error(text, **kwargs):
        """
        Print a styled error using the rich_theme error styling and a rich console. This is
        suitable for text that is intended to all use the error style. For error messages that
        need for fine-grained output, it's probably better to write the custom message message

        NOTE: The difference between this and the logging.error is that the console error does
        not include the logging formatting (like the module name and timestamp). This is just
        for direct error messages.

        Arguments:
            text {str} -- The error message to output

        NOTE: **kwargs are passed to the console.print() method, so any named
        arguments that console.print() supports are supported here as well.
        """
        kwargs.setdefault('highlight', False)
        _console.print(text, style=rich_theme.styles['error'], **kwargs)


    def ensure_output_dirs_exist(self):
        """
        Ensure that both the temprorary remote directory and the temporary local directory exist.

        Returns:
            bool -- True if we could ensure both the remote and local dirs exist, False if not.
        """
        local_exists = self.ensure_local_output_dir_exists()
        remote_exists = self.ensure_remote_output_dir_exists()
        return local_exists and remote_exists


    def ensure_remote_output_dir_exists(self):
        """
        Ensure the temporary remote directory that will be used for storing
        any downloads on the remote system exists.

        Returns:
            bool -- True if we could ensure the directory exists, False if not.
        """
        self.tunnel.ensure_connection()
        return self.tunnel.mkdir(self.main_options.remote_output_dir)


    def ensure_local_output_dir_exists(self):
        """
        Create the output directory provided by the original vem command

        Returns:
            bool -- True if the output directory was ensured to exist (whether
            we created it or it already existed), False if an exception was raised.
        """
        # We only need to do this once.
        if self.created_local_output_dir is not None:
            return True

        if os.path.exists(Command.main_options.output_dir):
            self.created_local_output_dir = False
            return True

        try:
            pathlib.Path(Command.main_options.output_dir).mkdir(parents=True, exist_ok=False)
            self.created_local_output_dir = True
            return True
        except EnvironmentError as err:
            _LOGGER.debug(err)
            return False


    def invoke(self, main_parser, main_options):
        """
        Prepare a Command object's static elements in order to make them
        available to all Command subclasses. Then invokes the run() command
        on the object to run the vem command that was actually called.

        Arguments:
            main_parser {configargparse.ArgParser} -- The ArgParser from the top-level module.
            main_options {Namespace} -- The namespace object containing all of the argument options
        """
        if not Command.main_options and not Command.main_parser:
            # store the main parser and the the main options so they can
            # be referenced by sub-commands whenever needed.
            Command.main_parser = main_parser
            Command.main_options = main_options

            # apply the log level from the original parsed arguments
            _LOGGER.setLevel(Command.main_options.log_level)

            # pass along the original remote connection args to the shared tunnel instance, so it
            # can be ready to connect whenever a command that uses the remote connection is invoked
            Command.tunnel.logger.setLevel(main_options.log_level)
            Command.tunnel.apply(ssh_host=main_options.ssh_host,
                                 ssh_gateway=main_options.ssh_gateway)

            # Pass along the tunnel instance to the shared Marketplace instance
            # so we don't have to maintain multiple tunnel connections.
            Command.marketplace = Marketplace(tunnel=Command.tunnel)

        # Invoke the run() method on the called command. The run() method must be implemented
        # within each command subclass.
        try:
            # TODO: This should be better handled. Right now, it would print the message
            # below if the Command.run() returns True, but I'm not sure how much value that adds.
            if self.run():
                _LOGGER.info('All Done!')
            # else:
            #     _console.print('[logging.level.warning]Command finished[/]')

        except Exception as err:
            _LOGGER.exception(repr(err))
            # raise err

        finally:
            # regardless of what happens, cleanup and created remote
            # directories and close the remote connection.
            self.tunnel.cleanup_created_dirs()
            self.tunnel.close()
            self.remove_temporary_files()


    def show_help(self):
        """
        Invoke the print() method on a Command's help object instance.
        NOTE: This expects that each Command sub-class implements a Help class instance
        """
        self.help.print_help()


    def show_usage(self):
        """
        Prints the synopsis of a command's help info.
        NOTE: This expects that each Command sub-class implements a Help class instance
        """
        self.help.print_usage()


    def get_command_parser(self, *args, **kwargs):
        """
        Implements parsing subcommands within a particular command.
        NOTE: This needs to be implemented in each of the sub-classes

        Raises:
            NotImplementedError: [description]
        """
        raise NotImplementedError


    def run(self, *args, **kwargs):
        """
        Implements the funcionality of a particular command.
        NOTE: This needs to be implemented in each of the sub-classes

        Raises:
            NotImplementedError: [description]
        """
        raise NotImplementedError
