"""The Tunnel provides a means of communicating with a remote host."""

from __future__ import print_function, absolute_import

import sys
import logging

from socket import gethostname
from fabric import Connection
from getpass import getpass
from pyvsc._containers import ConnectionParts, AttributeDict

_LOGGER = logging.getLogger(__name__)


class Tunnel:
    """
    Communicate with the remote host.

    The tunnel class establishes a connection to the remote system and allows
    a medium for getting remote resources and transferring them to the local
    system.
    """

    def __init__(self, ssh_host=None, ssh_gateway=None, autoconnect=False):
        """
        Apply argued ssh connection arguments. Setup connection if specified.

        Keyword Arguments:
            ssh_host {ConnectionParts} -- the ssh_host connection parts
                (default: {None})
            ssh_gateway {ConnectionParts} -- the ssh_gateway connection parts
                (default: {None})
            autoconnect {bool} -- If True, go ahead and try to connect to
                the remote host at initialization time (default: {False})
        """
        self.ssh_host = None
        self.ssh_gateway = None

        # maintain a list of all the directories we create during processing
        # so we can go back and clean them up before exiting.
        self.created_dirs = set()

        self.apply(ssh_host, ssh_gateway)
        if autoconnect:
            self.connect(ssh_host, ssh_gateway)


    def apply(self, ssh_host, ssh_gateway):
        """
        Apply the ssh_host and ssh_gateway values to the current tunnel.

        The SSH gateway (if one exists) will adopt most any value from the
        SSH host specification, except for the hostname.

        Arguments:
            ssh_host {ConnectionParts}
            ssh_gateway {ConnectionParts}
        """
        self.ssh_host = ssh_host
        if ssh_gateway:
            self.ssh_gateway = ConnectionParts(
                hostname=ssh_gateway.hostname,
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


    def connect(self, ssh_host=None, ssh_gateway=None, force=False):
        """
        Establish ssh connection (if not already connected).

        Keyword Arguments:
            ssh_host {ConnectionParts} -- (default: {None})
            ssh_gateway {ConnectionParts} -- (default: {None})
            force {bool} -- If True, the tunnel will attempt to connect
                regardless of whther or not its connected. (default: {False})
        """
        if force or not self.is_connected():
            self._connection = self.get_connection(
                ssh_host=ssh_host or self.ssh_host,
                ssh_gateway=ssh_gateway or self.ssh_gateway)


    def is_connected(self):
        """
        Check if the current ssh connection is active.

        Returns:
            bool -- True if connected, False if not.
        """
        try:
            return self._connection.is_connected
        except Exception as e:
            return False


    def get_connection(self, ssh_host, ssh_gateway=None):
        """
        Establish ssh connection to remote host(s).

        Arguments:
            ssh_host {ConnectionParts}
            ssh_gateway {ConnectionParts}

        Returns:
            Connection -- an instance of a fabric Connection object
                that represents a valid ssh connection to the remote host.

        Note:
            The current implementation assumes that the username, port,
            and password are the same for the ssh host and the gateway.
        """
        password = ssh_host.password

        if not password:
            prompt = '{}@{} password: '.format(
                ssh_host.username,
                ssh_host.hostname)

            # get a password from the user
            try:
                if sys.stdin.isatty():
                    password = getpass(prompt=prompt, stream=sys.stderr)
                else:
                    print(prompt)
                    password = sys.stdin.readline().rstrip()
                self.ssh_host.password = password

            except KeyboardInterrupt:
                _LOGGER.warning('Exiting.')
                sys.exit(1)

        try:
            # establish the ssh connection
            connection = Connection(
                host=ssh_host.hostname,
                port=ssh_host.port,
                user=ssh_host.username,
                gateway=Connection(
                    host=ssh_gateway.hostname,
                    user=ssh_gateway.username,
                    port=ssh_gateway.port,
                    connect_kwargs={'password': password}
                ) if ssh_gateway is not None else None,
                connect_kwargs={'password': password}
            )

            # open the ssh connection to test the connection
            connection.open()
            _LOGGER.info('Connected to host: {}.'.format(ssh_host.hostname))
            return connection

        except Exception as e:
            raise ConnectionError('Failed to connect to host: {}'.format(
                ssh_host.hostname))


    def get(self, remote, local):
        """
        Fetch a file from the remote path to the local path.

        Arguments:
            remote {str} -- the path to the file on the remote host.
            local {str} -- the path to the local file destination.
        """
        self.ensure_connection()
        self._connection.get(remote=remote, local=local)
        _LOGGER.debug('Copied "{}:{}" to "{}:{}"'.format(
            self.ssh_host.hostname, remote, gethostname(), local))


    def rmdir(self, path):
        """
        Remove a specified file or directory on the remote system.

        Arguments:
            path {str} -- the path to the file or directory to remove
        """
        self.ensure_connection()
        res = self._connection.run('rm -rf {}'.format(path))

        if res.exited == 0:
            _LOGGER.debug('Removed remote directory: "{}:{}"'.format(
                self.ssh_host.hostname, path))
            return True
        return False


    def mkdir(self, path):
        """
        Create a directory on the remote system.

        Arguments:
            path {str} -- the path to the directory to create
        """
        self.ensure_connection()
        res = self._connection.run('mkdir -p {}'.format(path))
        self.created_dirs.add(path)
        return res.exited == 0


    def cleanup_created_dirs(self):
        """Cleanup directories that were created during processing."""
        if not bool(self.created_dirs):
            _LOGGER.debug('No remote directories need to be cleaned up.')
            return

        if not self.is_connected():
            dirs = ', '.join(list(self.created_dirs))
            _LOGGER.error('Tunnel connection was lost. Unable to remove '
                          'remote directories: {}'.format(dirs))

        for d in self.created_dirs:
            try:
                self.rmdir(d)
            except Exception as e:
                _LOGGER.error(e)


    def run(self, command, hide=True):
        """
        Execute a command on the remote host over ssh and returns the output.

        Arguments:
            command {str} -- The command to execute

        Returns:
            Result -- The output of executing the command from the remote host
        """
        self.ensure_connection()
        result = self._connection.run(command, hide=hide)
        return result


    def close(self):
        """Close the remote SSH connection."""
        try:
            self._connection.close()
            _LOGGER.debug('Closed ssh tunnel connection.')
        except Exception as e:
            pass


    def __del__(self):
        """Close connection in class destructor."""
        self.close()
