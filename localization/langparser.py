import json
import inspect
import os


def split_path(path: str):
    elements = []

    # Split the path into components
    while True:
        path, tail = os.path.split(path)
        if tail:
            elements.insert(0, tail)
        else:
            if path:
                elements.insert(0, path)
            break
    return elements


class LangParser:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(LangParser, cls).__new__(cls)
        return cls._instance

    def __init__(self, localizations: dict, project_root: str, language: str = "English"):
        self.project_root = project_root
        self.language = language
        self.localization_dict = localizations

        with open(self.localization_dict.get("English")) as f:
            self.english: dict = json.load(f)

        with open(self.localization_dict.get(language, "localization/english.json")) as localizations_json:
            self.localization: dict = json.load(localizations_json)

    def get_key(self, caller_file: str, key: str):
        # function to get the key from the localization dict
        # based on the caller file

        if self.project_root[-1] != os.path.sep:
            # add a trailing slash if it's not present
            self.project_root += os.path.sep

        # remove the .py file extension from the absolute path
        caller_file = caller_file.rstrip(".py")

        # remove the project root from the absolute path
        # returns something like -> "src/cli/ui"
        if self.project_root in caller_file:
            caller_file = caller_file[len(self.project_root):]

        # src/cli/ui -> ["src", "cli", "ui"]
        key_elements = split_path(caller_file)

        subdict = self.localization["localizations"]

        for element in key_elements:
            subdict = subdict[element]

        return subdict.get(key)

    def change_localization(self, language: str):
        with open(self.localization_dict.get(language, "localization/english.json")) as localizations_json:
            self.localization: dict = json.load(localizations_json)

    def parse_message(self, message_code: str, *args):
        caller_file = inspect.currentframe().f_back.f_code.co_filename
        message_to_format = self.get_key(caller_file, message_code)

        if not message_to_format:
            message_to_format = self.english["localizations"].get(message_code, message_code)

        return message_to_format.format(*args)

    def parse_message_as(self, parse_as: str, message_code: str, *args):
        """
        parse_as: Is the caller file to emulate
        example: "src/cli/ui.py"
        or if running from "/users/username/Downloads/OCSysInfo", you can also use
         "/users/username/Downloads/OCSysInfo/src/cli/ui.py"
        """

        key = self.get_key(parse_as, message_code)
        try:
            return key.format(*args)
        except AttributeError:
            raise KeyError(f"Key {message_code} not found in {parse_as}")