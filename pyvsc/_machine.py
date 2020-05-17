import logging

_LOGGER = logging.getLogger(__name__)
_LOGGER.setLevel(logging.NOTSET)

_DARWIN_INSTALL_LOCATION = '/Applications'

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
    Identify common attributes for current system.

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

    def _arch_size(self):
        from sys import maxsize
        return 64 if maxsize > 2**32 else 32

    def _package_manager(self):
        from os import path, popen

        if self.os != 'linux':
            return None

        package_manager_path = popen(
            'for i in $(echo rpm dpkg pacman apt-get); do command -v $i; '
            'done 2> /dev/null',
            shell=True
        ).rstrip()

        return path.basename(package_manager_path).lower()


#
# Machine Helper Functions
#

_MACHINE = Machine()


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
    as None will instead inherit the value of the nearest ancestor platform
    which has a truthy value specification.

    NOTE: If no truthy value is able to be determined based on the provided
    arguments and current system attributes, an OSError exception israised.

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
      platform is Debian-based, 'linux-rpm' if RPM-based, and 'AppImage' if the
      current platform is any other Linux-based distro:
      >>> platform_query(linux='AppImage', rpm='linux-rpm', deb='linux-deb')

    * EX 5: Caller wants to return the value 'linux' if the current platform
      is Linux, 'darwin' if the current platform is mac OS, and raise an
      exception if the current platform is any version of Windows.
      >>> platform_query(linux='linux', darwin='darwin', windows=None)


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

    Raises:
        OSError -- If no match can be determined from the provided arguments
            and system attributes.
    """
    machine_os = _MACHINE.os
    machine_arch = _MACHINE.arch_size
    machine_pkg_manager = _MACHINE.package_manager

    if machine_os == 'darwin':
        result = darwin
    elif machine_os == 'windows':
        if machine_arch == 32:
            result = next(win32, windows)
        else:
            result = next(win64, windows)
    elif machine_os == 'linux':
        if machine_pkg_manager == 'rpm':
            if machine_arch == 32:
                result = next(rpm32, rpm, linux32, linux)
            else:
                result = next(rpm64, rpm, linux64, linux)
        elif machine_pkg_manager in ['dpkg', 'apt-get']:
            if machine_arch == 32:
                result = next(deb32, deb, linux32, linux)
            else:
                result = next(deb64, deb, linux64, linux)
        else:
            if machine_arch == 32:
                result = next(linux32, linux)
            else:
                result = next(linux64, linux)

    if not result:
        raise OSError('The current platform is not supported')
    return result


#
# System installation helpers
#

def install_dmg(dmg_file_path):
    """
    Installs a .dmg file located at a given path into the /Applications folder.

    Arguments:
        dmg_file_path {str} -- The absolute path to the .dmg file.
    """
    from subprocess import Popen, PIPE
    from os import listdir, path
    from shutil import copytree

    # dmgs are darwin-only
    assert(_MACHINE.os == 'darwin')

    # mount the dmg image
    proc = Popen(['hdiutil', 'attach', dmg_file_path],
                 stdout=PIPE, stderr=PIPE, encoding='utf-8')
    proc.wait()

    # find the mounted path
    mount_path = proc.stdout.read().split()[-1]
    _LOGGER.debug('Mounted {} at {}'.format(dmg_file_path, mount_path))

    try:
        # find the .app at the mounted path
        app = next(f for f in listdir(mount_path) if f.endswith('.app'))
        _LOGGER.debug('Found application {}'.format(app))

        # copy the .app to the Applications folder
        mounted_app_path = path.join(mount_path, app)
        applications_path = path.join(_DARWIN_INSTALL_LOCATION, app)
        copytree(mounted_app_path, applications_path)
        _LOGGER.info('Installed {} to {}'.format(app, applications_path))

    except Exception as e:
        _LOGGER.error(e)

    finally:
        # unmount the dmg image
        proc = Popen(['hdiutil', 'detach', mount_path],
                     stdout=PIPE, stderr=PIPE, encoding='utf-8')
        proc.wait()


def install_zip(zipped_path):
    """
    Installs a VSCode-like editor from a .zip file to the system

    Arguments:
        zipped_path {str} -- Absolute path to the .zip location
    """
    from os import system
    if _MACHINE.os == 'darwin':
        install_path = _DARWIN_INSTALL_LOCATION
        system('unzip -q -o {} -d {}'.format(zipped_path, install_path))
    else:
        raise('Your OS does not support installing VSCode editors from a .zip')


# TODO: handle installation types for other systems.
