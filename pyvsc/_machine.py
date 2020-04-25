"""
Notes on supported platforms: 

* VSCode only offically supports the following platforms:
    - macOS 10.10+
    - Windows 7,8,10 (32-bit, 64-bit) (User, System)
    - Linux (Debian, Red Hat)

* VSCodium also supports:
    - arm64
    - AppImage
"""

class Machine():
    """
    Class that identifies system attributes that have an effect on determining
    which vscode editor(s) and/or extension(s) are appropriate for a pyvsc
    action.

    NOTE: This class is only concerned with the system attributes that help
    distinguish the current system within the scope of the supported vscode
    editors and their extensions. In doing so, default system attributes are
    used where it's deemed reasonable.
    """
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


#
# Machine Helper Functions
#

def platform_query(
    windows='windows',
    win32=None,
    win64=None,
    darwin='darwin',
    linux='linux',
    linux32=None,
    linux64=None,
    rpm=None,
    rpm32=None,
    rpm64=None,
    deb=None,
    deb32=None,
    deb64=None,
):
    """
    Allows for specifying the composition of a platform-related string based
    on the attributes of the current system as determined by the Machine class.

    In other words, a caller of this function may specify which values to
    return based off of the current machine's attributes. Values that are left
    as 'None' will instead inherit the value of the nearest ancestor platform
    which has a non-truthy value specification.

    Here are some examples:
    * EX 1: Caller wants to return the value 'linux' if the current system is
      running linux, but more specifically wanted to return 'linux-32' if the
      system has a 32-bit architecture:
      >>> platform_query(linux='linux', linux32='linux-32')

      NOTE: In the example above, a linux system with a 64-bit architecture
      would return 'linux', since we did not provide a specification for 64-bit
      linux systems.

    * EX 2: Caller wants to return the value 'linux-rpm' if the current system
      uses the RPM Package Manager (e.g. RedHat, CentOS, or Fedora), regardless
      of the architecture:
      >>> platform_query(linux='linux', rpm='linux-rpm')

      NOTE: In the example above, linux distributions which do not use RPM
      would return the value 'linux'.

    * EX 3: Caller wants to return 'osx' if the current platform is darwin.
      >>> platform_query(darwin='osx')

    * EX 4: Caller wants to return the value 'linux-deb' if the current 
        platform is Debian-based, 'linux-rpm' if the current platform is RPM-
        based, and 'AppImage' if the current platform is any other Linux-based
        distro:
      >>> platform_query(linux='AppImage', rpm='linux-rpm', deb='linux-deb')

    Keyword Arguments:
        windows {str} -- Return value for systems running Windows
            (default: {'windows'})
        win32 {str} -- Return value for systems running Windows with a 32-bit
            architecture. If provided, overrides 'windows' (default: {None})
        win64 {str} -- Return value for systems running Windows with a 64-bit
            architecture. If provided, overrides 'windows' (default: {None})
        darwin {str} -- Return value for systems running Mac OS
            (default: {'darwin'})
        linux {str} -- Return value for systems running a Linux distrobution
            (default: {'linux'})
        linux32 {str} -- Return value for systems running Linux with a 32-bit
            architecture. If provided, overrides 'linux' (default: {None})
        linux64 {str} -- Return value for systems running Linux with a 64-bit
            architecture. If provided, overrides 'linux' (default: {None})
        rpm {str} -- Return value for Linux systems that are RPM-based. If
            provided, overrides 'linux', 'linux32', 'linux64' (default: {None})
        rpm32 {str} -- Return value for Linux systems that are RPM-based and
            have a 32-bit system. If provided, overrides 'linux', 'linux32',
            'rpm' (default: {None})
        rpm64 {str} -- Return value for Linux systems that are RPM-based and
            have a 32-bit system. If provided, overrides 'linux', 'linux64',
            'rpm' (default: {None})
        deb {str} -- Return value for Linux systems that are Debian-based. If
            provided, overrides 'linux', 'linux32', 'linux64' (default: {None})
        deb32 {str} -- Return value for Linux systems that are Debian-based and
            have a 32-bit system. If provided, overrides 'linux', 'linux32',
            'deb' (default: {None})
        deb64 {str} -- Return value for Linux systems that are Debian-based and
            have a 64-bit system. If provided, overrides 'linux', 'linux64',
            'deb' (default: {None})

    Returns:
        str -- The specified string (as provided in the function arguments)
            based on the determined system attributes.
    """
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
