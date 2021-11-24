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

# Colours!
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
            final_string = f"{format_var}{final_string}"
    final_string += end_formatting
    return final_string


version_dict = {
    6: f"Mac OS X 10.2 {color_text('(Jaguar)', 'cyan')}",
    7: f"Mac OS X 10.3 {color_text('(Panther)', 'cyan')}",
    8: f"Mac OS X 10.4 {color_text('(Tiger)', 'cyan')}",
    9: f"Mac OS X 10.5 {color_text('(Leopard)', 'cyan')}",
    10: f"Mac OS X 10.6 {color_text('(Snow Leopard)', 'cyan')}",
    11: f"Mac OS X 10.7 {color_text('(Lion)', 'cyan')}",
    12: f"OS X 10.8 {color_text('(Mountain Lion)', 'cyan')}",
    13: f"OS X 10.9 {color_text('(Mavericks)', 'cyan')}",
    14: f"OS X 10.10 {color_text('(Yosemite)', 'cyan')}",
    15: f"OS X 10.11 {color_text('(El Capitan)', 'cyan')}",
    16: f"macOS 10.12 {color_text('(Sierra)', 'cyan')}",
    17: f"macOS 10.13 {color_text('(High Sierra)', 'cyan')}",
    18: f"macOS 10.14 {color_text('(Mojave)', 'cyan')}",
    19: f"macOS 10.15 {color_text('(Catalina)', 'cyan')}",
    20: f"macOS 11 {color_text('(Big Sur)', 'cyan')}",
    21: f"macOS 12 {color_text('(Monterey)', 'cyan')}",
}


def macos_kernel_version(release_string=None):
    """
    Returns the version of the Mac OS X kernel.
    """
    if not release_string:
        release_string = str(platform.release())
    release_string = release_string.split(".")[0]

    version_name = version_dict.get(
        int(release_string),
        color_text("Unknown", "cyan")
        if int(release_string) > 21 or int(release_string) <= 0
        else f"Mac OS X {color_text(f'(Kernel version: {release_string})', 'cyan')}",
    )
    return version_name


if _platform == "darwin":
    os_ver = macos_kernel_version()
elif _platform == "windows":
    os_ver = f"{platform.system()} ({platform.version()})"
elif _platform == "linux":
    os_ver = f"{distro.name()} ({distro.version()})"

surprise = f"""{cyan}
 __     __            ______                    _    _____ _   
 \ \   / /           |  ____|                  | |  |_   _| |  
  \ \_/ /__  _   _   | |__ ___  _   _ _ __   __| |    | | | |_ 
   \   / _ \| | | |  |  __/ _ \| | | | '_ \ / _` |    | | | __|
    | | (_) | |_| |  | | | (_) | |_| | | | | (_| |   _| |_| |_ 
    |_|\___/ \__,_|  |_|  \___/ \__,_|_| |_|\__,_|  |_____|\__|


{yellow}⢀⣠⣾⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⠀⠀⠀⠀⣠⣤⣶⣶
⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⠀⠀⠀⢰⣿⣿⣿⣿
⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣧⣀⣀⣾⣿⣿⣿⣿
⣿⣿⣿⣿⣿⡏⠉⠛⢿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⡿⣿
⣿⣿⣿⣿⣿⣿⠀⠀⠀⠈⠛⢿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⠿⠛⠉⠁⠀⣿
⣿⣿⣿⣿⣿⣿⣧⡀⠀⠀⠀⠀⠙⠿⠿⠿⠻⠿⠿⠟⠿⠛⠉⠀⠀⠀⠀⠀⣸⣿
⣿⣿⣿⣿⣿⣿⣿⣷⣄⠀⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⣴⣿⣿
⣿⣿⣿⣿⣿⣿⣿⣿⣿⠏⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠠⣴⣿⣿⣿⣿
⣿⣿⣿⣿⣿⣿⣿⣿⡟⠀⠀{end_formatting}⢰⣹⡆⠀⠀⠀⠀⠀⠀⣭⣷⠀{yellow}⠀⠀⠸⣿⣿⣿⣿
⣿⣿⣿⣿⣿⣿⣿⣿⠃⠀⠀⠈⠉⠀⠀⠤⠄⠀⠀⠀⠉⠁⠀⠀⠀⠀⢿⣿⣿⣿
⣿⣿⣿⣿⣿⣿⣿⣿{red}⢾⣿⣷{yellow}⠀⠀⠀⠀⡠⠤⢄⠀⠀⠀{red}⠠⣿⣿⣷{yellow}⠀⢸⣿⣿⣿
⣿⣿⣿⣿⣿⣿⣿⣿⡀⠉⠀⠀⠀⠀⠀⢄⠀⢀⠀⠀⠀⠀⠉⠉⠁⠀⠀⣿⣿⣿
⣿⣿⣿⣿⣿⣿⣿⣿⣧⠀⠀⠀⠀⠀⠀⠀⠈⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢹⣿⣿
⣿⣿⣿⣿⣿⣿⣿⣿⣿⠃⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢸⣿⣿{end_formatting}
"""
