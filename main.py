#!/usr/bin/env python3

if __name__ == "__main__":
    import sys
    from src.util.missing_dep import Requirements, REQUIRED
    if sys.version_info < (3, 8, 0):
        print("OCSysInfo requires Python 3.8, while Python " + str(
            sys.version.partition(" ")[0]) + " was detected. Terminating... ")
        sys.exit(1)

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
    from src.info import color_text
    from src.cli.ui import clear as clear_screen

    try:
        from src.error.logger import Logger
        from src.cli.ui import UI
        from src.cli.flags import FlagParser
    except Exception as e:
        raise e
    else:
        try:
            logger = Logger()
            print("Launching OCSysInfo...")
            logger.info("Launching OCSysInfo...", __file__)
            try:
                print("Initializing FlagParser...")
                flag_parser = FlagParser(logger)
                print("Initializing UI...")
                ui = UI(flag_parser.dm, logger)
                
                print("Done! Launching UI...")
                clear_screen()
                ui.create_ui()
            except Exception as e:
                if isinstance(e, requests.ConnectionError):
                    print(color_text("This program needs an internet connection to run. "
                                     "Please connect to the internet and restart this program.", "red"))
                    logger.critical("No internet connection found. Exiting OCSysInfo", __file__)
                    exit(0)
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
