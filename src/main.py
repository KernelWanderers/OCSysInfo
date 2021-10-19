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
    except:
        print("Please ensure you've installed the required dependencies.")
    else:
        try:
            from cli.ui import UI
            from managers.devicemanager import DeviceManager
        except Exception as e:
            raise e
        else:
            try:
                dump = DeviceManager()
                ui = UI(dump)

                ui.create_ui()
            except KeyboardInterrupt:
                exit(0)
