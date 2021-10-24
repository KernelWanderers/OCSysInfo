import ctypes
import os
import re
import json
from error.cpu_err import cpu_err
from root import root
from util.codename import codename


class LinuxHardwareManager:
    """
    Instance, implementing `DeviceManager`, for extracting system information
    from Linux using the `sysfs` pseudo file system.

    https://www.kernel.org/doc/html/latest/admin-guide/sysfs-rules.html
    """

    def __init__(self, parent):
        self.info = parent.info
        self.pci = parent.pci
        self.logger = parent.logger
        self.cpu = {}

    def dump(self):
        self.cpu_info()
        self.mobo_info()
        self.gpu_info()
        self.net_info()
        self.audio_info()
        self.input_info()

    def extf(self):
        libname = os.path.join(root, 'cpp', 'bindings',
                               'cpuid', 'asm-cpuid.so')
        c_lib = ctypes.CDLL(libname)

        return (c_lib.EAX() >> 20) & 0xf

    def cpu_info(self):
        try:
            cpus = open('/proc/cpuinfo', 'r').read()
        except Exception as e:
            self.logger.critical(
                f'Failed to obtain CPU information. This should not happen. \nSnippet relevant to former line^^^\t^^^{str(e)}')
            cpu_err(e)

        cpu = cpus.split('\n\n')

        if not cpu:
            return

        cpu = cpu[0]  # Get only the first CPU identifier.

        model = re.search(r'(?<=model name\t\: ).+(?=\n)', cpu)
        flagers = re.search(r'(?<=flags\t\t\: ).+(?=\n)', cpu)
        cores = re.search(r'(?<=cpu cores\t\: ).+(?=\n)', cpu)
        _model = re.search(r'(?<=model\t\t\: ).+(?=\n)', cpu)
        fam = re.search(r'(?<=cpu\sfamily	\: ).+(?=\n)', cpu)
        stepping = re.search(r'(?<=stepping	\:).+(?=\n)', cpu)

        data = {}

        if model:
            model = model.group()
            data = {
                model: {}
            }
            self.cpu['model'] = model
        else:
            self.logger.warning(
                'Failed to obtain basic CPU information (PROC_FS)')
            exit(0)

        if flagers:
            flagers = flagers.group()

            # List of supported SSE instructions.
            data[model]['SSE'] = list(sorted([flag.replace('_', '.') for flag in flagers.split(' ') if 'sse' in flag.lower(
            ) and not 'ssse' in flag.lower()], reverse=True))[0].upper()
            data[model]['SSSE3'] = 'Supported' if 'ssse3' in flagers else 'Not Available'

        if cores:
            data[model]['Cores'] = cores.group()

        try:
            # Count the amount of times 'processor'
            # is matched, since threads are enumerated
            # individually.
            data[model]['Threads'] = open(
                '/proc/cpuinfo', 'r').read().count('processor')
        except:
            self.logger.warning(
                f'Failed to resolve thread count for {model} (PROC_FS)')
            pass

        if _model and fam:
            try:
                fam = hex(int(fam.group()))
                n = int(_model.group())
                
                if stepping:
                    stepping = hex(int(stepping.group().strip()))
                else:
                    stepping = None

                # Credits to:
                # https://github.com/1Revenger1
                extm = hex((n >> 0x4) & 0xf)
                base = hex(n & 0xf)

                extf = hex(self.extf())
                vendor = 'intel' if 'intel' in re.search(
                    r'(?<=vendor_id	\: ).+(?=\n)', cpu).group().lower() else 'amd'

                _data = json.load(
                    open(os.path.join(root, 'src',
                         'uarch', f'{vendor}.json'), 'r')
                )

                cname = codename(_data, extf,
                                 fam, extm, base, stepping=stepping)

                if cname:
                    self.cpu['codename'] = cname if len(cname) > 1 else cname[0]
            except:
                self.logger.warning(
                    f'Failed to construct extended family – ({model})')
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
                except:
                    self.logger.warning(
                        'Failed to obtain vendor/device id for GPU device (SYS_FS/DRM)')
                    continue

                # In some edge cases, we must
                # verify that the found codename
                # for Intel's CPUs corresponds to its
                # iGPU µarch.
                #
                # Otherwise, if it's not an edge-case,
                # it will simply use the guessed codename.
                if ven and dev and '8086' in ven and self.cpu.get('codename', None):

                    if any([x in n for n in self.cpu['codename']] for x in ('Kaby Lake', 'Coffee Lake', 'Comet Lake')):
                        try:
                            _data = json.load(open(os.path.join(root, 'src',
                                                                'uarch', f'intel_gpu.json'), 'r'))
                            found = False

                            for uarch in _data:
                                if found:
                                    break

                                for id in uarch.get('IDs', []):
                                    name = uarch.get('Microarch', '')

                                    if dev.lower() == id.lower():
                                        for guessed in self.cpu['codename']:
                                            if name.lower() in guessed.lower():
                                                self.cpu['codename'] = name
                                                found = True

                        except:
                            self.logger.warning(
                                f"Failed to obtain codename for {self.cpu.get('model')}")

                self.info.get('GPU').append({
                    model: {
                        'Device ID': dev,
                        'Vendor': ven
                    }
                })

        self.info['CPU'][0][self.cpu['model']
                            ]['Codename'] = self.cpu['codename']

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
                    self.logger.warning(
                        'Failed to obtain vendor/device id for Network controller (SYS_FS/NET)')
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
                    self.logger.warning(
                        'Failed to obtain vendor/device id for Audio controller (SYS_FS/SOUND)')
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
            self.logger.warning(
                'Failed to obtain Motherboard details (SYS_FS/DMI)')
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
            self.logger.critical(
                'Failed to obtain Input devices (SYS_FS/INPUT) — THIS GENERALLY SHOULD NOT HAPPEN ON LAPTOP DEVICES.')
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
                    self.logger.warning(
                        'Failed to identify device using the RMI4 protocol (SYS_FS/INPUT) – Non-critical, ignoring')
                    continue

                try:
                    prod_id = open(f'{path}/name', 'r').read().strip()
                    vendor = open(f'{path}/id/vendor', 'r').read().strip()
                except:
                    self.logger.warning(
                        'Failed to obtain product/vendor id of device using the RMI4 protocol (SYS_FS/INPUT) – Non-critical, ignoring')
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
                    self.logger.warning(
                        'Failed to identify PS2 device (SYS_FS/INPUT) – Non-critical, ignoring')
                    continue

                try:
                    name = open(f'{path}/name').read().strip()
                except:
                    self.logger.warning(
                        'Failed to obtain PS2 device name (SYS_FS/INPUT) – Non-critical, ignoring')
                    continue

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
                continue

            if os.path.isfile('{}/id/vendor'.format(path)):
                try:
                    dev = '0x' + open(f'{path}/id/product', 'r').read().strip()
                    ven = '0x' + open(f'{path}/id/vendor', 'r').read().strip()
                except:
                    self.logger.warning(
                        'Failed to obtain device/vendor id of ambiguous Input device (SYS_FS/INPUT) – Non-critical, ignoring')
                    continue

                else:
                    if ven and dev:
                        name = self.pci.get_item(dev[2:], ven[2:], types='usb')

                        if not name:
                            self.logger.warning(
                                'Failed to identify ambiguous Input device (SYS_FS/INPUT) – Non-critical, ignoring')
                            continue

                        self.info['Input'].append({
                            name.get('device', 'Unknown'): {
                                'Device ID': dev,
                                'Vendor': ven
                            }
                        })
