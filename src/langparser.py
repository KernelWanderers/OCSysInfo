import json


class LangParser:

    def __init__(self, localizations: dict, language: str="English"):
        self.language = language
        self.localization_dict = localizations

        with open(self.localization_dict.get("English")) as f:
            self.english: dict = json.load(f)

        with open(self.localization_dict.get(language, "localization/english.json")) as localizations_json:
            self.localization: dict = json.load(localizations_json)


    def change_localization(self, language: str):
        with open(self.localization_dict.get(language, "localization/english.json")) as localizations_json:
            self.localization: dict = json.load(localizations_json)

    def parse_message(self, message_code: str, *args):
        message_to_format = self.localization["localizations"].get(message_code)

        if not message_to_format:
            message_to_format = self.english["localizations"].get(message_code)

        return message_to_format.format(*args)
