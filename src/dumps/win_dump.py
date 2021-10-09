from managers.devicemanager import DeviceManager

class WinHardwareManager(DeviceManager):
    def __init__(self):
        self.cpu = ""

    # def get_cpu_info(self):
    #     model = 