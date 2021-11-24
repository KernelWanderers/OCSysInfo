#!/usr/bin/env python3

if __name__ == "__main__":
    import sys
    from util.missing_dep import Requirements, REQUIRED
    from info import color_text

    if sys.version_info < (3, 8, 0):
        print(
            "OCSysInfo requires Python 3.8, while Python "
            + str(sys.version.partition(" ")[0] + " was detected. Terminating. ")
        )
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

    import requests
    # requests is being importing here because it will error out
    # if there are missing dependencies in the start of the program

    try:
        from error.logger import Logger
        from cli.ui import UI
        from cli.flags import FlagParser
        from managers.devicemanager import DeviceManager
    except Exception as e:
        raise e
    else:
        try:
            logger = Logger()
            logger.info("Launching OCSysInfo...", __file__)
            try:
                dump = DeviceManager(logger)
                ui = UI(dump, logger)
                flag_parser = FlagParser(ui)
            except Exception as e:

                if isinstance(e, requests.ConnectionError):
                    print(color_text("This program needs an internet connection to run. "
                                     "Please connect to the internet and restart this program.", "red"))
                    logger.info("No internet connection found. Exiting OCSysInfo", __file__)
                    exit(0)
                else:
                    raise e

            logger.info("Successfully launched OCSysInfo.", __file__)
        except KeyboardInterrupt:
            logger.info("Exited successfully.", __file__)
            exit(0)
