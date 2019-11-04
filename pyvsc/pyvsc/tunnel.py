import paramiko
import getpass
import socket
import logging

_LOGGER = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(message)s')

class Tunnel:
    def __init__(self, **kwargs):
        self.host = kwargs.get('host')
        self.port = kwargs.get('port')
        self.user = kwargs.get('user')
        self.connect()

    def connect(self):
        """
        Initialize the ssh client connection.
        """
        is_connected = False

        # setup the ssh connection
        self.ssh = paramiko.SSHClient()
        self.ssh.load_system_host_keys()
        self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy)

        # make sure we get a password
        password = getpass.getpass("password: ")

        # try making the ssh connection
        try:
            self.ssh.connect(
                self.host, 
                port=self.port, 
                username=self.user, 
                password=password)
            _LOGGER.info(f'Connected to {self.host}')
        
            # setup the sftp connection
            t = self.ssh.get_transport()
            self.ftp = paramiko.SFTPClient.from_transport(t)

        except (
            paramiko.BadHostKeyException,
            paramiko.AuthenticationException,
            paramiko.ChannelException,
            paramiko.PasswordRequiredException,
            paramiko.SSHException,
            socket.error,
        ) as e:
            print(e)
            _LOGGER.error(f'Failed to connect to {self.host}')
            exit(1)

    def get(self, remote_path, local_path):
        """
        Fetches a file from the remote path to
        the local path.
        """
        self.ftp.get(remote_path, local_path)

    def listdir(self, path):
        """
        Lists the files in a specified directory.
        """
        return self.ftp.listdir(path)

    def rmdir(self, path):
        """
        Remove a specified directory.
        """
        self.ssh.exec_command(f'rm -rf {path}')


    def send(self, cmd):
        """
        Execute a command on the remote server.
        """
        stdin, stdout, stderr = self.ssh.exec_command(cmd)
        output = ''.join(stdout.readlines())
        return output


    def __del__(self):
        """
        Close the ssh connection.
        """
        if self.ssh != None:
            self.ssh.close()
        if self.ftp != None:
            self.ftp.close()