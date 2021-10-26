#!/usr/bin/env python3

if __name__ == "__main__":
    import sys

    if sys.version_info < (3, 6, 0):
        print('OCSysInfo requires Python 3.6, while Python ' +
              str(sys.version.partition(' ')[0] + ' was detected. Terminating. '))
        sys.exit(1)

    try:
        import dicttoxml
        import requests
        import distro

        if sys.platform.lower() == "darwin":
            import objc
        if sys.platform.lower() == "windows":
            import wmi
    except Exception:
        print("Please ensure you've installed the required dependencies.")
    else:
        try:
            from error.logger import Logger
            from cli.ui import UI
            from managers.devicemanager import DeviceManager
        except Exception as e:
            raise e
        else:
            try:
                logger = Logger()
                logger.info('Launching OCSysInfo...')
                dump = DeviceManager(logger)
                ui = UI(dump, logger)

                logger.info('Successfully launched OCSysInfo.')
                ui.create_ui()
            except KeyboardInterrupt:
                logger.info('Exited successfully.')
                exit(0)
