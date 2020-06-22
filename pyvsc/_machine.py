"""Helper classes/functions for identifying machine-specific attributes."""

import platform
import os
import shutil
import subprocess
import sys

from pyvsc._logging import get_rich_logger

_LOGGER = get_rich_logger(__name__)
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
        self.operating_system = platform.system().lower()
        self.processor = platform.processor()
        self.arch_size = self._arch_size()
        self.package_manager = self._package_manager()

    @staticmethod
    def _arch_size():
        return 64 if sys.maxsize > 2**32 else 32

    def _package_manager(self):
        """
        Identify the name of the package manager available on the current linux system.
        If the current system is not linux-based or the package manager does not meet any
        of the supported package managers, then return None.

        Returns:
            {str|None} -- The name of the package manager found on the current system.
        """
        if self.operating_system != 'linux':
            return None

        pkg_mgr_names = 'rpm dpkg pacman apt-get'
        pkg_mgr_cmd = f'for i in $(echo {pkg_mgr_names}); do command -v $i; done 2> /dev/null'
        pkg_mgr_path = subprocess.check_output(pkg_mgr_cmd, shell=True, universal_newlines=True)

        return os.path.basename(pkg_mgr_path).lower().strip()


#
# Machine Helper Functions
#

_MACHINE = Machine()


# pylint: disable=too-many-arguments, too-many-locals, too-many-branches
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

    In other words, a caller of this function may specify which values to return based off of the
    current machine's attributes. Values that are left as None will instead inherit the value of
    the nearest ancestor platform which has a truthy value specification.

    NOTE: If no truthy value is able to be determined based on the provided arguments and current
    system attributes, an OSError exception israised.

    Here are some examples:

    * EX 1: Caller wants to return the value 'linux' if the current system is running linux, but
      more specifically wanted to return 'linux-32' if the system has a 32-bit architecture:
      >>> platform_query(linux='linux', linux32='linux-32')

      NOTE: In the example above, a linux system with a 64-bit architecture would return 'linux',
      since we did not provide a specification for 64-bit linux systems.

    * EX 2: Caller wants to return the value 'linux-rpm' if the current system uses the RPM
      Package Manager (e.g. RedHat, CentOS, or Fedora), regardless of the architecture:
      >>> platform_query(linux='linux', rpm='linux-rpm')

      NOTE: In the example above, linux distributions which do not use RPM would return 'linux'.

    * EX 3: Caller wants to return 'osx' if the current platform is darwin.
      >>> platform_query(darwin='osx')

    * EX 4: Caller wants to return the value 'linux-deb' if the current platform is Debian-based,
      'linux-rpm' if RPM-based, and 'AppImage' if current platform is any other Linux-based distro:
      >>> platform_query(linux='AppImage', rpm='linux-rpm', deb='linux-deb')

    * EX 5: Caller wants to return the value 'linux' if current platform is Linux, 'darwin' if
      mac OS, and raise an exception if the current platform is any version of Windows.
      >>> platform_query(linux='linux', darwin='darwin', windows=None)


    Keyword Arguments:
        windows {str} -- Return value for systems running Windows (default: {'windows'})
        win32 {str} -- Return value for systems running Windows with a 32-bit architecture.
            If provided, overrides 'windows' (default: {None})
        win64 {str} -- Return value for systems running Windows with a 64-bit architecture. 
            If provided, overrides 'windows' (default: {None})
        darwin {str} -- Return value for systems running Mac OS (default: {'darwin'})
        linux {str} -- Return value for systems running a Linux distrobution (default: {'linux'})
        linux32 {str} -- Return value for systems running Linux with a 32-bit architecture.
            If provided, overrides 'linux' (default: {None})
        linux64 {str} -- Return value for systems running Linux with a 64-bit architecture.
            If provided, overrides 'linux' (default: {None})
        rpm {str} -- Return value for Linux systems that are RPM-based. If provided,
            overrides 'linux', 'linux32', 'linux64' (default: {None})
        rpm32 {str} -- Return value for Linux systems that are RPM-based and have a 32-bit system.
            If provided, overrides 'linux', 'linux32', 'rpm' (default: {None})
        rpm64 {str} -- Return value for Linux systems that are RPM-based and have a 32-bit system.
            If provided, overrides 'linux', 'linux64', 'rpm' (default: {None})
        deb {str} -- Return value for Linux systems that are Debian-based. If provided,
            overrides 'linux', 'linux32', 'linux64' (default: {None})
        deb32 {str} -- Return value for Linux systems that are Debian-based and have a 32-bit
            system. If provided, overrides 'linux', 'linux32', 'deb' (default: {None})
        deb64 {str} -- Return value for Linux systems that are Debian-based and have a 64-bit
            system. If provided, overrides 'linux', 'linux64', 'deb' (default: {None})

    Returns:
        str -- The specified string (as provided in the function arguments) based on the
            determined system attributes.

    Raises:
        OSError -- If no match can be determined from the provided arguments and system attributes.
    """
    machine_os = _MACHINE.operating_system
    machine_arch = _MACHINE.arch_size
    machine_pkg_mgr = _MACHINE.package_manager

    if machine_os == 'darwin':
        result = darwin

    elif machine_os == 'windows':
        if machine_arch == 32:
            result = next(win32, windows)
        else:
            result = next(win64, windows)

    elif machine_os == 'linux':
        if machine_pkg_mgr == 'rpm':
            if machine_arch == 32:
                result = next(rpm32, rpm, linux32, linux)
            else:
                result = next(rpm64, rpm, linux64, linux)

        elif machine_pkg_mgr in ['dpkg', 'apt-get']:
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
    # dmgs are darwin-only
    assert _MACHINE.operating_system == 'darwin'

    # mount the dmg image
    proc = subprocess.Popen(['hdiutil', 'attach', dmg_file_path],
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE,
                            encoding='utf-8')
    proc.wait()

    # find the mounted path
    mount_path = proc.stdout.read().split()[-1]
    _LOGGER.debug('Mounted %s at %s', dmg_file_path, mount_path)

    try:
        # find the .app at the mounted path
        app = next(f for f in os.listdir(mount_path) if f.endswith('.app'))
        _LOGGER.debug('Found application %s', app)

        # copy the .app to the Applications folder
        mounted_app_path = os.path.join(mount_path, app)
        applications_path = os.path.join(_DARWIN_INSTALL_LOCATION, app)
        shutil.copytree(mounted_app_path, applications_path)
        _LOGGER.info('Installed %s to %s', app, applications_path)

    except OSError as err:
        _LOGGER.error(err)

    finally:
        # unmount the dmg image
        proc = subprocess.Popen(['hdiutil', 'detach', mount_path],
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE,
                                encoding='utf-8')
        proc.wait()


def install_zip(zipped_path):
    """
    Installs a VSCode-like editor from a .zip file to the system.

    TODO: This currently only handles installing to Darwin systems. It may need to be
    expanded to handle installing to other systems, if code editors are downloaded as
    .zip archives on other systems.

    Arguments:
        zipped_path {str} -- Absolute path to the .zip location
    """
    if _MACHINE.operating_system != 'darwin':
        raise OSError('Your OS does not support installing VSCode editors from a .zip')

    os.system('unzip -q -o {} -d {}'.format(zipped_path, _DARWIN_INSTALL_LOCATION))
