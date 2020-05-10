from __future__ import print_function, absolute_import
import logging

from fabric import Connection
from getpass import getpass
from rich.logging import RichHandler
from pyvsc._containers import ConnectionParts, AttributeDict


_LOGGER = logging.getLogger(__name__)


class Tunnel:
    def __init__(self, ssh_host=None, ssh_gateway=None, autoconnect=False):
        self.ssh_host = None
        self.ssh_gateway = None

        self.apply(ssh_host, ssh_gateway)
        if autoconnect:
            self.connect(ssh_host, ssh_gateway)


    def apply(self, ssh_host, ssh_gateway):
        """
        Applies the ssh_host and ssh_gateway values to the current tunnel.
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
        Wrapper of connect() which just assumes checking for an existing
        connection based on pre-existing ssh configurations.
        """
        self.connect()


    def connect(self, ssh_host=None, ssh_gateway=None, force=False):
        """
        Attempts to establish the remote ssh connection if not already
        connected.

        Keyword Arguments:
            ssh_host {ConnectionParts} -- (default: {None})
            ssh_gateway {ConnectionParts} -- (default: {None})
            force {bool} -- If True, the tunnel will attempt to connect
                regardless of whther or not its connected. (default: {False})
        """
        if force or not self.is_connected():
            self._connection = self.get_connection(
                ssh_host=ssh_host or self.ssh_host,
                ssh_gateway=ssh_gateway or self.ssh_gateway,
            )


    def is_connected(self):
        """
        Checks if the current ssh connection is active.

        Returns:
            bool -- True if connected, False if not.
        """
        try:
            return self._connection.is_connected
        except Exception:
            return False


    def get_connection(self, ssh_host, ssh_gateway=None):
        """
        Establishes ssh connection to remote host(s).

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
        password = ssh_host.password or getpass(
            '%s@%s password: ' % (ssh_host.username, ssh_host.hostname))
        self.ssh_host.password = password

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
            _LOGGER.info('Connected to host: %s.' % ssh_host.hostname)
            return connection

        except Exception as e:
            raise ConnectionError(
                'Failed to connect to host: %s' % ssh_host.hostname)


    def get(self, remote, local):
        """
        Fetches a file from the remote path to the local path.

        Arguments:
            remote {str} -- the path to the file on the remote host.
            local {str} -- the path to the local file destination.
        """
        self.ensure_connection()
        self._connection.get(remote=remote, local=local)


    def rmdir(self, path):
        """
        Removes a specified file or directory on the remote system.

        Arguments:
            path {str} -- the path to the file or directory to remove
        """
        self.ensure_connection()
        self._connection.run('rm -rf %s' % path)


    def run(self, command, hide=True):
        """
        Executes a command on the remote host over ssh and returns the output.

        Arguments:
            command {str} -- The command to execute

        Returns:
            Result -- The output of executing the command from the remote host
        """
        self.ensure_connection()
        result = self._connection.run(command, hide=hide)
        return result


    def __del__(self):
        """
        Close the remote SSH connection.
        """
        try:
            self._connection.close()
            _LOGGER.debug('Closed ssh tunnel connection.')
        except Exception as e:
            pass
            _LOGGER.debug('No ssh tunnel exists.')
