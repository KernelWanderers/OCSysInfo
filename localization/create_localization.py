# WIP: This script will assist contributors in adding support for a language in OCSysInfo.

"""
- Read english json file and take it as the base format.
- ask a name for the language, both ascii and non-ascii (if applicable)
- loop through each key in the english json file and ask the user to translate it.
- provide the key name, and the value for reference
- check for {} count and if it is not equal, ask the user to fix it.
"""

import json
import re
import os
from platform import system
import sys


def clear():
    # copied from src.cli.ui to avoid importing the module, as it has external dependencies we don't need in this case.
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


def check_for_braces(string: str):
    """
    Check for braces in a string.
    """
    pattern = r"({})"
    return re.findall(pattern, string)


class Localization:
    def __init__(self):
        self.english_path = os.path.join("localization", "english.json")
        self.localizations_path = "localization"
        with open(self.english_path, "r") as file:
            self.english = json.load(file)
        self.create_language()

    def create_language(self):
        clear()
        eng_keys = self.english.get("localizations")
        new_lang = {
            "name": "",
            "localizations": {}
        }

        disclaimer = "Note: You will be asked to enter the name of the language " \
                     "as both the localized version, and the ASCII version.\nFor example:\n\t" \
                     "ASCII: Spanish\n\t" \
                     "Localized : Español"
        print(disclaimer)
        lang_name = input("Enter the name of the language (Localized): ").strip()
        new_lang["name"] = lang_name
        lang_name_ascii = input("Enter the name of the language (ASCII): ").strip()
        if lang_name_ascii.lower() == "english":
            print("the English localization is the default and cannot be altered. Exiting...")
            return

        count = 1
        total_count = len(eng_keys)
        if os.path.exists(os.path.join(self.localizations_path, lang_name_ascii + ".json")):
            overwrite_choice = input("Language already exists! Overwrite? (y/n): ")
            if overwrite_choice.lower() == "y":
                os.remove(os.path.join(self.localizations_path, lang_name_ascii + ".json"))
            else:
                return

        for key in eng_keys:
            braces_count = len(check_for_braces(eng_keys[key]))
            success = False
            while not success:
                clear()
                print(f"Entry {count}/{total_count}")
                print(f"Translation for key: {key}")
                print(f"Placeholders (curly braces) : {braces_count}")
                print()
                print(f"Text: {eng_keys[key]}")
                translation = input("Enter translation: ").strip()
                if not len(check_for_braces(translation)) == braces_count:
                    print("Placeholder count does not match! Please type the translation again.")
                    input("\nPress any key to continue...")
                else:
                    success = True
                    new_lang["localizations"][key] = translation
                    with open(os.path.join(self.localizations_path, lang_name_ascii + ".json"), "w") as out_file:
                        json.dump(new_lang, out_file, indent=4)
                    count += 1
        out_file.close()
        input("Done! Press any key to continue...")


localization = Localization()
