"""Config command implementation"""

import locale
import os
from itertools import chain
from typing import Any

import configargparse
import yaml

from rich.console import Console
from pyvem._command import Command
from pyvem._config import _PROG, rich_theme
from pyvem._help import Help
from pyvem._logging import get_rich_logger
from pyvem._util import get_confirmation, get_response, resolved_path

_CONSOLE = Console(theme=rich_theme)
_LOGGER = get_rich_logger(__name__)
_HELP = Help(
    name='config',
    brief=f'Manage the {_PROG} configuration file.',
    synopsis=f'\t{_PROG} config set <key> <value>\n'
             f'\t{_PROG} config get <key>\n'
             f'\t{_PROG} config delete <key>'
             f'\t{_PROG} config list'
             f'\t{_PROG} config edit'
             f'\n\n'
             f'\t[h2]aliases:[/h2] {_PROG} c',
    description=f'This command provides a means of managing '
                f'{_PROG}\'s .{_PROG}rc file. '
                f'This allows for setting, getting, or updating the contents '
                'within the .{_PROG}rc.',
    sub_commands='Config supports the following sub-commands:'
                 '\n\n'
                 '[h2]set[/h2]\n'
                 f'\t[example]{_PROG} config set <key> <value>[/]\n'
                 '\tSets the config key to the value.\n'
                 '\tIf the value is omitted, it\'s set to "true".\n\n'
                 '[h2]get[/h2]\n'
                 f'\t[example]{_PROG} config get <key>[/]\n'
                 '\tPrints the config key value to stdout.\n\n'
                 '[h2]list[/h2]\n'
                 f'\t[example]{_PROG} config list[/]\n'
                 '\tPrints all of the config settings to stdout.\n\n'
                 '[h2]delete[/h2]\n'
                 f'\t[example]{_PROG} config delete <key>[/]\n'
                 '\tDeletes the key from the configuration file.\n\n'
)


def print_config_key_value(key: str, value: Any) -> None:
    """Prints a key, value pair to stdout

    Raises:
        TypeError: If the value is None
    """
    try:
        if value is None:
            raise TypeError
        key = key + ':'
        _CONSOLE.print(f'{key:13}{value}', highlight=False)
    except (KeyError, TypeError):
        _LOGGER.info('No configuration found for "%s".', key)


