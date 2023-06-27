#!/usr/bin/env python3

if __name__ == "__main__":
    import json
    import os

    from sys import exit, version_info, version, argv
    from localization.langparser import LangParser

    # we define the langparser here.
    # check the `localizations` folder
    # and src/langparser.py for more info
    langparser = LangParser({"English": "localization/english.json"}, os.getcwd(), "English")
    # TODO: check if there's a better way to get project root than os.getcwd()

    if version_info < (3, 9, 0):
        message = langparser.parse_message("python_requirement", "3.9", str(version.partition(" ")[0]))
        print(message)
        exit(1)

    import requests
    import os
    from src.info import AppInfo, color_text, requests_timeout, useragent_header, localizations
    from src.cli.ui import clear as clear_screen
    from src.util.create_log import create_log
    from src.util.debugger import Debugger as debugger

    # we define the localization again, with all languages included this time.
    # this is done because we cannot import the `info` module before this point.
    # `info.py` has information on the available localizations
    language = "English"
    with open(localizations.get(language, "localization/english.json")) as localizations_json:
        localization = json.load(localizations_json)

    args_lower = [x.lower() for x in argv]

    # Whether or not to run the application
    # in DEBUG mode.
    if (
        "-dbg" in args_lower or
        "--debug" in args_lower or
        "-debug" in args_lower or
        os.environ.get("DEBUG", "0") == "1"
    ):
        debugger.toggle(True)

        print("=" * 25 + " BEGIN OF DEBUG " + "=" * 25)

    # Fix ANSI escape codes not being registered
    # in Windows's Command Prompt.
    #
    # Massive thank you to CorpNewt for pointing this out.
    import os
    import platform

    if platform.system() == "windows":
        os.system("color")

    # Preliminary check for internet availability.
    if "--offline" not in argv:
        try:
            debugger.log_dbg("--> [INTERNET]: Testing connection...")
            requests.get("https://www.google.com", timeout=requests_timeout, headers=useragent_header)

            offline = False

            debugger.log_dbg("--> [INTERNET]: Available!\n")
        except Exception:
            offline = True
            debugger.log_dbg("--> [INTERNET]: Not available!\n")
    else:
        offline = True

    # Hopefully fix path-related issues in app bundles.
    log_tmp = create_log(True)

    AppInfo.root_dir = log_tmp[1] or AppInfo.sanitise_dir(__file__)
    
    try:
        from src.error.logger import Logger
        from src.cli.ui import UI
        from src.cli.flags import FlagParser
    except Exception as e:
        raise e

    try:
        logger = Logger(log_tmp[0] or AppInfo.root_dir)

        debugger.log_dbg(color_text("--> [OCSysInfo]: Launching...", "yellow"))

        logger.info("Launching OCSysInfo...", __file__)
        
        try:
            debugger.log_dbg(color_text("--> [FlagParser]: Initialising...", "yellow"))
            flag_parser = FlagParser(logger, None, offline=offline)
            debugger.log_dbg(color_text("--> [FlagParser]: Success!\n", "green"))

            debugger.log_dbg(color_text("--> [UI]: Initialising...", "yellow"))
            ui = UI(flag_parser.dm, localizations, language, logger, log_tmp[1] or AppInfo.root_dir)
            debugger.log_dbg(color_text("--> [UI]: Successfully initialised!\n", "green"))

            debugger.log_dbg(color_text("--> [UI]: Spawning...\n", "yellow"))
            clear_screen()
            ui.create_ui()

        except Exception as e:
            if isinstance(e, KeyboardInterrupt):
                exit(0)

            if isinstance(e, PermissionError):
                print(color_text(langparser.parse_message("could_not_access_data"), "red"))
                logger.critical("Could not access the required data. Exiting OCSysInfo\n\t"
                                f"^^^^^^^^{str(e)}", __file__)
                exit(0)
            else:
                raise e
                
        finally:
            # clearing out the "Launching OCSysInfo..." line
            print(" " * 25, end="\r")

        logger.info("Successfully launched OCSysInfo.", __file__)
    except KeyboardInterrupt:
        try:
            logger.info("Exited successfully.", __file__)
        except:
            pass
        exit(0)
