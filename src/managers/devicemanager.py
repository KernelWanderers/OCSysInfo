import platform
from src.managers.pciids import PCIIDs


class DeviceManager:
    """Instance responsible for exposing all important information about the current system's hardware."""

    def __init__(self, logger):
        self.info = {
            "CPU": [],
            "Motherboard": {},
            "GPU": [],
            "Memory": [],
            "Network": [],
            "Audio": [],
            "Input": [],
            "Storage": [],
        }
        self.pci = PCIIDs()
        self.platform = platform.system().lower()
        self.logger = logger

        if self.platform == "darwin":
            from src.dumps.macOS.mac import MacHardwareManager

            self.manager = MacHardwareManager(self)
        elif self.platform == "linux":
            from src.dumps.Linux.linux import LinuxHardwareManager

            self.manager = LinuxHardwareManager(self)
        elif self.platform == "windows":
            from src.dumps.Windows.win import WindowsHardwareManager

            self.manager = WindowsHardwareManager(self)

        self.manager.dump()
