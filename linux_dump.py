import subprocess

class LinuxHardwareManager:
    def __init__(self):
        self.info = {}

        self.get_cpu_info()

    def get_cpu_info(self):
        c = subprocess.run(['cat', '/proc/cpuinfo'], shell=True)

        print(c)

lhm = LinuxHardwareManager()