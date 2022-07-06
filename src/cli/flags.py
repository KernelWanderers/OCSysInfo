import os
from sys import exit, argv
from src.cli.ui import clear
from src.info import color_text, AppInfo
from src.util.debugger import Debugger as debugger
from src.util.dump_functions.text import dump_txt
from src.util.dump_functions.json import dump_json
from src.util.dump_functions.xml import dump_xml
from src.util.dump_functions.plist import dump_plist
from src.managers.devicemanager import DeviceManager


class FlagParser:
    """
    Instance responsible for handling command-line arguments
    in the very case that they're presented.
    """

    def __init__(self, logger, dm=None, offline=False):
        self.args = argv[1:]
        self.dm = dm
        self.toggled_off = []

        if "--off-data" in self.args:
            if len(self.args) == (self.args.index("--off-data") + 1):
                debugger.log_dbg(color_text("--> No data for '--off-data'!", "red"))
                exit(1)

            self.off_data(self.args[self.args.index("--off-data") + 1])

        if not self.dm and not list(filter(lambda x: "-h" in x.lower(), self.args)):
            print(color_text(
                "--> Analyzing hardware... (this might take a while, don't panic)", "red"))
            self.dm = DeviceManager(logger, off_data=self.toggled_off, offline=offline)
            self.dm.info = {
                k: v
                for (k, v) in self.dm.info.items()
                if self.dm.info[k] and (v[0] != {} if isinstance(v, list) else v != {})
            }

        self.logger = logger
        self.completed = []
        self.missing = []
        self.interactive = not "--no-interactive" in self.args

        if (
            not self.interactive or 
            "--offline" in self.args or
            (
                "-dbg"    in self.args or 
                "-debug"  in self.args or
                "--debug" in self.args
            )
        ):
            for i in range(len(self.args)):
                print("ARGS: ", self.args[i])
                if (
                    "--no-interactive" in self.args[i].lower() or
                    "--offline" in self.args[i].lower() or
                    self.args[i].lower() in ["-dbg", "--debug", "-debug"]
                ):
                    del self.args[i]

        self.flags = [
            {
                "Aliases": ["--help", "-H"],
                "Command": self.help,
                "Log": {
                    "Failed": "Failed to print help page.",
                    "Success": "Successfully printed help page.",
                },
            },
            {
                "Aliases": ["--text", "--txt", "-tx", "-T"],
                "Command": dump_txt,
                "Log": {
                    "Failed": "Failed to dump to TXT file (FLAGS)",
                    "Success": "Successfully dumped to TXT file (FLAGS)",
                },
            },
            {
                "Aliases": ["--json", "-J"],
                "Command": dump_json,
                "Log": {
                    "Failed": "Failed to dump to JSON file (FLAGS)",
                    "Success": "Successfully dumped to JSON file (FLAGS)",
                },
            },
            {
                "Aliases": ["--xml", "-X"],
                "Command": dump_xml,
                "Log": {
                    "Failed": "Failed to dump to XML file (FLAGS)",
                    "Success": "Successfully dumped to XML file (FLAGS)",
                },
            },
            {
                "Aliases": ["--plist", "-P"],
                "Command": dump_plist,
                "Log": {
                    "Failed": "Failed to dump to Plist file (FLAGS)",
                    "Success": "Successfully dumped to Plist file (FLAGS)",
                },
            },
        ]

        self.handle(self.parse_flags(self.args))

    def help(self):
        try:
            clear()

            # List of possible arguments
            arguments = [
                (
                    "[--help]",
                    "prints this help page"
                ),
                (
                    "[--text]  <path>",
                    "dumps hardware information into a TXT file, inside of the specified directory",
                ),
                (
                    "[--json]  <path>",
                    "dumps hardware information into a JSON file, inside of the specified directory",
                ),
                (
                    "[--xml]   <path>",
                    "dumps hardware information into an XML file, inside of the specified directory",
                ),
                (
                    "[--plist] <path>",
                    "dumps hardware information into a plist file, inside of the specified directory",
                ),
                (
                    "[--off-data] \"{data}\"",
                    "disables detecting particular data (such as CPU, GPU, etc.) - must supply array under string."
                ),
                (
                    "[--no-interactive]",
                    "disables dynamic prompts for missing/invalid values (such as invalid dump types and [missing] paths)",
                ),
                (
                    "[--offline]",
                    "runs the application in OFFLINE mode, regardless of whether or not an internet connection is available"
                ),
                (
                    "[-dbg/-debug/--debug]",
                    "runs the application in DEBUG mode."
                )
            ]

            longest = self._longest(arguments)

            title = "OCSysInfo CLI Help Page"
            print(" " * 2 + "#" * (len(title) + 22))
            print(" " + "#" + " " * 10 + title + " " * 10 + "#")
            print("#" * (len(title) + 22), "\n" * 2)
            print(
                "<executable> \n  | [--help/-H] \n  | [--text/--txt/-tx/-T] \n  | [--json/-J] \n  | [--xml/-X] \n  | [--plist/-P]\n  | [--no-interactive]\n  | [--offline]\n"
            )

            for argument in arguments:
                if argument[0] == "":
                    print()
                    continue

                print(
                    argument[0]
                    + " " * (longest - len(argument[0]))
                    + " — "
                    + argument[1]
                )

            print(
                "\n\nExample:\n  <executable> -T ~/Downloads/myfolder -J ~/Downloads -X ~/Documents -P . --off-data \"{Memory, Network}\""
            )
        except Exception as e:
            raise e

    # Reminder: Thank Dids

    def handle(self, vals):
        if not vals or len(vals) < 1:
            return

        for val in vals:
            if val.get("Type") == "UNKNOWN" or not val.get("Path"):
                self.missing.append(val)
            elif val.get("Type") != "UNKNOWN" and val.get("Path"):
                self.completed.append(val)

        if self.missing:
            self.prompts()

        for completed in self.completed:
            desc = self.dump_desc(completed.get('Type'))

            try:
                ok = color_text("   OK   ", "green")

                print(
                    f"[{ok}]   Attempting to dump {desc} to {completed.get('Path')}...")
                self.logger.info(
                    f"Attempting to dump {desc} file to {completed.get('Path')}...",
                    __file__,
                )

                completed.get("Command")(
                    self.dm, completed.get("Path"), self.logger)

                print(
                    f"[{ok}]   Successfully dumped hardware information to {desc} file! Stored in {completed.get('Path')}\n"
                )
                self.logger.info(
                    f"Successfully dumped hardware information to {desc} file! Stored in {completed.get('Path')}",
                    __file__,
                )
            except Exception as e:
                fail = color_text(" FAILED ", "red")
                print(
                    f"[{fail}]   Failed to dump to {desc} file in {completed.get('Path')}...",
                    __file__,
                )
                self.logger.error(
                    f"Failed to dump to {desc}!\n\t^^^^^^^^^^^^{str(e)}",
                    __file__,
                )

        self.logger.info("Successfully exited after dumping.\n\n", __file__)
        exit(0)

    def off_data(self, arr):
        del self.args[self.args.index("--off-data")]
        del self.args[self.args.index(orig)]

        orig = arr
        arr = arr.replace("{", "").replace("}", "").split(", ")

        if not arr:
            return

        repl = {
            "cpu": "CPU",
            "gpu": "GPU",
            "motherboard": "Motherboard",
            "memory": "Memory",
            "network": "Network",
            "audio": "Audio",
            "input": "Input",
            "storage": "Storage",
        }

        for val in arr:
            val = repl[val.lower()]

        self.toggled_off = arr

    def parse_flags(self, args):
        if list(filter(lambda x: "-h" in x.lower(), args)):
            self.help()
            exit(0)

        if "--off-data" in args:
            return self.off_data(args[args.index("--off-data") + 1])

        vals = []

        for i in range(len(args)):
            if not args[i].startswith("-"):
                continue

            dump_type = self.dump_type(args[i])

            if len(args) <= i:
                vals.append({
                    "Type": dump_type,
                    "Original": args[i],
                    "Path": None,
                    "Command": self.dump_func(dump_type)
                })

            else:
                vals.append({
                    "Type": dump_type,
                    "Original": args[i],
                    "Path": self.parse_path(args[i + 1]) if len(args) > (i + 1) and not args[i + 1].startswith("-") else None,
                    "Command": self.dump_func(dump_type)
                })

        return vals

    def dump_type(self, value):
        dump_type = "UNKNOWN"

        for flag in self.flags:
            aliases = flag.get("Aliases", [])
            for i in range(len(aliases)):
                if value.lower() == aliases[i].lower():
                    dump_type = aliases[0]
                    break

        return dump_type

    def prompts(self):
        self.prompt(self.missing[0])

        if self.missing:
            return self.prompts()

        if not self.interactive:
            exit(0)

    def prompt(self, missing, again=False):
        if missing.get("Type") == "UNKNOWN":
            if not self.interactive:
                print(
                    f"'{missing.get('Original', 'UNKNOWN')}' is not a valid dump type!\n")
                if missing.get("Path"):
                    return self.delete_item(missing, self.missing)

            else:
                # Dump type
                dt = self.dump_type(
                    input(
                        f"'{missing.get('Original', 'UNKNOWN')}' is not a valid dump type!\nPlease retype a new flag: ")
                )

                print("\n")

                if dt == "UNKNOWN":
                    missing["Original"] = dt
                    return self.prompt(missing)

                missing["Type"] = dt
                missing["Command"] = self.dump_func(dt)

        if again == False and missing.get("Path") != None and not os.path.isdir(missing.get("Path") or ""):
            again = True

        if not missing.get("Path"):
            if not self.interactive:
                print(
                    f"'{missing.get('Type') if missing.get('Type') != 'UNKNOWN' else missing.get('Original')}' is missing an accommodating path!\n\n" if not again else
                    f"'{missing.get('Path')}' is an invalid path!\n\n"
                )
                return self.delete_item(missing, self.missing)

            else:
                # Dump path
                dp = self.parse_path(
                    input(
                        f"'{missing.get('Type') if missing.get('Type') != 'UNKNOWN' else missing.get('Original')}' is missing an accommodating path!\nPlease enter a path: " if not again else
                        f"'{missing.get('Path')}' is an invalid path! Please enter a new, valid path: ")
                )

                missing["Path"] = dp

                print("\n\n")

                if not os.path.isdir(dp):
                    return self.prompt(missing, again=True)

        self.delete_item(missing, self.missing)
        self.completed.append(missing)

    def dump_desc(self, value):
        if "-x" in value.lower():
            return "XML"
        elif "-t" in value.lower():
            return "TXT"
        elif "-j" in value.lower():
            return "JSON"
        elif "-p" in value.lower():
            return "Plist"

        return "UNKNOWN TYPE"

    def dump_func(self, dump_type):
        def func(x): return None

        for flag in self.flags:
            if dump_type in flag.get("Aliases", []):
                func = flag.get("Command", lambda x: None)
                break

        return func

    def delete_item(self, item, target):
        for i in range(len(target)):
            if target[i] == item:
                del target[i]
                break

    def parse_path(self, path):
        if path == ".":
            return os.getcwd()
        elif path.startswith("~/"):
            return os.path.join(os.path.expanduser("~"), path[2:])

        return path

    def _longest(self, tuples):
        highest = 0

        for _tuple in tuples:
            if len(_tuple[0]) > highest:
                highest = len(_tuple[0])

        return highest
