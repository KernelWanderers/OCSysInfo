import os
import shutil
import sys
from platform import system
from urllib.request import urlretrieve
from zipfile import ZipFile

import regex
import requests

from src.info import requests_timeout, useragent_header
from src.util.debugger import Debugger as debugger


class OCSIUpdater:
    def __init__(self):
        self.data = []
        self.local = []
        self.zip = "https://github.com/KernelWanderers/OCSysInfo/archive/main.zip"
        self.delim = "\\" if system().lower() == "windows" else "/"
        self.root = self.delim.join(os.path.dirname(__file__).split(self.delim)[:-1])
        self.should_update = False

    def run(self):
        try:
            requests.get(
                "https://www.google.com",
                timeout=requests_timeout,
                headers=useragent_header,
            )
        except Exception:
            return

        self.check_version()

        if not self.should_update:
            return

        self.obtain_updated()

        for path in ["main.py", "src"]:
            self.obtain_relative(path)

        self.handle_diffs()

    def check_version(self):
        file = requests.get(
            "https://raw.githubusercontent.com/KernelWanderers/OCSysInfo/main/src/info.py"
        )

        if file.ok:
            contents = file.text

            version = regex.findall(r"version = \"(.+)\"", contents)[0].replace("v", "")

            from src.info import AppInfo

            if tuple(int(x) for x in version.split(".")) > tuple(
                int(x) for x in AppInfo.version.replace("v", "").split(".")
            ):
                confirm = input("There's a new update. Would you like to update? [Y/N]")

                if confirm.lower() == "y":
                    self.should_update = True

    def handle_diffs(self):
        if not self.data or not self.local:
            debugger.log_dbg(
                "[OCSI/UPDATER]: Either failed to fetch ZIP, or there are no diffs!"
            )

            return

        debugger.log_dbg("[OCSI/UPDATER]: Handling diffs...")

        self.handle_diff(self.local, self.data)

    def handle_diff(self, parent, to_cmp):
        matched = [{"matched": False} | x for x in to_cmp]

        for value in parent:
            found = False
            abs_lcl = os.path.join(self.root, value.get("path"))

            for cmp in to_cmp:
                conditions = {
                    "contents": cmp.get("contents", "x") == value.get("contents", "y"),
                    "name": cmp.get("name", "x") == value.get("name", "y"),
                    "path": cmp.get("path", "x") == value.get("path", "y"),
                    "dir": os.path.dirname(cmp.get("path", "/x/z"))
                    == os.path.dirname(value.get("path", "/y/q")),
                }

                match_found = list(
                    filter(
                        lambda x: x.get("name", "x") == cmp.get("name", "y")
                        and x.get("path", "/x/z") == cmp.get("path", "/y/q"),
                        matched,
                    )
                )
                abs_cmp = os.path.join(self.root, cmp.get("path"))

                # File was edited
                if (
                    not conditions["contents"]
                    and conditions["name"]
                    and conditions["dir"]
                ):
                    found = True

                    if match_found:
                        match_found[0]["matched"] = True

                    try:
                        print(f"Editing {value.get('name')}...")

                        with open(abs_lcl, "w") as file:
                            file.seek(0)
                            file.write(cmp.get("contents"))
                            file.truncate()
                            file.close()

                        print(f"Successfully edited {value.get('name')}!\n")
                    except Exception as e:
                        print(
                            f"Failed to edit {value.get('name')}!\n\t^^^^^^^{str(e)}\n"
                        )

                    break

                # File was renamed
                elif (
                    conditions["contents"]
                    and not conditions["name"]
                    and conditions["dir"]
                ):
                    found = True

                    if match_found:
                        match_found["matched"] += 1

                    try:
                        print(
                            f"Attempting to rename '{os.path.basename(abs_lcl)}' to '{os.path.basename(abs_cmp)}'..."
                        )
                        debugger.log_dbg(
                            f"Attempting to rename '{os.path.basename(abs_lcl)}' to '{os.path.basename(abs_cmp)}'..."
                        )

                        os.rename(abs_lcl, abs_cmp)

                        print(
                            f"Successfully renamed '{os.path.basename(abs_lcl)}' to '{os.path.basename(abs_cmp)}'!\n"
                        )
                        debugger.log_dbg(
                            f"[OCSI/UPDATER]: Successfully renamed '{os.path.basename(abs_lcl)}' to '{os.path.basename(abs_cmp)}'!"
                        )
                    except Exception as e:
                        print(
                            f"Failed to rename '{os.path.basename(abs_lcl)}' to '{os.path.basename(abs_cmp)}'!\n\t^^^^^^^{str(e)}\n"
                        )
                        debugger.log_dbg(
                            f"[OCSI/UPDATER]: Failed to rename '{os.path.basename(abs_lcl)}' to '{os.path.basename(abs_cmp)}'!\n\t^^^^^^^{str(e)}"
                        )

                    break

                # File was moved
                elif (
                    conditions["contents"]
                    and conditions["name"]
                    and not conditions["dir"]
                ):
                    found = True

                    if match_found:
                        match_found[0]["matched"] = True

                    try:
                        print(f"Deleting {abs_lcl} and creating {abs_cmp}...")
                        debugger.log_dbg(
                            f"[OCSI/UPDATER]: Deleting '{abs_lcl}' and creating '{abs_cmp}'..."
                        )

                        os.remove(abs_lcl)

                        with open(abs_cmp, "w") as file:
                            debugger.log_dbg(
                                f"[OCSI/UPDATER]: Writing updated contents to '{abs_cmp}'..."
                            )
                            file.write(cmp.get("contents"))
                            file.close()

                        print(
                            f"Successfully deleted '{abs_lcl}' and created '{abs_cmp}'!\n"
                        )
                        debugger.log_dbg(
                            f"[OCSI/UPDATER]: Successfully deleted '{abs_lcl}' and created '{abs_cmp}'!"
                        )
                    except Exception as e:
                        print(
                            f"Failed to delete '{abs_lcl}' and create '{abs_cmp}'!\n\t^^^^^^^{str(e)}\n"
                        )
                        debugger.log_dbg(
                            f"[OCSI/UPDATER]: Failed to delete '{abs_lcl}' and create '{abs_cmp}'!\n\t^^^^^^^{str(e)}"
                        )

                    break

                # If the file stays the same,
                # do nothing.
                elif (
                    conditions["contents"] and conditions["name"] and conditions["dir"]
                ):
                    if match_found:
                        match_found[0]["matched"] = True

                    debugger.log_dbg(
                        f"[OCSI/UPDATER]: Contents of '{abs_lcl}' are the same, skipping..."
                    )

                    found = True

                    break

            # If nothing matches,
            # it means the file was removed.
            if not found:
                try:
                    print(f"Deleting {abs_lcl}...")
                    debugger.log_dbg(f"[OCSI/UPDATER]: Deleting '{abs_lcl}'...")

                    os.remove(abs_lcl)

                    print(f"Successfully deleted {abs_lcl}!\n")
                    debugger.log_dbg(
                        f"[OCSI/UPDATER]: Successfully deleted '{abs_lcl}'!"
                    )
                except Exception as e:
                    print(f"Failed to delete {abs_lcl}!\n\t^^^^^^^{str(e)}\n")

        # “Clever” way of determining
        # whether or not new files were pushed
        # to the repository.
        for match in matched:
            if not match["matched"]:
                try:
                    print(f"Creating '{match.get('name')}'...")

                    with open(os.path.join(self.root, match.get("path")), "w") as file:
                        file.write(match.get("contents"))
                        file.close()

                    print(
                        f"Successfully created '{match.get('name')}' at '{match.get('path')}'!"
                    )
                except Exception as e:
                    print(f"Failed to create '{match.get('name')}'!\n\t^^^^^^^{str(e)}")
                    continue

        os.execl(sys.executable, sys.executable, *sys.argv)

    def obtain_relative(self, path="src", o_type="local"):
        if "__pycache__" in path.lower() and os.path.isdir(
            os.path.join(self.root, path)
        ):
            return

        pp = os.path.join(self.root, path)

        if os.path.isfile(pp):
            data = {
                "name": path.split(self.delim)[-1],
                "path": pp.split(f"OCSysInfo{self.delim}")[-1].split(
                    f"OCSysInfo-main{self.delim}"
                )[-1],
                "contents": open(pp, "r").read(),
            }

            if o_type == "github":
                debugger.log_dbg(
                    f"[OCSI/UPDATER]: Adding '{data.get('path', 'unknown file')}' files as server-side diff..."
                )
                self.data.append(data)
            else:
                debugger.log_dbg(
                    f"[OCSI/UPDATER]: Adding '{data.get('path', 'unknown file')}' files as server-side diff..."
                )
                self.local.append(data)

            return

        dir = os.listdir(pp)

        for item in dir:
            abs_path = os.path.join(self.root, path, item)

            if os.path.isdir(abs_path):
                self.obtain_relative(os.path.join(path, item), o_type)
                continue
            elif ".ds_store" in item.lower() and os.path.isfile(abs_path):
                continue

            to_split = (
                f"src{self.delim}"
                if f"{self.delim}src{self.delim}" in abs_path
                else f"update{self.delim}"
            )

            data = {
                "name": item,
                "path": to_split + abs_path.split(to_split)[1],
                "contents": open(abs_path, "r").read(),
            }

            if o_type == "github":
                debugger.log_dbg(
                    f"[OCSI/UPDATER]: Adding '{data.get('path', 'unknown file')}' files as server-side diff..."
                )
                self.data.append(data)
            else:
                debugger.log_dbg(
                    f"[OCSI/UPDATER]: Adding '{data.get('path', 'unknown file')}' files as local diff..."
                )
                self.local.append(data)

    def obtain_updated(self):
        try:
            debugger.log_dbg(
                "[OCSI/UPDATER]: Checking if we need to create a temporary directory..."
            )
            update_dir = os.path.join(self.root, "UpdateTemp")

            if not os.path.isdir(update_dir):
                debugger.log_dbg("[OCSI/UPDATER]: Creating temporary directory...")
                os.mkdir(update_dir)

            path = os.path.join(update_dir, "OCSysInfo_Update.zip")

            print("Downloading ZIP file...")
            debugger.log_dbg(
                "[OCSI/UPDATER]: Attempting to download latest project in ZIP file..."
            )

            urlretrieve(self.zip, path)

            print("Successfully downloaded ZIP!\n")
            debugger.log_dbg("[OCSI/UPDATER]: Successfully downloaded archive!")
        except Exception:
            print("[CONERROR]: Unable to download ZIP, ignoring – cancelling...\n")

            self.data = []

            return -1

        with ZipFile(path, "r") as zip:
            debugger.log_dbg("[OCSI/UPDATER]: Extracting archive...")
            zip.extractall(update_dir)
            zip.close()

        name = ([x for x in os.listdir(update_dir) if "ocsysinfo" in x.lower()] + [-1])[
            0
        ]

        if name == -1:
            self.data = []
            return

        for path in ["main.py", "src"]:
            self.obtain_relative(
                path=os.path.join("UpdateTemp", name, path), o_type="github"
            )

        debugger.log_dbg("[OCSI/UPDATER]: Removing temporary directory...")

        # Remove temporary update directory
        # after we're finished.
        shutil.rmtree(os.path.join(self.root, "UpdateTemp"))
