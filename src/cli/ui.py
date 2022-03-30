import os
import subprocess
import sys
from src.info import name, version, arch, color_text, format_text, surprise
from src.info import root_dir as root
from src.util.os_version import os_ver
from src.util.dump_functions.text import dump_txt
from src.util.dump_functions.json import dump_json
from src.util.dump_functions.xml import dump_xml
from src.util.dump_functions.plist import dump_plist
from src.managers.tree import tree


def hack_disclaimer():
    kern_ver = int(os.uname().release.split(".")[0])

    if kern_ver > 19:
        kext_loaded = subprocess.run(
            ["kmutil", "showloaded", "--list-only", "--variant-suffix", "release"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )
    else:
        kext_loaded = subprocess.run(
            ["kextstat", "-l"], stdout=subprocess.PIPE, stderr=subprocess.STDOUT
        )

    if any(x in kext_loaded.stdout.decode().lower() for x in ("fakesmc", "virtualsmc")):
        return color_text(
            format_text("DISCLAIMER:\n", "bold+underline"), "red"
        ) + color_text(
            f"THIS IS BEING RUN ON A HACKINTOSH.\n"
            f"INFORMATION EXTRACTED MIGHT NOT BE COMPLETELY ACCURATE.",
            "red",
        )


def title():
    spaces = " " * int((53 - len(name)) / 2)

    print(color_text(" " * 2 + "#" * 55, "cyan"))
    print(color_text(" #" + spaces + name + spaces + "#", "cyan"))
    print(color_text("#" * 55 + "\n" * 2, "cyan"))


def clear():
    if sys.platform == "win32":
        os.system("cls")
    elif sys.platform == "darwin":
        # Special thanks to [A.J Uppal](https://stackoverflow.com/users/3113477/a-j-uppal) for this!
        # Original comment: https://stackoverflow.com/a/29887659/13120761

        # But, with more cursed bullshit!
        print("\033c", end="")
        print("\033[3J", end="")
        print("\033c", end="")
    elif sys.platform == "linux":
        os.system("clear")


class UI:
    """
    Instance responsible for properly formatting,
    displaying data about the system, providing options,
    and handling specific CLI commands.
    """

    def __init__(self, dm, logger):
        self.dm = dm
        self.logger = logger
        self.dump_dir = root

    def handle_cmd(self, options=[]):
        cmd = input("\n\nPlease select an option: ")
        valid = False
        if cmd.lower() == "yee":
            clear()
            print(surprise)
            self.logger.info("Easter-egg discovered", __file__)
            valid = True
            self.enter()
            clear()
            self.create_ui()
        for option in options:
            if any(type(c) == str and cmd.upper() == c.upper() for c in option):
                clear()
                title()
                data = option[2]()

                print(data if data else "Successfully executed.\n")
                self.enter()

                clear()
                self.create_ui()
                valid = True

        if not valid:
            clear()
            print("Invalid option!\n")
            self.enter()

            clear()
            self.create_ui()

    def change_dump_dir(self):
        # Sanitise the UI
        clear()
        title()

        dump_dir = input("Please enter the directory (or 'Q' to exit.): ").strip().replace(
            '"', '').replace("'", "")

        if not len(dump_dir):
            clear()
            title()
            if input(color_text("Please specify a directory! Press [enter] to retry... ", "yellow")) is not None:
                self.change_dump_dir()

        elif dump_dir.lower() == "q":
            self.create_ui()

        elif not os.path.isdir(dump_dir):
            clear()
            title()
            if input(color_text("Invalid directory! Press [enter] to retry... ", "yellow")) is not None:
                self.change_dump_dir()

        else:
            self.dump_dir = dump_dir
            self.create_ui()

    def discover(self):
        self.logger.info("Attempting to discover hardware...", __file__)
        for key in self.dm.info:
            try:
                is_empty = (
                    next(iter(self.dm.info[key]), {}) == {}
                    if isinstance(self.dm.info[key], list)
                    else self.dm.info[key] == {}
                )

                if key and not is_empty:
                    val = tree(key, self.dm.info[key])
                    print(val)
            except Exception as e:
                self.logger.critical(
                    f"Failed to discover hardware! This should not happen.\n\t^^^^^^^^^{str(e)}",
                    __file__,
                )
                raise e

        print(" ")

        options = [
            (color_text("R. ", "yellow"), "Return"),
            (color_text("T. ", "yellow"), "Dump as TXT"),
            (color_text("J. ", "yellow"), "Dump as JSON"),
            (color_text("X. ", "yellow"), "Dump as XML"),
            (color_text("P. ", "yellow"), "Dump as Plist"),
            (color_text("C. ", "yellow"), "Change dump directory"),
            (color_text("Q. ", "yellow"), "Quit"),
        ]

        cmd_options = [
            ("R", "R.", self.create_ui),
            ("T", "T.", self.dump_txt),
            ("J", "J.", self.dump_json),
            ("X", "X.", self.dump_xml),
            ("P", "P.", self.dump_plist),
            ("C", "C.", self.change_dump_dir),
            ("Q", "Q.", self.quit),
        ]

        for option in options:
            print("".join(option))

        self.logger.info("Successfully ran 'discovery'.", __file__)

        self.handle_cmd(cmd_options)

    def dump_txt(self):
        return dump_txt(self.dm, self.dump_dir, self.logger)

    def dump_json(self):
        return dump_json(self.dm, self.dump_dir, self.logger)
    
    def dump_xml(self):
        return dump_xml(self.dm, self.dump_dir, self.logger)

    def dump_plist(self):
        return dump_plist(self.dm, self.dump_dir, self.logger)

    def quit(self):
        clear()
        self.logger.info("Successfully exited.\n\n")
        sys.exit(0)

    def create_ui(self):
        options = [
            (color_text("D. ", "yellow"), "Discover hardware"),
            (color_text("T. ", "yellow"), "Dump as TXT"),
            (color_text("J. ", "yellow"), "Dump as JSON"),
            (color_text("X. ", "yellow"), "Dump as XML"),
            (color_text("P. ", "yellow"), "Dump as Plist"),
            (color_text("C. ", "yellow"), "Change dump directory"),
            ("\n\n", color_text("Q. ", "yellow"), "Quit"),
        ]

        cmd_options = [
            ("D", "D.", self.discover),
            ("T", "T.", self.dump_txt),
            ("J", "J.", self.dump_json),
            ("X", "X.", self.dump_xml),
            ("P", "P.", self.dump_plist),
            ("C", "C.", self.change_dump_dir),
            ("Q", "Q.", self.quit),
        ]

        self.logger.info("Creating UI...", __file__)

        try:
            clear()
            title()

            if sys.platform.lower() == "darwin":
                hack = hack_disclaimer()
                if hack:
                    print(f"{hack}\n")

            print(f"Program      :  {color_text(name, 'green')}")
            print(f"Version      :  {color_text(version, 'green')}")
            print(f"Platform     :  {color_text(os_ver, 'green')}")
            print(f"Architecture :  {color_text(arch, 'green')}")
            print(f"Current dump :  {color_text(self.dump_dir, 'cyan')}")

            print("\n")

            for option in options:
                print("".join(option))

            self.logger.info("UI creation ran successfully.", __file__)

            self.handle_cmd(cmd_options)
        except Exception as e:
            self.logger.critical(
                f"Failed to create UI! This should not happen. \n\t^^^^^^^^^{str(e)}",
                __file__,
            )

    def enter(self):
        # “Hacky” way of detecting when
        # the Enter key is pressed down.
        if input(color_text("Press [enter] to return... ", "yellow")) is not None:
            self.create_ui()
