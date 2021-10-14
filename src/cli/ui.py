import dicttoxml
import json
import logging
import os
import plistlib
import time
from info import name, version, os_ver, arch
from managers.tree import tree
from root import root


class UI:
    def __init__(self, dm):
        self.dm = dm

    def handle_cmd(self):
        options = [
            ('D', 'D.', self.discover),
            ('T', 'T.', self.dump_txt),
            ('J', 'J.', self.dump_json),
            ('X', 'X.', self.dump_xml),
            ('P', 'P.', self.dump_plist),
            ('Q', 'Q.', self.quit)
        ]

        cmd = input("\n\nPlease select an option: ")
        valid = False

        for option in options:
            if any(type(c) == str and cmd.upper() == c.upper() for c in option):
                self.clear()
                self.title()
                option[2]()

                print("Successfully executed.")
                print("Going back to main menu in 5 seconds...")

                time.sleep(5)

                self.clear()
                self.create_ui()
                valid = True

        if not valid:
            self.clear()
            print("Invalid option! Try again in 5 seconds...")

            time.sleep(5)

            self.clear()
            self.create_ui()

    def discover(self):
        for key in self.dm.info:
            val = tree(key, self.dm.info[key])
            print(val)

        exit(0)

    def dump_txt(self):
        with open(os.path.join(root, "info_dump.txt"), "w") as file:
            for key in self.dm.info:
                file.write(tree(key, self.dm.info[key]))
                file.write('\n')

            file.close()

    def dump_json(self):
        with open(os.path.join(root, "info_dump.json"), "w") as _json:
            _json.write(json.dumps(self.dm.info, indent=4, sort_keys=False))
            _json.close()

    def dump_xml(self):
        with open(os.path.join(root, "info_dump.xml"), "wb") as xml:
            dicttoxml.LOG.setLevel(logging.ERROR) # Disables debug prints from `dicttoxml`
            xml.write(dicttoxml.dicttoxml(self.dm.info, root=True))
            xml.close()

    def dump_plist(self):
        with open(os.path.join(root, "info_dump.plist"), "wb") as plist:
            plistlib.dump(self.dm.info, plist, sort_keys=False)
            plist.close()

    def quit(self):
        self.clear()
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

        self.clear()
        self.title()

        print(f"Program      :  {name}")
        print(f"Version      :  {version}")
        print(f"Platform     :  {os_ver}")
        print(f"Architecture :  {arch}")

        print("\n")

        for option in options:
            print("".join(option))

        self.handle_cmd()

    def clear(self):
        os.system('cls||clear')

    def title(self):
        spaces = " " * int((53 - len(name)) / 2)

        print(" " * 2 + "#" * 55)
        print(" #" + spaces + name + spaces + "#")
        print("#" * 55, "\n" * 2)
