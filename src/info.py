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
pink = "\033[95m"
blue = "\033[94m"
cyan = "\033[96m"
green = "\033[92m"
yellow = "\033[93m"
red = "\033[91m"
bold = "\033[1m"
underline = "\033[4m"
end_formatting = "\033[0m"


def color_text(text, color):
    color_var = globals().get(color) if globals().get(color) else green
    return f"{color_var}{text}{end_formatting}"


def format_text(text, formatting):
    formatting_list = formatting.split("+")
    final_string = text
    for format in formatting_list:
        format_var = globals().get(format) if globals().get(format) else None
        if format_var:
            final_string = f"{format_var}{final_string}{end_formatting}"
    return final_string
