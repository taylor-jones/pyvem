import os
import platform



def get_package_manager():
    if _OPERATING_SYSTEM != 'linux':
        return None

    pkg_mgr_path = os.popen(
        'for i in $( echo rpm dpkg pacman apt-get ); do command -v $i; done 2> /dev/null',
        shell=True
    ).rstrip()

    return os.path.basename(pkg_mgr_path)


def get_distribution_extension():
    if _OPERATING_SYSTEM == 'darwin':
        return 'dmg'
    if _OPERATING_SYSTEM == 'linux':
        if _PACKAGE_MANAGER == 'rpm':
            return 'rpm'
        elif _PACKAGE_MANAGER == 'dpkg' or _PACKAGE_MANAGER == 'apt-get':
            return 'deb'
        else:
            return 'AppImage'

    if _OPERATING_SYSTEM == 'windows':
        return 'exe'


def get_distribution_query():
    """
    Determine the VSCode distribution endpoint based on the platform that
    can be determined from the current system.

    Raises:
        OSError: If an unsupported platform is identified

    Returns:
        str -- The query endpoint that can be used to fetch VSCode editor data.
    """
    # mac
    if _OPERATING_SYSTEM == 'darwin':
        return _OPERATING_SYSTEM

    # linux
    if _OPERATING_SYSTEM == 'linux':
        if _PACKAGE_MANAGER == 'rpm':
            return 'linux-rpm-x64'
        elif _PACKAGE_MANAGER == 'dpkg' or _PACKAGE_MANAGER == 'apt-get':
            return 'linux-deb-x64'
        else:
            return 'linux-x64'

    # not supported
    raise OSError('%s is not supported at this time.' % (_OPERATING_SYSTEM))


_OPERATING_SYSTEM = platform.system().lower()
_PROCESSOR = platform.processor()
_PACKAGE_MANAGER = get_package_manager()
