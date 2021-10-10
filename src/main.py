# from dumps.mac_dump import MacHardwareManager
from managers.tree import tree
from dumps.macOS.mac import MacHardwareManager

if __name__ == "__main__":
    dump = MacHardwareManager()

    dump.cpu_info()
    dump.gpu_info()
    dump.net_info()
    dump.audio_info()

    for key in dump.info:
        tree(key, dump.info[key])
        print(" ")