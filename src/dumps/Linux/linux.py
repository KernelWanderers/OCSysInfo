import asyncio
import os
import re
import subprocess

from managers.devicemanager import DeviceManager


class LinuxHardwareManager:
    """
    Instance, implementing `DeviceManager`, for extracting system information
    from Linux using the `sysfs` pseudo file system.

    https://www.kernel.org/doc/html/latest/admin-guide/sysfs-rules.html
    """

    def __init__(self, parent: DeviceManager):
        self.info = parent.info
        self.pci = parent.pci

    def dump(self):
        self.cpu_info()
        self.gpu_info()
        self.net_info()
        self.audio_info()
        self.input_info()

    def cpu_info(self):
        cpus = subprocess.getoutput('cat /proc/cpuinfo')

        cpu = cpus.split('\n\n')[0]  # Get only the first CPU identifier.

        model = re.search(r'(?<=model name\t\: ).+(?=\n)', cpu).group(0)
        flagers = re.search(r'(?<=flags\t\t\: ).+(?=\n)', cpu).group(0)
        cores = re.search(r'(?<=cpu cores\t\: ).+(?=\n)', cpu).group(0)
        # No clue, don't ask.
        threads = subprocess.getoutput('grep -c processor /proc/cpuinfo')

        # List of supported SSE instructions.
        sse = [flag.replace('_', '.') for flag in flagers.split(' ') if 'sse' in flag.lower(
        ) and not 'ssse' in flag.lower()]

        ssse3 = 'Supported' if 'ssse3' in flagers else 'Not Available'

        highest = list(sorted(sse, reverse=True))[0]

        self.info.get('CPU').append({
            model: {
                'SSE': highest.upper(),
                'SSSE3': ssse3,
                'Cores': cores + ' cores',
                'Threads': threads + ' threads'
            }
        })

    def gpu_info(self):
        for file in os.listdir('/sys/class/drm/'):

            # DRM devices (no FBDev) are enumerated with the format `cardX`
            # inside of sysfs's DRM directory. So we look for those, and traverse
            # them. We look for the `device` and `vendor` file, which should always be there.
            if 'card' in file and not '-' in file:
                path = '/sys/class/drm/{}'.format(file)

                ven = subprocess.getoutput('cat {}/device/vendor'.format(path))
                dev = subprocess.getoutput('cat {}/device/device'.format(path))

                model = (self.pci.get_item(dev[2:], ven[2:])).get('device')

                self.info.get('GPU').append({
                    model: {
                        'Device ID': dev,
                        'Vendor': ven
                    }
                })

    def net_info(self):
        for file in os.listdir('/sys/class/net'):
            path = '/sys/class/net/{}/device'.format(file)

            # We ensure that the enumerated directory in the sysfs net
            # directory is a valid card, since it'll contain a `vendor` and
            # `device` file.
            if os.path.isfile('{}/device'.format(path)):
                ven = subprocess.getoutput('cat {}/vendor'.format(path))
                dev = subprocess.getoutput('cat {}/device'.format(path))

                model = self.pci.get_item(dev[2:], ven[2:]).get('device')

                self.info.get('Network').append({
                    model: {
                        'Device ID': dev,
                        'Vendor': ven
                    }
                })

    def audio_info(self):
        for file in os.listdir('/sys/class/sound'):

            # Sound devices are enumerated similarly to DRM devices,
            # with the format `cardX`, so we look for those, and look
            # for `vendor` and `device` files.
            if "card" in file.lower() and not "-" in file.lower():
                path = '/sys/class/sound/{}/device'.format(file)

                ven = subprocess.getoutput('cat {}/vendor'.format(path))
                dev = subprocess.getoutput('cat {}/device'.format(path))

                model = self.pci.get_item(dev[2:], ven[2:]).get('device')

                self.info.get('Audio').append({
                    model: {
                        'Device ID': dev,
                        'Vendor': ven
                    }
                })

    def input_info(self):
        devices = subprocess.getoutput('cat /proc/bus/input/devices')
        sysfs = []

        for device in devices.split('\n\n'):
            if not "touchpad" in device.lower() and not "trackpad" in device.lower() and not "synaptics" in device.lower():
                continue

            for line in device.split('\n'):
                if "sysfs" in line.lower():
                    sysfs.append("/sys{}".format(line.split('=')[1]))

        for path in sysfs:
            if os.path.isfile('{}/id/vendor'.format(path)):
                ven = subprocess.getoutput('cat {}/id/vendor'.format(path))
                dev = subprocess.getoutput('cat {}/id/product'.format(path))
                print(f"Vendor: {ven}\nDevice ID: {dev}\n")
