import dicttoxml
import json
import logging
import os
import plistlib
import subprocess
import sys
from info import name, version, os_ver, arch, color_text
from managers.tree import tree
from root import root


class UI:
    """
    Instance responsible for properly formatting,
    displaying data about the system, providing options,
    and handling specific CLI commands.
    """

    def __init__(self, dm, logger):
        self.dm = dm
        self.dm.info = {k: v for (k, v) in self.dm.info.items(
        ) if self.dm.info[k] and (v[0] != {} if isinstance(v, list) else v != {})}
        self.logger = logger

    def handle_cmd(self, options=[]):
        cmd = input("\n\nPlease select an option: ")
        valid = False

        for option in options:
            if any(type(c) == str and cmd.upper() == c.upper() for c in option):
                self.clear()
                self.title()
                option[2]()

                print("Successfully executed.\n")
                self.enter()

                self.clear()
                self.create_ui()
                valid = True

        if not valid:
            self.clear()
            print("Invalid option!\n")
            self.enter()

            self.clear()
            self.create_ui()

    def discover(self):
        self.logger.info('Attempting to discover hardware...')
        for key in self.dm.info:
            is_empty = next(iter(self.dm.info[key]), {}) == {} if isinstance(
                self.dm.info[key], list) else self.dm.info[key] == {}

            if key and not is_empty:
                val = tree(key, self.dm.info[key])
                print(val)

        print(" ")

        options = [
            ('R. ', 'Return'),
            ('T. ', 'Dump as TXT'),
            ('J. ', 'Dump as JSON'),
            ('X. ', 'Dump as XML'),
            ('P. ', 'Dump as Plist'),
            ('Q. ', 'Quit')
        ]

        cmd_options = [
            ('R', 'R.', self.create_ui),
            ('T', 'T.', self.dump_txt),
            ('J', 'J.', self.dump_json),
            ('X', 'X.', self.dump_xml),
            ('P', 'P.', self.dump_plist),
            ('Q', 'Q.', self.quit)
        ]

        for option in options:
            print("".join(option))

        self.logger.info('Successfully ran \'discovery\'.')

        self.handle_cmd(cmd_options)

    def dump_txt(self):
        with open(os.path.join(root, "info_dump.txt"), "w", encoding="utf-8") as file:
            for key in self.dm.info:
                file.write(tree(key, self.dm.info[key]))
                file.write('\n')

            file.close()
            self.logger.info('Successfully dumped info to "info_dump.txt"')

    def dump_json(self):
        with open(os.path.join(root, "info_dump.json"), "w") as _json:
            _json.write(json.dumps(self.dm.info, indent=4, sort_keys=False))
            _json.close()
            self.logger.info('Successfully dumped info to "info_dump.json"')

    def dump_xml(self):
        with open(os.path.join(root, "info_dump.xml"), "wb") as xml:
            # Disables debug prints from `dicttoxml`
            dicttoxml.LOG.setLevel(logging.ERROR)
            xml.write(dicttoxml.dicttoxml(self.dm.info, root=True))
            xml.close()
            self.logger.info('Successfully dumped info to "info_dump.xml"')

    def dump_plist(self):
        with open(os.path.join(root, "info_dump.plist"), "wb") as plist:
            plistlib.dump(self.dm.info, plist, sort_keys=False)
            plist.close()
            self.logger.info('Successfully dumped info to "info_dump.plist"')

    def quit(self):
        self.clear()
        self.logger.info('Successfully exited.\n\n')
        exit(0)

    def create_ui(self):
        options = [
            ('D. ', 'Discover hardware'),
            ('T. ', 'Dump as TXT'),
            ('J. ', 'Dump as JSON'),
            ('X. ', 'Dump as XML'),
            ('P. ', 'Dump as Plist'),
            ('\n\n', 'Q. ', 'Quit')
        ]

        cmd_options = [
            ('D', 'D.', self.discover),
            ('T', 'T.', self.dump_txt),
            ('J', 'J.', self.dump_json),
            ('X', 'X.', self.dump_xml),
            ('P', 'P.', self.dump_plist),
            ('Q', 'Q.', self.quit)
        ]

        self.logger.info('Creating UI...')

        self.clear()
        self.title()

        if sys.platform.lower() == "darwin":
            hack = self.hack_disclaimer()

            if hack:
                print(f"{hack}\n")

        print(f"Program      :  {name}")
        print(f"Version      :  {version}")
        print(f"Platform     :  {os_ver}")
        print(f"Architecture :  {arch}")

        print("\n")

        for option in options:
            print("".join(option))

        self.logger.info('UI creation ran successfully.')

        self.handle_cmd(cmd_options)

    def clear(self):
        os.system('cls||clear')

    def enter(self):
        # “Hacky” way of detecting when
        # the Enter key is pressed down.
        if input("Press [enter] to return... ") != None:
            self.create_ui()

    def title(self):
        spaces = " " * int((53 - len(name)) / 2)

        print(color_text(" " * 2 + "#" * 55, "cyan"))
        print(color_text(" #" + spaces + name + spaces + "#", "cyan"))
        print(color_text("#" * 55 + "\n" * 2, "cyan"))

    def hack_disclaimer(self):
        kern_ver = int(os.uname().release.split('.')[0])

        if kern_ver > 19:
            kext_loaded = subprocess.run(['kmutil', 'showloaded', '--list-only', '--variant-suffix',
                                         'release'], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        else:
            kext_loaded = subprocess.run(
                ['kextstat', '-l'], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

        if [x in kext_loaded.stdout.decode().lower() for x in ('fakesmc', 'virtualsmc')]:
            return color_text("DISCLAIMER:\n"
                              "THIS IS BEING RUN ON A HACKINTOSH.\n"
                              "INFORMATION EXTRACTED MIGHT NOT BE COMPLETELY ACCURATE.",
                              "red"
                              )
