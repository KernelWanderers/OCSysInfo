import os
import platform
import subprocess
import sys
import pkg_resources


def install_deps():
    required = set(filter(lambda _: len(_), {
                   '"requests"',
                   '"distro"',
                   '"dicttoxml"',
                   '"pyobjc"' if sys.platform.lower() == 'darwin' else ''
                   }))
    installed = {pkg.key for pkg in pkg_resources.working_set}
    missing = installed - required

    for missed in missing:
        print(f"Attempting to install {missed}...")
        try:
            subprocess.call([sys.executable, '-m', 'pip',
                             'install', missed], shell=True, stdout=open(os.devnull, "w"))

            print(f"Successfully installed {missed}!")
        except:
            print(f"Error occurred. Unable to install {missed}")

    if platform.platform().lower() == "darwin":
        py_ver = str(sys.version_info.major) + \
            ('.' + str(sys.version_info.minor)
             if sys.version_info.minor != 0 else '')
        subprocess.run(
            '/Applications/Python\ {}/Install\ Certificates.command'.format(py_ver), shell=True)
