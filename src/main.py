# from dumps.mac_dump import MacHardwareManager
from managers.tree import tree
from managers.devicemanager import DeviceManager
# from dumps.macOS.mac import MacHardwareManager

if __name__ == "__main__":
    dump = DeviceManager()

    for key in dump.info:
        tree(key, dump.info[key])
        print(" ")