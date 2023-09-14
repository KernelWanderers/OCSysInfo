def main():
    from sys import argv, exit, version, version_info

    from src.util.missing_dep import Requirements

    if version_info < (3, 9, 0):
        print(
            "OCSysInfo requires Python 3.9, while Python "
            + str(version.partition(" ")[0])
            + " was detected. Terminating... "
        )
        exit(1)

    reqs = Requirements()

    missing = reqs.test_req()

    if missing:
        reqs.install_reqs(missing)


    import os
    from src.util.debugger import Debugger as debugger

    args_lower = [x.lower() for x in argv]

    # Whether or not to run the application
    # in DEBUG mode.
    if (
        "-dbg" in args_lower
        or "--debug" in args_lower
        or "-debug" in args_lower
        or os.environ.get("DEBUG", "0") == "1"
    ):
        debugger.toggle(True)

        print("=" * 25 + " BEGIN OF DEBUG " + "=" * 25)

    from update.updater import OCSIUpdater

    OCSIUpdater().run()

    # Fix ANSI escape codes not being registered
    # in Windows's Command Prompt.
    #
    # Massive thank you to CorpNewt for pointing this out.
    import platform

    import requests

    from src.cli.ui import clear as clear_screen
    from src.info import (
        AppInfo,
        color_text,
        format_text,
        requests_timeout,
        useragent_header,
    )
    from src.util.create_log import create_log

    if platform.system() == "windows":
        os.system("color")

    # Preliminary check for internet availability.
    if "--offline" not in argv:
        try:
            debugger.log_dbg("--> [INTERNET]: Testing connection...")

            requests.get(
                "https://www.google.com",
                timeout=requests_timeout,
                headers=useragent_header,
            )

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
        from src.cli.flags import FlagParser
        from src.cli.ui import UI
        from src.error.logger import Logger
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
            ui = UI(flag_parser.dm, logger, log_tmp[1] or AppInfo.root_dir)
            debugger.log_dbg(
                color_text("--> [UI]: Successfully initialised!\n", "green")
            )

            debugger.log_dbg(color_text("--> [UI]: Spawning...\n", "yellow"))
            clear_screen()
            ui.create_ui()

        except Exception as e:
            if isinstance(e, KeyboardInterrupt):
                exit(0)

            if isinstance(e, PermissionError):
                print(
                    color_text(
                        "Could not access the required data. "
                        "Try running this program using elevated privileges.",
                        "red",
                    )
                )
                logger.critical(
                    "Could not access the required data. Exiting OCSysInfo\n\t"
                    f"^^^^^^^^{str(e)}",
                    __file__,
                )
                exit(0)
            else:
                raise e

        finally:
            # clearing out the "Launching OCSysInfo..." line
            print(" " * 25, end="\r")

        logger.info("Successfully launched OCSysInfo.", __file__)
    except KeyboardInterrupt:
        logger.info("Exited successfully.", __file__)
        exit(0)
