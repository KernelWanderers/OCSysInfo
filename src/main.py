#!/usr/bin/env python3

if __name__ == "__main__":
    import sys
    from util.missing_dep import Requirements, REQUIRED

    if sys.version_info < (3, 6, 0):
        print(
            "OCSysInfo requires Python 3.6, while Python "
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

    try:
        from error.logger import Logger
        from cli.ui import UI
        from managers.devicemanager import DeviceManager
    except Exception as e:
        raise e
    else:
        try:
            logger = Logger()
            logger.info("Launching OCSysInfo...", __file__)
            dump = DeviceManager(logger)
            ui = UI(dump, logger)

            logger.info("Successfully launched OCSysInfo.", __file__)
            ui.create_ui()
        except KeyboardInterrupt:
            logger.info("Exited successfully.", __file__)
            exit(0)
