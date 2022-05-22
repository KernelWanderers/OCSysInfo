#!/usr/bin/env python3

if __name__ == "__main__":
    from sys import exit, version_info, version
    from src.util.missing_dep import Requirements, REQUIRED
    if version_info < (3, 8, 0):
        print("OCSysInfo requires Python 3.8, while Python " + str(
            version.partition(" ")[0]) + " was detected. Terminating... ")
        exit(1)

    # Check if there are missing dependencies
    requirements = Requirements()
    missing = requirements.test_req()

    # If there are missing dependencies,
    # list them and exit.
    if missing:
        for missed in missing:
            print(f'\033[1m\033[4m\033[91mPackage "{missed}" is not installed!\033[0m')

        try:
            requirements.install_reqs(missing)
        except KeyboardInterrupt:
            exit(0)

    # requests, clear_screen and color_text are being imported here due to
    # the program throwing an error if there are missing dependencies
    # at the initial start-up phase of the program.
    import requests
    from platform import system
    from sys import exit
    from src.cli.ui import clear as clear_screen
    from src.info import color_text, AppInfo
    from src.util.create_log import create_log

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
        print("Launching OCSysInfo...")
        logger.info("Launching OCSysInfo...", __file__)
        try:
            print("Initializing FlagParser...")
            flag_parser = FlagParser(logger)
            print("Initializing UI...")
            ui = UI(flag_parser.dm, logger, log_tmp[1] or AppInfo.root_dir)
            
            print("Done! Launching UI...")
            clear_screen()
            ui.create_ui()
        except Exception as e:
            if isinstance(e, requests.ConnectionError):
                flag_parser.offline = True
            if isinstance(e, PermissionError):
                print(color_text("Could not access the required data. "
                                    "Try running this program using elevated privileges.", "red"))
                logger.critical("Could not access the required data. Exiting OCSysInfo\n\t"
                                f"^^^^^^^^{str(e)}", __file__)
                exit(0)
            else:
                raise e
        finally:
            print(" " * 25, end="\r")
            # clearing out the "Launching OCSysInfo..." line

        logger.info("Successfully launched OCSysInfo.", __file__)
    except KeyboardInterrupt:
        logger.info("Exited successfully.", __file__)
        exit(0)
