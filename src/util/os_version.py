import platform

from src.info import color_text

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
    22: f"macOS 13 {color_text('(Ventura)', 'cyan')}"
}

_platform = platform.system().lower()


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
    import distro
    os_ver = f"{distro.name()} ({distro.version()})"