class ConfigCommand(Command):
    """
    Inherits from the base Command class and overrides the `run` method
    to implement the Config functionality.
    """
    def __init__(self, name, aliases=None):
        self.conf_file = None
        self.conf_settings = None
        self.subcommands = {'get', 'set', 'list', 'delete'}
        super().__init__(name, _HELP, aliases=aliases or [])


    def _fetch_configurations(self):
        """
        Parses the configurations from configargparse to determine which of
        them came from a configuration file.
        """
        if not self.conf_file or not self.conf_settings:
            parser_attr = dict(vars(Command.main_parser))
            confs = parser_attr['_source_to_settings']
            conf_files = [(key, confs[key]) for key in confs.keys()
                          if key.startswith('config_file')]

            if conf_files:
                conf_file, conf_settings = conf_files[0]
                conf_file = conf_file.split('|')[-1]
                conf_file = os.path.join(os.getcwd(), conf_file)
                conf_settings = [(k, v[1]) for k, v in conf_settings.items()]

                self.conf_file = conf_file
                self.conf_settings = conf_settings


    def _get_config(self, key: str):
        """
        Implements a "get" subcommand, reading an individual setting from the
        user's configuration file, if one exists. If found, the value is
        printed to the console stdout.

        Arguments:
            key -- The name of the setting to get the value of
        """
        self._fetch_configurations()

        # make sure there's a config file to read from
        if not self.conf_file:
            _LOGGER.warning('No config file was found.')
            return False

        # if the config file, itself, was requested, just return the path
        # to the config file as a key-value pair.
        if key == 'config':
            return ('config file', self.conf_file)

        # make sure there are any configurations to read
        if not self.conf_settings:
            _CONSOLE.print('[i]no configurations found.[/]')
            return False

        # Find the first matching config.
        return next((x for x in self.conf_settings if x[0] == key), None)


    def _set_config(self, key, value):
        self._fetch_configurations()
        rc_file = f'.{_PROG}rc'

        # make sure there's a config file to read from
        if not self.conf_file:
            question = f'No {rc_file} file was found. Would you like to ' \
                        'create one?'

            # check if the user wants to create a .vimrc file
            if get_confirmation(question):
                rc_home = f'~/{rc_file}'
                rc_file = get_response('Configuration file', rc_home)
                self.conf_file = resolved_path(rc_file)

                # create the config file
                with open(self.conf_file, 'w+',
                          encoding=locale.getpreferredencoding()):
                    pass
            else:
                self.show_error('No configuration can be set without a config'
                                'file.')


        # Open the config file and read it's contents into a dict
        with open(self.conf_file,
                  encoding=locale.getpreferredencoding()) as conf_file:
            conf = yaml.safe_load(conf_file) or {}

        # Update the config setting
        conf[key] = value

        # Write the configuration back to the file
        with open(self.conf_file, 'w',
                  encoding=locale.getpreferredencoding()) as conf_file:
            yaml.safe_dump(conf, conf_file, default_flow_style=False)


    def _remove_config(self, key: str) -> bool:
        """
        Remove a configuration key from the vem configuration file

        Args:
            key: the name of the key to remove

        Returns:
            True if the configuration key could be removed, False if not
        """

        # make sure there's a config file to read from
        self._fetch_configurations()
        if not self.conf_file:
            self.show_error('No configuration can be removed without a '
                            'config file.')
            return False

        # Open the config file and read it's contents into a dict
        with open(self.conf_file,
                  encoding=locale.getpreferredencoding()) as conf_file:
            conf = yaml.safe_load(conf_file) or {}

            # Delete the config setting
            del conf[key]

        # Write the configuration back to the file
        with open(self.conf_file, 'w',
                  encoding=locale.getpreferredencoding()) as conf_file:
            yaml.safe_dump(conf, conf_file, default_flow_style=False)

        return True


    def _get_config_list(self):
        """
        Lists all configuration settings from the user's vem configuration.
        All found settings are printed to the console's stdout.
        """
        self._fetch_configurations()

        # check for a config file
        if not self.conf_file:
            _LOGGER.warning('No config file was found.')
            return False

        # include the config file, itself, in the list
        _CONSOLE.print(f'config file: {self.conf_file}')

        # check for any configurations in the config file
        if not self.conf_settings:
            _CONSOLE.print('[i]No configurations found.[/]')

        return self.conf_settings


    def get_command_parser(self, *args, **kwargs):
        """
        Builds and returns an argument parser that is specific to the
        "install" command.

        Returns:
            configargparse.ArgParser
        """
        parser_kwargs = {'add_help': False, 'prog': f'{_PROG} {self.name}'}
        parser = configargparse.ArgumentParser(**parser_kwargs)
        parser.add_argument('--help',
                            action='help',
                            help='Show help.')
        parser.add_argument('subcommand',
                            nargs='?',
                            type=str,
                            help='The config subcommand.')
        parser.add_argument('key',
                            nargs='+',
                            default=None,
                            type=str,
                            help='The subcommand key.')
        return parser


    def run(self, *args, **kwargs):
        """
        Implements the actual behavior of calling "vem config"
        """
        # Update the logger to apply the log-level from the main options
        self.apply_log_level(_LOGGER)

        # Create a new parser to parse the config command
        parser = self.get_command_parser()
        args, _ = parser.parse_known_args()

        # Destructure the "config" command parts from the vem input.
        defaults = [None] * 3
        subcommand, key, value, *_ = chain(args.key, defaults)

        try:
            # Call the method associated with the provided subcommand, passing
            # along the key as well, where applicable.
            if subcommand == 'list':
                for setting in self._get_config_list():
                    print_config_key_value(*setting)
            elif subcommand == 'get':
                value = self._get_config(key)
                print_config_key_value(key, value)
            elif subcommand == 'set':
                self._set_config(key, value)
            elif subcommand in ('remove', 'delete'):
                self._remove_config(key)
            else:
                raise ValueError
        except Exception as err:
            _LOGGER.error(repr(err))
            parser.print_usage()


#
# Create the ConfigCommand instance
#
config_command = ConfigCommand(name='config', aliases=['config', 'c'])
