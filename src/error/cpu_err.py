import os
from sys import exit

from localization.langparser import LangParser
from src.info import localizations, project_root

langparser = LangParser(localizations, project_root, os.environ.get("LANGUAGE", "English"))


def cpu_err(e):
    print(langparser.parse_message("something_went_wrong_cpu_discovery"))
    print(langparser.parse_message("this_should_not_happen"))
    print(langparser.parse_message("error_logs", str(e)))
    exit(1)
