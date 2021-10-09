# from dumps.mac_dump import MacHardwareManager
from managers.tree import tree
from dumps.macOS.dump import MacHardwareManager

if __name__ == "__main__":
    dump = MacHardwareManager()

    dump.cpu_info()
    dump.gpu_info()
    dump.net_info()

    print(dump.info)