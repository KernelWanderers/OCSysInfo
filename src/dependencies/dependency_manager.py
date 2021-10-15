import os
import platform
import subprocess
import sys
import pkg_resources
from requirements import required as _required


def install_deps():
    required = set([_ for _ in _required if _])
    installed = {pkg.key for pkg in pkg_resources.working_set}
    missing = required - installed

    for missed in missing:
        print(f"Attempting to install {missed}...")
        try:
            subprocess.call([sys.executable, '-m', 'pip',
                            'install', missed, '--no-warn-script-location'], shell=True, stdout=open(os.devnull, "w"))
            print(f"Successfully installed {missed}!")
        except Exception as e:
            print(f"Error occurred. Unable to install {missed}")

    if platform.platform().lower() == "darwin":
        py_ver = str(sys.version_info.major) + \
            ('.' + str(sys.version_info.minor)
             if sys.version_info.minor != 0 else '')
        subprocess.run(
            '/Applications/Python\ {}/Install\ Certificates.command'.format(py_ver), shell=True)
