"""
The only purpose for this file is to hold metadata
for OCSysInfo, and is not used by anything other than
the UI functions.
"""

import platform
import os
import sys
from platform import system

dir_delim = "\\" if platform.system().lower() == "windows" else "/"

class AppInfo:
    name = "OCSysInfo"
    version = "v1.0.5"
    os_ver = ""
    arch = platform.machine()
    root_dir = ""

    def set_root_dir(new_dir):
        if not os.path.isdir(new_dir):
            return

        try:
            AppInfo.root_dir = AppInfo.sanitise_dir(new_dir)
        except Exception:
            return

        return AppInfo.root_dir

    def sanitise_dir(dir):
        if getattr(sys, 'frozen', False):
            dir = os.path.dirname(sys.executable)
            os.chdir(dir)
        else:
            dir = os.path.dirname(os.path.abspath(__file__))

        if "src" in dir.split(dir_delim):
            dir = dir_delim.join(dir.split(dir_delim)[:-1])

        return dir

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