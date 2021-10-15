if __name__ == "__main__":
    from dependencies.dependency_manager import install_deps
    install_deps()

    from cli.ui import UI
    from managers.devicemanager import DeviceManager
    dump = DeviceManager()
    ui = UI(dump)

    ui.create_ui()
