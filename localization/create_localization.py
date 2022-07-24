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

from src.cli.ui import clear


def check_for_braces(string: str):
    """
    Check for braces in a string.
    """
    pattern = r"({})"
    return re.findall(pattern, string)


class Localization:
    def __init__(self):
        pass
        self.options = {
            "Add Language": self.create_language,
            "Modify Entries For Language": self.modify_language,
            "View Languages": self.view_languages,
            "Exit": self.exit_loop
        }
        self.english_path = os.path.join("localization", "english.json")
        self.localizations_path = "localization"
        with open(self.english_path, "r") as file:
            self.english = json.load(file)
        self.localizations = []
        self.load_localizations()
        self.lang_names = [x["name"] for x in self.localizations]
        self.exit = False
        while not self.exit:
            clear()
            self.print_menu()

    def print_menu(self):
        for i, entry in enumerate(self.options):
            print(f"{i + 1}: {entry}")
        choice = input("\nEnter your choice: ")

        # the choice needs to be a digit, and needs to be between 1 and the length of the options
        if not choice.isdigit():
            print("Invalid choice!")
            input("Press any key to continue...")
            return self.print_menu()
        choice = int(choice)
        if choice not in range(1, len(self.options) + 1):
            print("Invalid choice!")
            input("Press any key to continue...")
            return self.print_menu()

        # we have the choice - get the corresponding function and run it
        self.options[list(self.options.keys())[choice - 1]]()

    def create_language(self):
        pass
        clear()
        eng_keys = self.english.get("localizations")
        new_lang_entries = {}
        disclaimer = "Note: You will be asked to enter the name of the language " \
                     "as both the localized version, and the ASCII version.\nFor example:\n\t" \
                     "ASCII: Spanish\n\t" \
                     "Localized : Español"
        print(disclaimer)
        lang_name = input("Enter the name of the language (Localized): ").strip()
        if lang_name in self.lang_names:
            print("Language already exists!")
            input("Press any key to continue...")
            return
        lang_name_ascii = input("Enter the name of the language (ASCII): ").strip()
        count = 1
        total_count = len(eng_keys)
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
                    count += 1
        input("Press any key to continue...")

    def modify_language(self):
        pass

    def view_languages(self):
        lang_names = []
        for json_obj in self.localizations:
            lang_names.append(json_obj.get("name"))
        clear()
        print("Languages Currently Loaded:")
        print("\n".join(lang_names))
        input("Press any key to continue...")

    def exit_loop(self):
        self.exit = True

    def load_localizations(self):
        files = [x for x in os.listdir(self.localizations_path) if x.lower().endswith(".json")]
        format = {}
        for k, v in self.english.items():
            format[k] = type(v)
        # we make a new object for comparing the localization structure.
        # we only take it as a valid localization if it matches the english structure.

        for file in files:
            with open(os.path.join(self.localizations_path, file), "r") as f:
                valid = True
                localization_file = json.load(f)
                if type(localization_file) != dict:
                    print(f"{file} is not a valid localization file.")
                    valid = False
                    continue
                for k, v in localization_file.items():
                    if k in format:
                        if type(v) != format[k]:
                            print(f"{file} is not a valid localization file.")
                            valid = False
                            break
                # it has passed all tests
                if valid:
                    self.localizations.append(localization_file)


localization = Localization()
