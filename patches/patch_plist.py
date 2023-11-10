import os
import plistlib
from pathlib import Path


from src.info import localizations, project_root
from localization.langparser import LangParser
langparser = LangParser(localizations, project_root, os.environ.get("LANGUAGE", "English"))


def patch_info_plist():
    print(langparser.parse_message("updating_info_plist"))
    plist_path = "./dist/OCSysInfo.app/Contents/Info.plist"

    print(langparser.parse_message("patching_cfbundleexecutable"))
    plist = plistlib.load(Path(plist_path).open("rb"))

    plist["CFBundleExecutable"] = "Launcher"
    print(langparser.parse_message("writing_changes"))

    plistlib.dump(plist, Path(
        plist_path).open("wb"), sort_keys=True)

    print(langparser.parse_message("successfully_patched_info_plist"))


patch_info_plist()
