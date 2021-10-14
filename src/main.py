from cli.ui import UI
from dependencies.dependency_manager import install_dep
from managers.tree import tree
from managers.devicemanager import DeviceManager

if __name__ == "__main__":
    install_dep()

    dump = DeviceManager()
    ui = UI(dump)

    ui.create_ui()