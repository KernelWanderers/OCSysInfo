import platform

"""
TODO: Implement hardware dumps for Linux, Windows and macOS - and parse each dump accordingly.
"""
class DeviceManager:
    """Instance responsible for exposing all important information about the current system's hardware."""
    def __init__(self):
        self.info = {
            "CPU": {},
            "GPU": [],
            "Network": [],
            "Audio": {}
        }
        self.platform = platform.system().lower()