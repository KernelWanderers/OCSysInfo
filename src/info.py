"""
The only purpose for this file is to hold metadata
for OCSysInfo, and is not used by anything other than
the UI functions.
"""

import platform
import distro

name = "OCSysInfo"
version = "0.0.1-alpha"
os_ver = ""
arch = platform.machine()
_platform = platform.system().lower()

if _platform == "darwin":
    os_ver = f"{platform.platform().split('-')[0]} ({platform.mac_ver()[0]})"
elif _platform == "windows":
    os_ver = f"{platform.system()} ({platform.version()})"
elif _platform == "linux":
    os_ver = f"{distro.name()} ({distro.version()})"
