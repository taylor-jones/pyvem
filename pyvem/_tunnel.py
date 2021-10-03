"""The Tunnel provides a means of communicating with a remote host."""

import sys
from socket import gethostname
from getpass import getpass
from typing import Any

import fabric
from paramiko import ssh_exception
import rich.console

from pyvem._config import rich_theme, _PROG
from pyvem._containers import ConnectionParts
from pyvem._logging import get_rich_logger
from pyvem._util import delimit

_CONSOLE = rich.console.Console(theme=rich_theme)
_LOGGER = get_rich_logger(__name__, console=_CONSOLE)


class Tunnel:
    """
    Communicate with the remote host.

    The tunnel class establishes a connection to the remote system and allows a
    medium for getting remote resources and transferring them to the local
    system.
    """

    def __init__(self, ssh_host: ConnectionParts = None,
                 ssh_gateway: ConnectionParts = None,
                 autoconnect: bool = False):
        """
        Apply argued ssh connection arguments. Setup connection if specified.

        Keyword Arguments:
            ssh_host -- the ssh_host connection info
            ssh_gateway -- the ssh_gateway connection info
            autoconnect -- If True, try to connect to the remote host
        """
        self._connection = None
        self._localhost_name = gethostname()
        self._ssh_host = None
        self._ssh_gateway = None

        # expose the module logger so the loglevel can be updated by external
        # users of the Tunnel instanace.
        self.logger = _LOGGER

        # maintain a list of all the directories we create during processing
        # so we can go back and clean them up before exiting.
        self._created_dirs = set()

        # apply the ssh host and gateway attributes from the constructor
        self.apply(ssh_host, ssh_gateway)

        if autoconnect:
            self.connect(ssh_host, ssh_gateway)


    def apply(self, ssh_host: ConnectionParts,
              ssh_gateway: ConnectionParts = None) -> None:
        # TODO: Better handle cases where we don't want to adopt the password
        # from the ssh host connection parameters.
        """
        Apply the ssh_host and ssh_gateway values to the current tunnel.

        The SSH gateway (if one exists) will adopt most any value from the SSH
        host specification, except for the hostname.
        """
        self._ssh_host = ssh_host

        if ssh_gateway:
            self._ssh_gateway = ConnectionParts(
                hostname=ssh_gateway.hostname,
                # Adopt the username and password from the host connection
                username=ssh_gateway.username or ssh_host.username,
                password=ssh_gateway.password or ssh_host.password,
                port=ssh_gateway.port or ssh_host.port,
            )


    def ensure_connection(self):
        """
        Check for existing ssh connection.

        Wrapper of connect() which just assumes checking for an existing
        connection based on pre-existing ssh configurations.
        """
        self.connect()


    def connect(self, ssh_host: ConnectionParts = None,
                ssh_gateway: ConnectionParts = None,
                force: bool = False) -> None:
        """
        Establish ssh connection (if not already connected).

        Keyword Arguments:
            ssh_host
            ssh_gateway
            force -- If True, the tunnel will attempt to re-establish a
                connection, ignoring whether or not a connection already exists
        """
        if force or not self.is_connected():
            self._connection = self.get_connection(
                ssh_host=ssh_host or self._ssh_host,
                ssh_gateway=ssh_gateway or self._ssh_gateway)


    def is_connected(self) -> bool:
        """
        Check if the current ssh connection is active.

        Returns:
            bool -- True if connected, False if not.
        """
        return self._connection and self._connection.is_connected


    def get_connection(self, ssh_host: ConnectionParts,
                       ssh_gateway: ConnectionParts = None) -> fabric.Connection:
        """
        Establish ssh connection to remote host(s).

        Arguments:
            ssh_host {ConnectionParts}
            ssh_gateway {ConnectionParts}

        Returns:
            fabric.Connection -- A valid ssh connection to the remote host.

        Note:
            The current implementation assumes that the username, port, and
            password are the same for the ssh host and the gateway.
        """
        password = ssh_host.password
        num_failed_attempts = 0
        max_allowed_failed_attempts = 3

        while num_failed_attempts < max_allowed_failed_attempts:
            if not password:
                # get a password from the user
                prompt = f'{ssh_host.username}@{ssh_host.hostname} password: '

                try:
                    if sys.stdin.isatty():
                        password = getpass(prompt=prompt, stream=sys.stderr)
                    else:
                        print(prompt)
                        password = sys.stdin.readline().rstrip()
                    self._ssh_host.password = password

                except KeyboardInterrupt:
                    _LOGGER.warning('Terminated by user. Exiting.')
                    sys.exit(1)

            # TODO: Abstract the gateway connection to a more generalized
            # "connection" method so we can more specifically pinpoint (in the
            # event of a connection error) whether the error occurred while
            # trying to connect to the host or the gateway.

            try:
                # establish the ssh connection
                connection = fabric.Connection(
                    host=ssh_host.hostname,
                    port=ssh_host.port,
                    user=ssh_host.username,
                    gateway=fabric.Connection(
                        host=ssh_gateway.hostname,
                        user=ssh_gateway.username,
                        port=ssh_gateway.port,
                        connect_kwargs={'password': password}
                    ) if ssh_gateway is not None else None,
                    connect_kwargs={'password': password}
                )

                # open the ssh connection to test the connection
                connection.open()
                _LOGGER.info('Connected to host: %s.', ssh_host.hostname)
                return connection

            except ssh_exception.AuthenticationException as err:
                password = None
                num_failed_attempts += 1

                if num_failed_attempts >= max_allowed_failed_attempts:
                    _LOGGER.error('Too many failed authentication attempts')
                    sys.exit(1)
                else:
                    _LOGGER.error('%s. Please retry (%d remaining)', str(err),
                                  max_allowed_failed_attempts -
                                  num_failed_attempts)

            except ssh_exception.SSHException as err:
                _LOGGER.error('Failed to connect to host "%s". %s',
                            ssh_host.hostname, err)
                _LOGGER.error(repr(err))
                sys.exit(1)


    def get(self, remote_path: str, local_dest: str) -> None:
        """
        Fetch a file from the remote path to the local path.

        Arguments:
            remote_path -- the path to the file on the remote host.
            local_dest -- the path to the local file destination.
        """
        self.ensure_connection()
        self._connection.get(remote=remote_path, local=local_dest)
        _LOGGER.debug('Copied "%s:%s" to "%s:%s"',
                      self._ssh_host.hostname, remote_path,
                      self._localhost_name, local_dest)


    def rmdir(self, path: str, force: bool = False) -> bool:
        """
        Remove a specified file or directory on the remote system.

        Arguments:
            path -- the path to the file or directory to remove

        Returns:
            True if the remote dir was successfully removed, False if not
        """
        self.ensure_connection()

        opts = '-r'
        if force:
            opts += 'f'

        res = self._connection.run(f'rm {opts} {path}')

        if res.exited == 0:
            _LOGGER.debug('Removed remote directory: "%s:%s"',
                          self._ssh_host.hostname, path)
            return True
        return False


    def mkdir(self, path: str) -> bool:
        """
        Create a directory on the remote system and adds the directory to the
        running set of created directories, so we can go back and delete all
        the created directories at the end of processing.

        Arguments:
            path -- the path to the directory to create

        Returns:
            True if the remove directory was able to be created, False if not
        """
        self.ensure_connection()
        res = self._connection.run(f'mkdir -p {path}')

        if res.exited == 0:
            _LOGGER.debug('Created remote directory: "%s:%s"',
                          self._ssh_host.hostname, path)
            self._created_dirs.add(path)
            return True

        return False


    def cleanup_created_dirs(self) -> None:
        """Cleanup directories that were created during processing"""

        if not bool(self._created_dirs):
            _LOGGER.debug('No remote directories need to be cleaned up.')

        elif not self.is_connected():
            _LOGGER.error('Tunnel connection was lost. Unable to remove '
                          'remote directories: %s. \nYou may need to manually '
                          'remove them.', delimit(self._created_dirs))
        else:
            # There are directories that need to be removed and the remote
            # connection is active
            for directory in self._created_dirs:
                try:
                    self.rmdir(directory)
                except EnvironmentError as err:
                    _LOGGER.error(err)


    def run(self, command: str, hide: bool = True) -> Any:
        """
        Execute a command on the remote host over ssh and returns the output.

        Arguments:
            command -- The command to execute

        Returns:
            The output of executing the command from the remote host
        """
        try:
            self.ensure_connection()
            return self._connection.run(command, hide=hide)
        except KeyboardInterrupt:
            _LOGGER.debug('%s interrupted. Preparing to exit.', _PROG)
            sys.exit(1)


    def close(self) -> None:
        """
        Close the remote SSH connection.
        """
        if self._connection is not None:
            self._connection.close()
            _LOGGER.debug('Closed ssh tunnel connection.')


    def __del__(self):
        """
        Close connection in class destructor.
        """
        try:
            self.close()
        except ImportError:
            pass
