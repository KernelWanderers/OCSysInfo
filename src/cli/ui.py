import os
import subprocess
import sys
from platform import system
from sys import exit
from src.info import AppInfo, color_text, format_text, surprise
from src.util.os_version import os_ver
from src.util.dump_functions.text import dump_txt
from src.util.dump_functions.json import dump_json
from src.util.dump_functions.xml import dump_xml
from src.util.dump_functions.plist import dump_plist
from src.util.tree import tree


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
    spaces = " " * int((53 - len(AppInfo.name)) / 2)

    print(color_text(" " * 2 + "#" * 55, "cyan"))
    print(color_text(" #" + spaces + AppInfo.name + spaces + "#", "cyan"))
    print(color_text("#" * 55 + "\n" * 2, "cyan"))


def clear():
    if system().lower() == "windows":
        os.system("cls")
    elif system().lower() == "linux":
        os.system("clear")
    elif sys.platform == "darwin":
        # Special thanks to [A.J Uppal](https://stackoverflow.com/users/3113477/a-j-uppal) for this!
        # Original comment: https://stackoverflow.com/a/29887659/13120761

        # But, with more cursed bullshit!
        print("\033c", end="")
        print("\033[3J", end="")
        print("\033c", end="")


class UI:
    """
    Instance responsible for properly formatting,
    displaying data about the system, providing options,
    and handling specific CLI commands.
    """

    def __init__(self, dm, logger, dump_dir=AppInfo.root_dir):
        self.dm = dm
        self.logger = logger
        self.dump_dir = dump_dir
        self.state = "menu"

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

    def toggle_data(self):
        # Sanitise the UI
        clear()
        title()

        data_options = [
            ("C", "CPU"),
            ("G", "GPU"),
            ("B", "Motherboard" if system().lower() != "darwin" else "Vendor"),
            ("M", "Memory"),
            ("N", "Network"),
            ("A", "Audio"),
            ("I", "Input"),
            ("S", "Storage"),
        ]

        opts = ["C", "G", "B", "M", "N", "A", "I", "S"]

        for opt in data_options:
            toggled = " " if opt[1] in self.dm.off_data else "X"

            print(f"[{toggled}] ({opt[0]}) - {opt[1]}")

        selected = input(
            "Please select an option to toggle (or 'R'/'Q' to return): ")

        if selected.lower() == "q" or selected.lower() == "r":
            clear()
            title()

            print(color_text("Please wait while we adjust settings...\n", "green"))

            deletions = []
            asyncs    = []

            for opt in data_options:
                if (
                    not opt[1] in self.dm.off_data and 
                    not self.dm.info.get(opt[1])
                ):
                    asyncs.append(opt[1])

                if (
                    opt[1] in self.dm.off_data and
                    self.dm.info.get(opt[1])
                ):
                    deletions.append(opt[1])

            if asyncs:
                print(f"Attempting to retrieve dumps for: {', '.join(asyncs)}...\n")

                try:
                    self.dm.manager.dump()
                    self.dm.info = self.dm.manager.info

                    if (
                        not deletions and
                        input(color_text("[   OK   ] Successfully retrieved additional dumps.\n", "green") + 
                        " Press [enter] to return...") is not None
                    ):
                        pass
                except Exception:
                    if (
                        asyncs and 
                        input(color_text("[ FAILED ] Unable to retrieve dumps.", "red") + 
                        " Press [enter] to return...") is not None
                    ):
                        pass
                    elif not asyncs:
                        self.logger.error(
                            f"[UI]: UNKNOWN ERROR\n\t^^^^^^^{str(e)}",
                            __file__
                        )

            if deletions:
                print(f"Attempting to delete info for: {', '.join(deletions)}...\n")

                for delete in deletions:
                    if self.dm.info.pop(delete):
                        self.dm.off_data.append(delete)

                        print(color_text(
                            f"[   OK   ] Successfully deleted info for '{delete}'!",
                            "green"
                        ))
                    else:
                        print(color_text(
                            f"[  ERROR  ] Failed to delete info for '{delete}'!\n\t^^^^^^^{str(e)}",
                            "red"
                        ))

                if (
                    input(color_text("[   OK   ] Successfully deleted selected info.\n", "green") + 
                    " Press [enter] to return...") is not None
                ):
                    pass

            if self.state == "discovery":
                return self.discover()
            else:
                return self.create_ui()

        if (
            not selected.upper() in opts and
            input(color_text("Invalid option! Press [enter] to retry...", "red")) is not None
        ):
            self.toggle_data()

        option = data_options[opts.index(selected.upper())][1]

        if option in self.dm.off_data:
            del self.dm.off_data[self.dm.off_data.index(option)]
        else:
            self.dm.off_data.append(option)

        return self.toggle_data()

    def change_dump_dir(self):
        # Sanitise the UI
        clear()
        title()

        dump_dir = input("Please enter the directory (or 'Q' to exit.): ").strip().replace(
            '"', '').replace("'", "")

        if "~" in dump_dir:
            dump_dir = dump_dir.replace("~", os.path.expanduser("~"))

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

                if key and not is_empty and not key in self.dm.off_data:
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
            (color_text("A. ", "yellow"), "Toggle data"),
            (color_text("Q. ", "yellow"), "Quit"),
        ]

        cmd_options = [
            ("R", "R.", self.create_ui),
            ("T", "T.", self.dump_txt),
            ("J", "J.", self.dump_json),
            ("X", "X.", self.dump_xml),
            ("P", "P.", self.dump_plist),
            ("C", "C.", self.change_dump_dir),
            ("A", "A.", self.toggle_data),
            ("Q", "Q.", self.quit),
        ]

        for option in options:
            print("".join(option))

        self.logger.info("Successfully ran 'discovery'.", __file__)

        self.state = "discovery"

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
        exit(0)

    def create_ui(self):
        options = [
            (color_text("D. ", "yellow"), "Discover hardware"),
            (color_text("T. ", "yellow"), "Dump as TXT"),
            (color_text("J. ", "yellow"), "Dump as JSON"),
            (color_text("X. ", "yellow"), "Dump as XML"),
            (color_text("P. ", "yellow"), "Dump as Plist"),
            (color_text("C. ", "yellow"), "Change dump directory"),
            (color_text("A. ", "yellow"), "Toggle data"),
            ("\n\n", color_text("Q. ", "yellow"), "Quit"),
        ]

        cmd_options = [
            ("D", "D.", self.discover),
            ("T", "T.", self.dump_txt),
            ("J", "J.", self.dump_json),
            ("X", "X.", self.dump_xml),
            ("P", "P.", self.dump_plist),
            ("C", "C.", self.change_dump_dir),
            ("A", "A.", self.toggle_data),
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

            print(f"Program      :  {color_text(AppInfo.name, 'green')}")
            print(f"Version      :  {color_text(AppInfo.version, 'green')}")
            print(f"Platform     :  {color_text(os_ver, 'green')}")
            print(f"Architecture :  {color_text(AppInfo.arch, 'green')}")
            print(f"Current dump :  {color_text(self.dump_dir, 'cyan')}")

            print("\n")

            for option in options:
                print("".join(option))

            self.logger.info("UI creation ran successfully.", __file__)

            self.state = "menu"

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
