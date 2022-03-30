#!/usr/bin/env python3

if __name__ == "__main__":
    # requests, clear_screen and color_text are being imported here due to
    # the program throwing an error if there are missing dependencies
    # at the initial start-up phase of the program.
    import requests
    import sys
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
                    sys.exit(0)
                if isinstance(e, PermissionError):
                    print(color_text("Could not access the required data. "
                                     "Try running this program using elevated privileges.", "red"))
                    logger.critical("Could not access the required data. Exiting OCSysInfo\n\t"
                                    f"^^^^^^^^{str(e)}", __file__)
                    sys.exit(0)
                else:
                    raise e
            finally:
                print(" " * 25, end="\r")
                # clearing out the "Launching OCSysInfo..." line

            logger.info("Successfully launched OCSysInfo.", __file__)
        except KeyboardInterrupt:
            logger.info("Exited successfully.", __file__)
            sys.exit(0)
