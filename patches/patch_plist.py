import plistlib
from pathlib import Path


def patch_info_plist():
    print("Updating Info.plist...")
    plist_path = "./dist/OCSysInfo.app/Contents/Info.plist"

    print("Patching CFBundleExecutable...")
    plist = plistlib.load(Path(plist_path).open("rb"))

    plist["CFBundleExectuable"] = "Launcher"

    print("Writing changes...")
    plistlib.dump(plist, Path(
        plist_path).open("wb"), sort_keys=True)

    print("Successfully patched Info.plist!")


patch_info_plist()
