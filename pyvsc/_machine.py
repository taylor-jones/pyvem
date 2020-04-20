class Machine():
    def __init__(self):
        from platform import system, processor
        self.os = system().lower()
        self.processor = processor()
        self.arch_size = self._arch_size()
        self.package_manager = self._package_manager()
        self.distro_extension = self._distro_extension()
        self.distro_query = self._distro_query()

    def _arch_size(self):
        from sys import maxsize
        return 64 if maxsize > 2**32 else 32


    def _package_manager(self):
        from os import path, popen
        if self.os != 'linux':
            return None

        package_manager_path = popen(
            'for i in $(echo rpm dpkg pacman apt-get); do command -v $i; done 2> /dev/null',
            shell=True
        ).rstrip()

        return path.basename(package_manager_path)


    def _distro_extension(self):
        # mac
        if self.os == 'darwin':
            return 'dmg'

        # linux
        if self.os == 'linux':
            pm = self.package_manager

            if pm == 'rpm':
                return 'rpm'
            elif pm in ['dpkg', 'apt-get']:
                return 'deb'
            else:
                return 'AppImage'

        # windows
        if self.os == 'windows':
            return 'exe'


    def _distro_query(self):
        """
        Determine the VSCode distribution endpoint based on the platform that
        can be determined from the current system.

        Raises:
            OSError: If an unsupported platform is identified

        Returns:
            str -- Query endpoint that can be used to get VSCode editor data.
        """
        # mac
        if self.os == 'darwin':
            return self.os

        # linux
        if self.os == 'linux':
            pm = self.package_manager
            if pm == 'rpm':
                return 'linux-rpm-x64'
            elif pm in ['dpkg', 'apt-get']:
                return 'linux-deb-x64'
            else:
                return 'linux-x64'

        # not supported
        raise OSError('%s is not supported at this time.' % (self.os))



def machine_query(
    windows='windows',
    win32=None,
    win64=None,
    darwin='darwin',
    linux='linux',
    linux64=None,
    linux32=None,
    rpm=None,
    rpm32=None,
    rpm64=None,
    deb=None,
    deb32=None,
    deb64=None,
):
    machine = Machine()
    m_os = machine.os
    m_arch = machine.arch_size
    m_pkg = machine.package_manager
    
    if m_os == 'darwin':
        return darwin
    elif m_os == 'windows':
        if m_arch == 32:
            return next(win32, windows)
        else:
            return next(win64, windows)
    elif m_os == 'linux':
        if m_pkg == 'rpm':
            if m_arch == 32:
                return next(rpm32, rpm, linux32, linux)
            else:
                return next(rpm64, rpm, linux64, linux)
        elif m_pkg in ['dpkg', 'apt-get']:
            if m_arch == 32:
                return next(deb32, deb, linux32, linux)
            else:
                return next(deb64, deb, linux64, linux)
        else:
            if m_arch == 32:
                return next(linux32, linux)
            else:
                return next(linux64, linux)

