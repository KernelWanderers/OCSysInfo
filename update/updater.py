import os
import shutil
from platform import system
from urllib.request import urlretrieve
from zipfile import ZipFile


class OCSIUpdater:
    def __init__(self):
        self.data = []
        self.local = []
        self.zip = "https://github.com/KernelWanderers/OCSysInfo/archive/main.zip"
        self.delim = "\\" if system().lower() == "windows" else "/"
        self.root = self.delim.join(
            os.path.dirname(__file__).split(self.delim)[:-1]
        )

    def run(self):
        self.obtain_updated()
        self.obtain_relative()
        self.handle_diffs()

    def handle_diffs(self):
        if not self.data or not self.local:
            return

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
                    "dir": os.path.dirname(cmp.get("path", "/x/z")) == os.path.dirname(value.get("path", "/y/q"))
                }

                match_found = list(
                    filter(
                        lambda x: x.get("name", "x") == cmp.get("name", "y") and x.get("path", "/x/z") == cmp.get("path", "/y/q"),
                        matched
                    )
                )
                abs_cmp = os.path.join(self.root, cmp.get("path"))

                # File was edited
                if (
                    not conditions["contents"] and
                    conditions["name"] and
                    conditions["path"]
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
                            f"Failed to edit {value.get('name')}!\n\t^^^^^^^{str(e)}\n")

                    break

                # File was renamed
                elif (
                    conditions["contents"] and
                    not conditions["name"] and
                    conditions["dir"]
                ):
                    found = True

                    if match_found:
                        match_found["matched"] += 1

                    try:
                        print(
                            f"Attempting to rename '{os.path.basename(abs_lcl)}' to '{os.path.basename(abs_cmp)}'...")

                        os.rename(abs_lcl, abs_cmp)

                        print(
                            f"Successfully renamed '{os.path.basename(abs_lcl)}' to '{os.path.basename(abs_cmp)}'!\n")
                    except Exception as e:
                        print(
                            f"Failed to rename '{os.path.basename(abs_lcl)}' to '{os.path.basename(abs_cmp)}'!\n\t^^^^^^^{str(e)}\n")

                    break

                # File was moved
                elif (
                    conditions["contents"] and
                    conditions["name"] and
                    not conditions["dir"]
                ):
                    found = True

                    if match_found:
                        match_found[0]["matched"] = True

                    try:
                        print(f"Deleting {abs_lcl} and creating {abs_cmp}...")

                        os.remove(abs_lcl)
                        with open(abs_cmp, "w") as file:
                            file.write(cmp.get("contents"))
                            file.close()

                        print(
                            f"Successfully deleted '{abs_lcl}' and created '{abs_cmp}'!\n")
                    except Exception as e:
                        print(
                            f"Failed to delete '{abs_lcl}' and create '{abs_cmp}'!\n\t^^^^^^^{str(e)}\n")

                    break

                # If the file stays the same,
                # do nothing.
                elif (
                    conditions["contents"] and
                    conditions["name"] and
                    conditions["dir"]
                ):
                    if match_found:
                        match_found[0]["matched"] = True

                    found = True
                    break

            # If nothing matches,
            # it means the file was removed.
            if not found:
                try:
                    print(f"Deleting {abs_lcl}...")
                    os.remove(abs_lcl)
                    print(f"Successfully deleted {abs_lcl}!\n")
                except Exception as e:
                    print(f"Failed to delete {abs_lcl}!\n\t^^^^^^^{str(e)}\n")

        # “Clever” way of determining
        # whether or not new files were pushed
        # to the repository.
        for match in matched:
            if not match["matched"]:
                try:
                    print(f"Creating '{match.get('name')}'...")

                    with open(os.path.join(self.root, match.get('path')), 'w') as file:
                        file.write(match.get('contents'))
                        file.close()

                    print(f"Successfully created '{match.get('name')}' at '{match.get('path')}'!")
                except Exception as e:
                    print(
                        f"Failed to create '{match.get('name')}'!\n\t^^^^^^^{str(e)}")
                    continue

    def obtain_relative(self, path="src", o_type="local"):
        if (
            "__pycache__" in path.lower() and
            os.path.isdir(os.path.join(self.root, path))
        ):
            return

        dir = os.listdir(
            os.path.join(
                self.root,
                path
            )
        )

        for item in dir:
            abs_path = os.path.join(
                self.root,
                path,
                item
            )

            if os.path.isdir(abs_path):
                self.obtain_relative(os.path.join(path, item), o_type)
                continue
            elif (
                ".ds_store" in item.lower() and
                os.path.isfile(abs_path)
            ):
                continue

            data = {
                "name": item,
                "path": f"src{self.delim}" + abs_path.split(f"src{self.delim}")[1],
                "contents": open(abs_path, "r").read()
            }

            if o_type == "github":
                self.data.append(data)
            else:
                self.local.append(data)

    def obtain_updated(self):
        try:
            update_dir = os.path.join(
                self.root,
                "UpdateTemp"
            )

            if not os.path.isdir(update_dir):
                os.mkdir(update_dir)

            path = os.path.join(
                update_dir,
                "OCSysInfo_Update.zip"
            )

            print("Downloading ZIP file...")
            urlretrieve(
                self.zip,
                path
            )
            print("Successfully downloaded ZIP!\n")
        except Exception:
            print("[CONERROR]: Unable to download ZIP, ignoring – cancelling...\n")
            self.data = []
            return -1

        with ZipFile(path, "r") as zip:
            zip.extractall(update_dir)
            zip.close()

        name = ([x for x in os.listdir(update_dir)
                if "ocsysinfo" in x.lower()] + [-1])[0]

        if name == -1:
            self.data = []
            return

        self.obtain_relative(
            path=os.path.join(
                "UpdateTemp",
                name,
                "src"
            ),
            o_type="github"
        )

        shutil.rmtree(
            os.path.join(
                self.root,
                "UpdateTemp"
            )
        )
