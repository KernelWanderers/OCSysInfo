from cli.ui import UI
from dependencies.dependency_manager import install_deps
from managers.devicemanager import DeviceManager

if __name__ == "__main__":
    install_deps()

    dump = DeviceManager()
    ui = UI(dump)

    ui.create_ui()