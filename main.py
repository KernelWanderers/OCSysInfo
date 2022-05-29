#!/usr/bin/env python3
if __name__ == "__main__":
    from sys import exit, version_info, version
    from src.util.missing_dep import Requirements
    if version_info < (3, 9, 0):
        print("OCSysInfo requires Python 3.9, while Python " + str(
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

    import queue
    import requests
    from threading import Thread
    from update.updater import OCSIUpdater
    from src.info import get_latest_version, format_text, AppInfo, color_text
    from sys import exit, argv
    from src.cli.ui import clear as clear_screen
    from src.util.create_log import create_log

    # Preliminary check for internet availability.
    if "--offline" not in argv:
        try:
            print("Testing internet connection...")
            requests.get("https://www.google.com")
            offline = False
            print("Machine has an available connection!")
        except Exception:
            offline = True
            print("Internet connection not available!")
    else:
        offline = True

    if not offline:
        # Get info for latest version
        que = queue.Queue()
        thread = Thread(target=lambda q: q.put(get_latest_version()), args=(que,))

        # We start the thread while the script is discovering the data
        thread.start()
        thread.join()

        # We have the latest version!
        latest_version = que.get()

        if latest_version != AppInfo.version:
            import os
            import sys

            # Formatted 'n coloured
            fnc = color_text(
                format_text(
                    f"NEW VERSION ({latest_version}) AVAILABLE!\nInstall? (y/n): ",
                    "bold+underline"
                ),
                "red"
            )
            res = input(fnc)

            if "y" in res.lower():
                update = OCSIUpdater()

                update.run()

                print("\nRunning OCSysInfo after update...")

                # Restart with the updated version
                os.execv(sys.executable, ['python'] + [sys.argv[0]])


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
            flag_parser = FlagParser(logger, None, offline=offline)

            print("Initializing UI...")
            ui = UI(flag_parser.dm, logger, log_tmp[1] or AppInfo.root_dir)
            
            print("Done! Launching UI...")
            clear_screen()
            ui.create_ui()
        except Exception as e:
            if isinstance(e, KeyboardInterrupt):
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
