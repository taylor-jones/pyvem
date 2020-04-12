from fabric import Connection
from paramiko import SFTPClient
from getpass import getpass
import logging


LOGGER = logging.getLogger(__name__)

class Tunnel:
    def __init__(self, **kwargs):
        verbose = kwargs.get('verbose')
        host = kwargs.get('host')
        port = kwargs.get('port')
        user = kwargs.get('user')
        gateway = kwargs.get('gateway')

        if verbose:
            LOGGER.setLevel(__debug__)

        # Establish the ssh & sftp connections
        self.ssh = self.get_ssh_connection(host, port, user, gateway)
        self.sftp = self.get_sftp_client(self.ssh)


    def get_sftp_client(self, ssh_connection):
        """
        Establishes an SFTP client via a SSH connection to the remote host.

        Arguments:
            ssh_connection {Connection} -- An instance of an established 
                fabic ssh Connection.

        Returns:
            paramiko.SFTPClient
        """
        try:
            sftp_client = SFTPClient.from_transport(
                ssh_connection.transport)
            LOGGER.debug('SFTP Client successfully established.')
            return sftp_client
        except Exception as e:
            LOGGER.error(e, exc_info=self.verbose)


    def get_ssh_connection(self, host, port, user, gateway):
        """
        Establishes ssh and sftp connections to remote host(s).

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
        proxy = None

        try:
            # establish the gateway/proxy connection
            proxy = Connection(
                host=gateway,
                user=user,
                port=port,
                connect_kwargs={'password': password}
            ) if gateway is not None else None
        except Exception as e:
            LOGGER.error(
                'Failed to connect to gateway: %s' % (gateway),
                exc_info=self.verbose)

        try:
            # establish the ssh connection
            ssh_client = Connection(
                host=host,
                port=port,
                user=user,
                gateway=proxy,
                connect_kwargs={'password': password}
            )

            # open the ssh connection
            ssh_client.open()
            LOGGER.debug('SSH Client successfully established.')
            return ssh_client

        except Exception as e:
            LOGGER.error(
                'Failed to connect to host: %s' % (host),
                exc_info=self.verbose)


    def get(self, remote_path, local_path):
        """
        Fetches a file from the remote path to the local path.

        Arguments:
            remote_path {str} -- the path to the file on the remote host.
            local_path {str} -- the path to the local file destination.
        """
        self.sftp.get(remote_path, local_path)


    def listdir(self, path):
        """
        Lists the files in a specified directory.
        """
        return self.sftp.listdir(path)


    def rmdir(self, path):
        """
        Removes a specified file or directory on the remote system.

        Arguments:
            path {str} -- the path to the file or directory to remove
        """
        self.ssh.run('rm -rf %s' % (path))


    def run(self, command):
        """
        Executes a command on the remote host over ssh and returns the output.

        Arguments:
            command {str} -- The command to execute

        Returns:
            str -- The output of executing the command from the remote host
        """
        result = self.ssh.run(command)
        if result.exited > 0:
            return result.stderr
        return result.stdout


    def __del__(self):
        """
        Close the remote SSH and SFTP connections.
        """
        try:
            self.ssh.close()
        except Exception as e:
            LOGGER.warning('No ssh tunnel exists.')

        try:
            self.sftp.close()
        except Exception as e:
            LOGGER.warning('No ftp connection exists.')