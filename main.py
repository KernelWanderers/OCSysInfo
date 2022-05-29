#!/usr/bin/env python3

if __name__ == "__main__":
    # requests, clear_screen and color_text are being imported here due to
    # the program throwing an error if there are missing dependencies
    # at the initial start-up phase of the program.
    import requests
    from platform import system
    from sys import exit
    from src.cli.ui import clear as clear_screen
    from src.info import color_text, AppInfo
    from src.util.create_log import create_log

    try:
        print("Testing internet connection...")
        requests.get("https://www.google.com")
        offline = False
        print("Machine has an available internet connection!")
    except Exception:
        offline = True
        print("No internet connection available!")

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
