import os
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
                            'install', missed, '--no-warn-script-location'], stdout=open(os.devnull, "w"), shell=False)
            print(f"Successfully installed {missed}!")
        except Exception as e:
            path = os.path.join(os.path.dirname(
                os.path.abspath(__file__)), "error_log.txt")
            with open(path, "w") as file:
                file.write(
                    f"Failed to execute 'pip install -m {missed} --no-warn-script-location'\nError logs:\n\n{str(e)}")
            print(
                f"Error occurred. Unable to install {missed}\n\nDump is in: {path}")

    if sys.platform.lower() == "darwin":
        py_ver = str(sys.version_info.major) + \
            ('.' + str(sys.version_info.minor)
             if sys.version_info.minor != 0 else '')
        try:
            print("Attempting to install certificates for macOS...")
            subprocess.call(
                ['/Applications/Python {}/Install Certificates.command'.format(py_ver)], shell=False)
            print("Successfully installed certificates!")
        except Exception as e:
            path = os.path.join(os.path.dirname(
                os.path.abspath(__file__)), "macos_error_log.txt")
            with open(path, "w") as file:
                file.write(
                    f"Failed to install certificates.\nError logs:\n\n{str(e)}")
            print(
                f"Error occurred. Unable to install certificates.\n\nDump is in: {path}")
