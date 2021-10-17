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

# Colors!
pink = '\033[95m'
blue = '\033[94m'
cyan = '\033[96m'
green = '\033[92m'
yellow = '\033[93m'
red = '\033[91m'
format_bold = '\033[1m'
format_underline = '\033[4m'
end_formatting = '\033[0m'


def color_text(text, color):
    color_var = globals().get(color) if globals().get(color) else green
    return f"{color_var}{text}{end_formatting}"
