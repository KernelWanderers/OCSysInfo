import subprocess
import sys
import platform
import pkg_resources


def install_dep():
    try:
        from pip import main as pipmain
    except ImportError:
        from pip._internal import main as pipmain

    required = set(filter(lambda _: len(_), {
                   'psutil', 'requests', 'pyobjc' if platform.platform().lower() == 'darwin' else ''}))
    installed = {pkg.key for pkg in pkg_resources.working_set}
    missing = installed - required

    if missing:
        pipmain(['install', '-r', *missing])

    if platform.platform().lower() == "darwin":
        py_ver = str(sys.version_info.major) + \
            ('.' + str(sys.version_info.minor)
             if sys.version_info.minor != 0 else '')
        subprocess.run(
            '/Applications/Python\ {}/Install\ Certificates.command'.format(py_ver), shell=True)