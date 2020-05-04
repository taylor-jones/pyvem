from fabric import Connection
from getpass import getpass
import logging

# NOTE: Maybe this fn can import the parsed config to determine which tunnel
# connection to establish, then instantiate a tunnel connection within itself
# so that other modules can just import the already-established tunnel
# connection?

_LOGGER = logging.getLogger(__name__)


class Tunnel:
    def __init__(self, **kwargs):
        host = kwargs.get('host')
        port = kwargs.get('port')
        user = kwargs.get('user')
        gateway = kwargs.get('gateway')
        password = kwargs.get('password')

        # Establish the ssh connection
        self._connection = self.get_connection(host, port, user, gateway)


    def is_connected(self):
        try:
            return self._connection.is_connected
        except Exception:
            return False


    def get_connection(self, host, port, user, gateway=None):
        """
        Establishes ssh connection to remote host(s).

        Arguments:
            host {str} -- ip or hostname of remote host
            port {int} -- port of remote host
            user {str} -- username for remote host connection
            gateway {str|None} -- ip or hostname of gateway host (optional)

        Returns:
            Connection -- an instance of a fabric Connection object
                that represents a valid ssh connection to the remote host.

        Note:
            The current implementation assumes that the username, port,
            and password are the same for the ssh host and the gateway.
        """
        password = getpass('%s@%s password: ' % (user, host))

        try:
            # establish the ssh connection
            connection = Connection(
                host=host,
                port=port,
                user=user,
                gateway=Connection(
                    host=gateway,
                    user=user,
                    port=port,
                    connect_kwargs={'password': password}
                ) if gateway is not None else None,
                connect_kwargs={'password': password}
            )

            # open the ssh connection to test the connection
            connection.open()
            _LOGGER.info('Connected to host: %s.' % host)
            return connection

        except Exception as e:
            _LOGGER.error('Failed to connect to host: %s' % host)


    def get(self, remote, local):
        """
        Fetches a file from the remote path to the local path.

        Arguments:
            remote {str} -- the path to the file on the remote host.
            local {str} -- the path to the local file destination.
        """
        self._connection.get(remote=remote, local=local)


    def rmdir(self, path):
        """
        Removes a specified file or directory on the remote system.

        Arguments:
            path {str} -- the path to the file or directory to remove
        """
        self._connection.run('rm -rf %s' % path)


    # NOTE: This is the v1 run

    # def run(self, command):
    #     """
    #     Executes a command on the remote host over ssh and returns the output.

    #     Arguments:
    #         command {str} -- The command to execute

    #     Returns:
    #         str -- The output of executing the command from the remote host
    #     """
    #     result = self._connection.run(command)
    #     return result.stderr if result.exited > 0 else result.stdout


    # NOTE: possible V2 implementation

    def run(self, command, hide=True):
        """
        Executes a command on the remote host over ssh and returns the output.

        Arguments:
            command {str} -- The command to execute

        Returns:
            Result -- The output of executing the command from the remote host
        """
        result = self._connection.run(command, hide=hide)
        return result


    def __del__(self):
        """
        Close the remote SSH connection.
        """
        try:
            self._connection.close()
            _LOGGER.info('Closed ssh tunnel connection.')
        except Exception as e:
            _LOGGER.warning('No ssh tunnel exists.')
