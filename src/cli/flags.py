import os
import sys
from sys import exit
from src.info import root_dir as root
from src.info import color_text


class FlagParser:
    def __init__(self, ui):
        self.ui = ui
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
                "Command": self.ui.dump_txt,
                "Log": {
                    "Failed": "Failed to dump to TXT file (FLAGS)",
                    "Success": "Successfully dumped to TXT file (FLAGS)",
                },
            },
            {
                "Aliases": ["--json", "-J"],
                "Command": self.ui.dump_json,
                "Log": {
                    "Failed": "Failed to dump to JSON file (FLAGS)",
                    "Success": "Successfully dumped to JSON file (FLAGS)",
                },
            },
            {
                "Aliases": ["--xml", "-X"],
                "Command": self.ui.dump_xml,
                "Log": {
                    "Failed": "Failed to dump to XML file (FLAGS)",
                    "Success": "Successfully dumped to XML file (FLAGS)",
                },
            },
            {
                "Aliases": ["--plist", "-P"],
                "Command": self.ui.dump_plist,
                "Log": {
                    "Failed": "Failed to dump to Plist file (FLAGS)",
                    "Success": "Successfully dumped to Plist file (FLAGS)",
                },
            },
        ]

        self.parse_flags(sys.argv[1:])

    def help(self):
        try:
            self.ui.clear()

            # List of possible arguments
            arguments = [
                ("[--help]", "prints this help page"),
                (
                    "[--text]",
                    "dumps hardware information into a TXT file, inside of the specified directory",
                ),
                (
                    "[--json]",
                    "dumps hardware information into a JSON file, inside of the specified directory",
                ),
                (
                    "[--xml]",
                    "dumps hardware information into an XML file, inside of the specified directory",
                ),
                (
                    "[--plist]",
                    "dumps hardware information into a plist file, inside of the specified directory",
                ),
                ("", ""),
                (
                    "[--pathT]",
                    "path to directory, where the information from the TXT dump will be stored",
                ),
                (
                    "[--pathJ]",
                    "path to directory, where the information from the JSON dump will be stored",
                ),
                (
                    "[--pathX]",
                    "path to directory, where the information from the XML dump will be stored",
                ),
                (
                    "[--pathP]",
                    "path to directory, where the information from the Plist dump will be stored",
                ),
            ]

            longest = self._longest(arguments)

            title = "OCSysInfo CLI Help Page"
            print(" " * 2 + "#" * (len(title) + 22))
            print(" " + "#" + " " * 10 + title + " " * 10 + "#")
            print("#" * (len(title) + 22), "\n" * 2)
            print(
                "<executable> \n  | [--help/-H] \n  | [--text/--txt/-tx/-T] \n  | [--json/-J] \n  | [--xml/-X] \n  | [--plist/-P]\n"
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
                "\n\nExample:\n  <executable> -T -J ~/Downloads -X --pathX ~/Documents -P"
            )
        except Exception as e:
            raise e

    def parse_flags(self, args):
        found = list(
            filter(
                lambda x: type(x.get("Argument", {})) == dict,
                self.recursively_parse(args),
            )
        )

        # In case any of the flags match
        # the ones that trigger the help page,
        # simply run the help command, and exit.
        if any(
            "-H"
            in f.get("Argument", {})
            .get("Valid", [{}])[0]
            .get("Found", {})
            .get("Aliases", [])
            for f in found
        ):
            self.help()
            exit(0)

        found = self.apff(found)
        found = self.assign_paths(found)

        executed = False

        for flag in found:
            found = flag.get("Argument", {}).get("Valid", [{}])[0].get("Found", {})
            path = flag.get("Path")

            dump_type = ""

            if not found.get("Aliases") or not found.get("Command"):
                continue

            if "--text" in found.get("Aliases"):
                dump_type = "TXT"
            elif "--json" in found.get("Aliases"):
                dump_type = "JSON"
            elif "--xml" in found.get("Aliases"):
                dump_type = "XML"
            elif "--plist" in found.get("Aliases"):
                dump_type = "Plist"

            if flag.get("Argument"):
                try:
                    ok = color_text("   OK   ", "green")

                    print(f"[{ok}]   Attempting to dump {dump_type} file to {path}...")
                    self.ui.logger.info(
                        f"Attempting to dump {dump_type} file to {path}...", __file__
                    )

                    found.get("Command")(path)
                    executed = True

                    print(
                        f"[{ok}]   Successfully dumped hardware information to {dump_type} file! Stored in {path}\n"
                    )
                    self.ui.logger.info(
                        f"Successfully dumped hardware information to {dump_type} file! Stored in {path}",
                        __file__,
                    )
                except Exception as e:
                    fail = color_text(" FAILED ", "red")
                    print(
                        f"[{fail}]   Failed to dump to {dump_type}!\n\t^^^^^^^^^{str(e)}"
                    )
                    self.ui.logger.error(
                        f"Failed to dump to {dump_type}!\n\t^^^^^^^^^^^^{str(e)}",
                        __file__,
                    )

        if executed:
            self.ui.logger.info("Successfully exited after dumping.\n\n", __file__)
            exit(0)

        self.ui.create_ui()

    def recursively_parse(self, args=[]):
        """
        Function to properly format and extract flags.
        Case #1:
            <executable> -X -T -J [path]

        We'd want to map the functions for dumping XML, TXT and JSON,
        but make sure they're all dumped to the same path.

        Case #2:
            <executable> -X [path1] -T -J [path2]

        Here, we'd want to execute the XML dump to path1,
        but TXT and JSON dumps to path2.

        Case #3:
            <executable> -X [path1] -T -J

        Here, we'd want to execute the XML dump to path1,
        but TXT and JSON dumps to the root directory of the program.

        Case #4:
            <executable> -X -T --pathX <path1> --pathT <path2>

        Here, we'd want to execute the XML dump to path1,
        but TXT dump to path2.

        Case #5:
            <executable> -X -T -J --pathX <path1> --pathT <path2>

        Here, we'd want to execute the XML dump to path1,
        but TXT dump to path2, and JSON dump to the root directory of the program.
        """

        if len(args) == 0:
            return [{}]

        if "--path" == args[0][0:6].lower():
            return [
                {"Argument": args[0], "Path Flag": True},
                *self.recursively_parse(args[2:]),
            ]

        if "-" in args[0][0]:
            flag = self.find_flag(args[0])

            if len(args) > 1:
                if "-" in args[1]:
                    return [
                        {"Argument": flag, "Path": None},
                        *self.recursively_parse(args[1:]),
                    ]
                else:
                    if args[1] == ".":
                        args[1] = os.getcwd()

                    return [
                        {"Argument": flag, "Path": args[1]},
                        *self.recursively_parse(args[2:]),
                    ]
            elif len(args) == 1:
                return [{"Argument": flag, "Path": root}]
        else:
            return [{"Argument": args[0]}, *self.recursively_parse(args[1:])]

    def assign_paths(self, values):
        # List of dictionaries with the following values:
        #
        #   Indexes — "tuple" specifying the range of elements without a path
        #   Parent  — parent path the aforementioned should have
        vals = []
        i = 0

        while i < len(values):
            if not values[i].get("Path"):
                k = i

                while True:
                    if len(values) <= k:
                        vals.append({"Indexes": [i, k - 1], "Parent": os.getcwd()})
                        i = k
                        break

                    if values[k].get("Path"):
                        vals.append(
                            {"Indexes": [i, k], "Parent": values[k].get("Path")}
                        )

                        i = k
                        break

                    k += 1
            i += 1

        for val in vals:
            begin = val.get("Indexes")[0]
            end = val.get("Indexes")[1]
            k = begin

            while k < end:
                values[k]["Path"] = val.get("Parent")

                k += 1

        return values

    # APFF – Assign Path From Flags
    def apff(self, values):
        # List of tuples:
        #    (X, Y)
        #
        #  X – Format of dump file (TXT/JSON/XML/Plist)
        #  Y – Index of its location in `values`
        dumps = []

        # List of tuples:
        #    (K, N)
        #
        #  K — Parent format this directory belongs to (TXT/JSON/XML/Plist)
        #  N — The path itself
        paths = []

        i, k = 0, 0

        while i < len(values):
            if type(values[i].get("Argument")) != dict:
                i += 1
                continue

            success_log = (
                values[i]
                .get("Argument", {})
                .get("Valid", [{}])[0]
                .get("Found", {})
                .get("Log", {})
                .get("Success", "")
            )

            if "txt" in success_log.lower():
                dumps.append(("TXT", i))
            elif "json" in success_log.lower():
                dumps.append(("JSON", i))
            elif "xml" in success_log.lower():
                dumps.append(("XML", i))
            elif "plist" in success_log.lower():
                dumps.append(("Plist", i))
            elif success_log:
                print("Uhhh. What?")
                print("You appeared to have broken our CLI, bravo.")
                exit(0)

            i += 1

        argv = sys.argv[1:]

        while k < len(argv):
            try:
                path_arg = argv[k]
            except IndexError:
                break

            if type(path_arg) != str:
                k += 1
                continue

            if "--path" in path_arg.lower():
                path = ""
                parent = ""

                # `path_arg[-1:]` retrieves the last character
                #  of the flag. Example:
                #      --pathX
                #
                #  here, it would yield `X`
                if "t" == path_arg.split("=")[0][-1:].lower():
                    parent = "TXT"
                elif "j" == path_arg.split("=")[0][-1:].lower():
                    parent = "JSON"
                elif "x" == path_arg.split("=")[0][-1:].lower():
                    parent = "XML"
                elif "p" == path_arg.split("=")[0][-1:].lower():
                    parent = "Plist"
                else:
                    print(f"\"{path_arg.split('=')[0]}\" is an invalid path flag!")
                    print('Please use the "-H" flag to see a list of valid path flags.')
                    exit(1)

                if "=" in path_arg.lower():
                    _arg = path_arg.split("=")[1]

                    path = os.getcwd() if _arg == "." else _arg
                else:
                    try:
                        path = argv[k + 1]

                        if "-" in path:
                            print(
                                f"\"{path_arg.split('=')[0]}\" flag does not contain a path. Please specify one."
                            )
                            exit(1)

                    except IndexError:
                        print(
                            f"\"{path_arg.split('=')[0]}\" flag does not contain a path. Please specify one."
                        )
                        exit(1)

                paths.append((parent, path))

            k += 1

        missing = False

        for path in paths:
            found = next((dump for dump in dumps if dump[0] == path[0]), None)

            if found:
                try:
                    # print(values[dumps[found[1]][1]])
                    values[dumps[found[1]][1]]["Path"] = (
                        path[1] if path[1] != "." else os.getcwd()
                    )
                except Exception as e:
                    raise e
            else:
                missing = True
                print(
                    f'Path for "--{path[0].lower()}" flag specified, but flag not found!'
                )

        if missing:
            exit(1)

        return values

    def find_flag(self, arg):
        data = {"Valid": [], "Invalid": []}

        found = next(
            (
                flag
                for flag in self.flags
                if arg.lower() in [x.lower() for x in flag.get("Aliases")]
            ),
            {},
        )

        data["Valid" if found else "Invalid"].append({"Original": arg, "Found": found})

        # In case some flags are invalid.
        if data.get("Invalid"):
            for invalid in data.get("Invalid"):
                original = invalid.get("Original", "")
                print(f'"{original}" is not a valid flag!')

            print('Please use the "-H" flag to bring up the help menu.')

            exit(1)

        return data

    def _longest(self, tuples):
        highest = 0

        for _tuple in tuples:
            if len(_tuple[0]) > highest:
                highest = len(_tuple[0])

        return highest
