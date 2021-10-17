import os
import re
from error.cpu_err import cpu_err
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
        self.intel = parent.intel

    def dump(self):
        self.cpu_info()
        self.mobo_info()
        self.gpu_info()
        self.net_info()
        self.audio_info()
        self.input_info()

    def cpu_info(self):
        try:
            cpus = open('/proc/cpuinfo', 'r').read()
        except Exception as e:
            cpu_err(e)

        cpu = cpus.split('\n\n')

        if not cpu:
            return

        cpu = cpu[0]  # Get only the first CPU identifier.

        model = re.search(r'(?<=model name\t\: ).+(?=\n)', cpu)
        flagers = re.search(r'(?<=flags\t\t\: ).+(?=\n)', cpu)
        cores = re.search(r'(?<=cpu cores\t\: ).+(?=\n)', cpu)
        # Count the amount of times 'processor'
        # is matched, since threads are enumerated
        # individually.
        data = {}

        if model:
            data = {
                model.group(0): {}
            }
        else:
            return

        if flagers:
            flagers = flagers.group(0)

            # List of supported SSE instructions.
            data[model.group(0)]['SSE'] = list(sorted([flag.replace('_', '.') for flag in flagers.split(' ') if 'sse' in flag.lower(
            ) and not 'ssse' in flag.lower()], reverse=True))[0].upper()
            data[model.group(
                0)]['SSSE3'] = 'Supported' if 'ssse3' in flagers else 'Not Available'

        if cores:
            data[model.group(0)]['Cores'] = cores.group(0)

        try:
            data[model.group(0)]['Threads'] = open(
                '/proc/cpuinfo', 'r').read().count('processor')
        except:
            pass

        self.info.get('CPU').append(data)

    def gpu_info(self):
        for file in os.listdir('/sys/class/drm/'):

            # DRM devices (not FBDev) are enumerated with the format `cardX`
            # inside of sysfs's DRM directory. So we look for those, and traverse
            # them. We look for the `device` and `vendor` file, which should always be there.
            if 'card' in file and not '-' in file:
                path = f'/sys/class/drm/{file}'

                try:
                    ven = open(f'{path}/device/vendor', 'r').read().strip()
                    dev = open(f'{path}/device/device', 'r').read().strip()

                    model = self.pci.get_item(dev[2:], ven[2:]).get('device')
                except Exception as e:
                    continue

                igpu = self.intel.get(dev.upper()[2:], {})

                if igpu:
                    CPU = self.info['CPU'][0][list(
                        self.info['CPU'][0].keys())[0]]

                    self.info['CPU'][0] = {
                        list(self.info['CPU'][0].keys())[0]: CPU | {
                            'Codename': igpu.get('codename')
                        }
                    }

                self.info.get('GPU').append({
                    model: {
                        'Device ID': dev,
                        'Vendor': ven
                    }
                })

    def net_info(self):
        for file in os.listdir('/sys/class/net'):
            path = f'/sys/class/net/{file}/device'

            # We ensure that the enumerated directory in the sysfs net
            # directory is a valid card, since it'll contain a `vendor` and
            # `device` file.
            if os.path.isfile('{}/device'.format(path)):
                try:
                    ven = open(f'{path}/vendor', 'r').read().strip()
                    dev = open(f'{path}/device', 'r').read().strip()

                    model = self.pci.get_item(dev[2:], ven[2:]).get('device')
                except:
                    return

                else:
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
            if 'card' in file.lower() and not '-' in file.lower():
                path = f'/sys/class/sound/{file}/device'

                try:
                    ven = open(f'{path}/vendor', 'r').read().strip()
                    dev = open(f'{path}/device', 'r').read().strip()

                    model = self.pci.get_item(dev[2:], ven[2:]).get('device')
                except:
                    continue

                else:
                    self.info.get('Audio').append({
                        model: {
                            'Device ID': dev,
                            'Vendor': ven
                        }
                    })

    def mobo_info(self):

        # Details about the motherboard is
        # located in /sys/devices/virtual/dmi/id
        #
        # So we simply look for `board_name` and
        # `board_vendor` to extract its model name,
        # and its vendor's name.
        try:
            path = '/sys/devices/virtual/dmi/id'

            model = open(f'{path}/board_name', 'r').read().strip()
            vendor = open(f'{path}/board_vendor', 'r').read().strip()
        except:
            return

        if model:
            data = {
                'Model': model
            }

            if vendor:
                data['Vendor'] = vendor

            self.info['Motherboard'] = data

    def input_info(self):

        # This is the simplest way of reliably
        # obtaining the path of the input devices
        # located in sysfs. Ironically, by looking
        # into procfs.
        #
        # Out of the things we look for,
        # it contains the device name, and its sysfs path.
        try:
            devices = open('/proc/bus/input/devices', 'r').read().strip()
            sysfs = []
        except:
            return

        for device in devices.split('\n\n'):
            for line in device.split('\n'):
                if 'sysfs' in line.lower():
                    sysfs.append('/sys{}'.format(line.split('=')[1]))

        for path in sysfs:
            # RMI4 devices, probably SMBus
            # TODO: I2C RMI4 devices
            if 'rmi4' in path.lower():
                # Check for passed-through devices like trackpad
                if 'fn' in path:
                    continue

                if (not os.path.isfile(f'{path}/name')) or \
                   (not os.path.isfile(f'{path}/id/vendor')):
                    continue

                try:
                    prod_id = open(f'{path}/name', 'r').read().strip()
                    vendor = open(f'{path}/id/vendor', 'r').read().strip()
                except:
                    continue

                self.info['Input'].append({
                    'Synaptics SMbus Trackpad': {
                        'Device ID': prod_id,
                        'Vendor': vendor
                    }
                })

            # PS2 devices
            if 'i8042' in path.lower():
                if not os.path.isfile(f'{path}/name'):
                    continue;

                try:
                    name = open(f'{path}/name').read().strip()
                except:
                    continue;
                
                port = re.search('\d+(?=\/input)', path)

                self.info['Input'].append({
                    name: {
                        'PS2 Port': port.group()
                    }
                })

            # Thinkpad hotkeys (HKEYs ACPI device)
            # Also includes Battery level controls, LED control, etc
            if 'thinkpad_acpi' in path.lower():
                self.info['Input'].append({
                    'Thinkpad Fn Keys': {}
                })

            # TODO: Handle I2C HID
            if not 'usb' in path.lower():
                continue;
                    
            if os.path.isfile('{}/id/vendor'.format(path)):
                try:
                    dev = '0x' + open(f'{path}/id/product', 'r').read().strip()
                    ven = '0x' + open(f'{path}/id/vendor', 'r').read().strip()
                except:
                    continue

                else:
                    if ven and dev:
                        name = self.pci.get_item(dev[2:], ven[2:], types='usb')

                        if not name:
                            continue

                        self.info['Input'].append({
                            name.get('device', 'Unknown'): {
                                'Device ID': dev,
                                'Vendor': ven
                            }
                        })
