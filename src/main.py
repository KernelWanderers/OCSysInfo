if __name__ == "__main__":
    from dependencies.dependency_manager import install_deps
    install_deps()

    try:
        from cli.ui import UI
        from managers.devicemanager import DeviceManager
    except:
        install_deps()

    try: 
        dump = DeviceManager()
        ui = UI(dump)

        ui.create_ui()
    except KeyboardInterrupt:
        exit(0)
