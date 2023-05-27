import json


class LangParser:

    def __init__(self, localizations: dict, language: str="English"):
        self.localization_dict = localizations
        with open(self.localization_dict.get(language, "localization/english.json")) as localizations_json:
            self.localization: dict = json.load(localizations_json)

    def change_localization(self, language: str):
        with open(self.localization_dict.get(language, "localization/english.json")) as localizations_json:
            self.localization: dict = json.load(localizations_json)

    def parse_message(self, message_code: str, *args):
        return self.localization["localizations"].get(message_code).format(*args)
