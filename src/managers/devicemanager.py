import platform

from managers.pciids import PCIIDs

class DeviceManager:
    """Instance responsible for exposing all important information about the current system's hardware."""
    def __init__(self):
        self.info = {
            "CPU": [],
            "GPU": [],
            "Network": [],
            "Audio": []
        }
        self.pci = PCIIDs()
        self.platform = platform.system().lower()

        if self.platform == "darwin":
            from dumps.macOS.mac import MacHardwareManager
            self.manager = MacHardwareManager(self)
        elif self.platform == "linux":
            from dumps.Linux.linux import LinuxHardwareManager
            self.manager = LinuxHardwareManager(self)

        self.manager.dump()