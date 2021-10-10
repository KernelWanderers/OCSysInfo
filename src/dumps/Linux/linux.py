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
            if 'card' in file and not '-' in file:
                path = '/sys/class/drm/{}'.format(file)

                ven = subprocess.getoutput('cat {}/device/vendor'.format(path))
                dev = subprocess.getoutput('cat {}/device/device'.format(path))

                model = asyncio.run(self.pci.get_item(dev[2:], ven[2:]))

                self.info.get('GPU').append({
                    model: {
                        'Device ID': dev,
                        'Vendor': ven
                    }
                })

    def net_info(self):
        for file in os.listdir('/sys/class/net'):
            path = '/sys/class/net/{}/device'.format(file)

            if os.path.isfile('{}/device'.format(path)):
                ven = subprocess.getoutput('cat {}/vendor'.format(path))
                dev = subprocess.getoutput('cat {}/device'.format(path))

                model = asyncio.run(self.pci.get_item(dev[2:], ven[2:]))

                self.info.get('Network').append({
                    model: {
                        'Device ID': dev,
                        'Vendor': ven
                    }
                })

    def audio_info(self):
        for file in os.listdir('/sys/class/sound'):
            if "card" in file.lower() and not "-" in file.lower():
                path = '/sys/class/sound/{}/device'.format(file)

                ven = subprocess.getoutput('cat {}/vendor'.format(path))
                dev = subprocess.getoutput('cat {}/device'.format(path))

                model = asyncio.run(self.pci.get_item(dev[2:], ven[2:]))

                self.info.get('Audio').append({
                    model: {
                        'Device ID': dev,
                        'Vendor': ven
                    }
                })
