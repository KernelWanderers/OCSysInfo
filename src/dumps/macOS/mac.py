import binascii
import dumps.macOS.ioreg as ioreg
import subprocess
from managers.devicemanager import DeviceManager
from error.cpu_err import cpu_err


class MacHardwareManager:
    """
    Instance, implementing `DeviceManager`, for extracting system information
    from macOS using the `IOKit` framework.

    https://developer.apple.com/documentation/iokit
    """

    def __init__(self, parent: DeviceManager):
        self.info = parent.info
        self.pci = parent.pci
        self.intel = parent.intel

    def dump(self):
        self.cpu_info()
        self.gpu_info()
        self.net_info()
        self.audio_info()
        self.input_info()

    def cpu_info(self):
        try:
            # Model of the CPU
            model = subprocess.check_output([
                'sysctl', 'machdep.cpu.brand_string'], shell=False).decode().split(': ')[1].strip()
        except Exception as e:
            cpu_err(e)
        try:
            # Full list of features for this CPU.
            features = subprocess.check_output([
                'sysctl', 'machdep.cpu.features']).decode().strip()
        except:
            features = None

        data = {
            # Highest supported SSE version.
            'SSE': '',

            # SSSE3 instruction availability
            'SSSE3': '',

            # Amount of cores for this processor.
            'Cores': subprocess.check_output(['sysctl', 'machdep.cpu.core_count']).decode().split(': ')[1].strip() + ' cores',

            # Amount of threads for this processor.
            'Threads': subprocess.check_output(['sysctl', 'machdep.cpu.thread_count']).decode().split(': ')[1].strip() + ' threads'
        }

        # This will fail if the CPU is _not_
        # of an x86-like architecture, which
        # traditionally uses the CPUID instruction.
        #
        # See: https://en.wikipedia.org/wiki/CPUID
        if features:
            # Highest supported SSE version.
            data['SSE'] = sorted(list(filter(lambda f: 'sse' in f.lower(
            ) and not 'ssse' in f.lower(), features.split(': ')[1].split(' '))), reverse=True)[0]

            # Whether or not SSSE3 support is present.
            data['SSSE3'] = 'Supported' if features.lower().find(
                'ssse3') > -1 else 'Not Available'

        self.info['CPU'].append({
            model: data
        })

    def gpu_info(self):

        device = {
            'IOProviderClass': 'IOPCIDevice',
            # Bit mask matching, ensuring that the 3rd byte is one of the display controller (0x03).
            'IOPCIClassMatch': '0x03000000&0xff000000'
        }

        # Obtain generator instance, whose values are `CFDictionary`-ies
        interface = ioreg.ioiterator_to_list(ioreg.IOServiceGetMatchingServices(
            ioreg.kIOMasterPortDefault,
            device,
            None)[1])

        # Loop through the generator returned from `ioiterator_to_list()`
        for i in interface:

            # Obtain CFDictionaryRef of the current PCI device.
            device = ioreg.corefoundation_to_native(ioreg.IORegistryEntryCreateCFProperties(
                i, None, ioreg.kCFAllocatorDefault, ioreg.kNilOptions))[1]

            try:
                model = bytes(device.get('model')).decode()
                model = model[0:len(model) - 1]
            except:
                continue

            try:
                dev = '0x' + (binascii.b2a_hex(
                    bytes(reversed(device.get('device-id')))).decode()[4:])
                ven = '0x' + (binascii.b2a_hex(
                    bytes(reversed(device.get('vendor-id')))).decode()[4:])

                data = {
                    # Reverse the byte sequence, and format it using `binascii` – remove leading 0s
                    'Device ID': dev,

                    # Reverse the byte sequence, and format it using `binascii` – remove leading 0s
                    'Vendor': ven
                }
            except:
                data = {}

            try:
                igpu = self.intel.get(dev.upper()[2:], {})

                if igpu:
                    CPU = self.info['CPU'][0][list(
                        self.info['CPU'][0].keys())[0]]

                    self.info['CPU'][0] = {
                        list(self.info['CPU'][0].keys())[0]: CPU | {
                            'Codename': igpu.get('codename')
                        }
                    }
            except:
                pass

            self.info['GPU'].append({
                model: data
            })

            ioreg.IOObjectRelease(i)

    def net_info(self):

        device = {
            'IOProviderClass': 'IOPCIDevice',
            # Bit mask matching, ensuring that the 3rd byte is one of the network controller (0x02).
            'IOPCIClassMatch': '0x02000000&0xff000000'
        }

        # Obtain generator instance, whose values are `CFDictionary`-ies
        interface = ioreg.ioiterator_to_list(ioreg.IOServiceGetMatchingServices(
            ioreg.kIOMasterPortDefault,
            device,
            None)[1])

        # Loop through the generator returned from `ioiterator_to_list()`
        for i in interface:

            # Obtain CFDictionaryRef of the current PCI device.
            device = ioreg.corefoundation_to_native(ioreg.IORegistryEntryCreateCFProperties(
                i, None, ioreg.kCFAllocatorDefault, ioreg.kNilOptions))[1]

            try:
                dev = '0x' + (binascii.b2a_hex(
                    bytes(reversed(device.get('device-id')))).decode()[4:])
                ven = '0x' + (binascii.b2a_hex(
                    bytes(reversed(device.get('vendor-id')))).decode()[4:])

                data = {
                    # Reverse the byte sequence, and format it using `binascii` – remove leading 0s
                    'Device ID': dev,

                    # Reverse the byte sequence, and format it using `binascii` – remove leading 0s
                    'Vendor': ven
                }
            except:
                continue

            model = self.pci.get_item(dev[2:], ven[2:])

            if model:
                model = model.get('device')

                self.info['Network'].append({
                    model: data
                })

            ioreg.IOObjectRelease(i)

    def audio_info(self, default=False):

        if default:
            _device = {
                'IOProviderClass': 'IOPCIDevice',
                # Bit mask matching, ensuring that the 3rd byte is one of the multimedia controller (0x04).
                'IOPCIClassMatch': '0x04000000&0xff000000'
            }
        else:
            _device = {'IOProviderClass': 'IOHDACodecDevice'}

        # Obtain generator instance, whose values are `CFDictionary`-ies
        interface = ioreg.ioiterator_to_list(ioreg.IOServiceGetMatchingServices(
            ioreg.kIOMasterPortDefault,
            _device,
            None)[1])

        # Loop through the generator returned from `ioiterator_to_list()`
        for i in interface:

            # Obtain CFDictionaryRef of the current PCI device.
            device = ioreg.corefoundation_to_native(ioreg.IORegistryEntryCreateCFProperties(
                i, None, ioreg.kCFAllocatorDefault, ioreg.kNilOptions))[1]

            if default == False:
                # Ensure it's the AppleHDACodec device
                if device.get('DigitalAudioCapabilities'):
                    continue

                try:
                    dev = hex(device.get('IOHDACodecVendorID'))[6:]
                    ven = hex(device.get('IOHDACodecVendorID'))[2:6]
                except:
                    continue

                model = self.pci.get_item(dev, ven)

                if model:
                    model = model.get('device')

            else:
                try:
                    dev = '0x' + (binascii.b2a_hex(
                        bytes(reversed(device.get('device-id')))).decode()[4:])  # Reverse the byte sequence, and format it using `binascii` – remove leading 0s

                    ven = '0x' + (binascii.b2a_hex(
                        bytes(reversed(device.get('vendor-id')))).decode()[4:])  # Reverse the byte sequence, and format it using `binascii` – remove leading 0s
                except:
                    continue

                model = self.pci.get_item(dev[2:], ven[2:]).get('device', '')

                if not model:
                    continue

            self.info['Audio'].append({
                model: {
                    'Device ID': dev,
                    'Vendor': ven,
                }
            })

            ioreg.IOObjectRelease(i)

        # If we don't find any AppleHDACodec devices (i.e. if it's a T2 Mac, try to find any multimedia controllers.)
        # This _will_ also fail on non-x86* architectures.
        #
        # See: https://en.wikipedia.org/wiki/Intel_High_Definition_Audio#Host_controller
        if not self.info['Audio'] and not default:
            self.audio_info(default=True)

    def input_info(self):
        if not self.info.get('Input'):
            self.info['Input'] = []

        device = {
            'IOProviderClass': 'IOHIDDevice'
        }

        interface = ioreg.ioiterator_to_list(ioreg.IOServiceGetMatchingServices(
            ioreg.kIOMasterPortDefault, device, None)[1])

        for i in interface:

            device = ioreg.corefoundation_to_native(ioreg.IORegistryEntryCreateCFProperties(
                i, None, ioreg.kCFAllocatorDefault, ioreg.kNilOptions))[1]

            name = device.get('Product', '')
            hid = device.get('Transport', '')

            if not name:
                continue

            if hid:
                hid = "(" + hid + ")"

            if any('{} {}'.format(name, hid) in k for k in self.info['Input']):
                continue

            try:
                dev = hex(device.get('ProductID'))
                ven = hex(device.get('VendorID'))

                data = {
                    'Device ID': dev,
                    'Vendor': ven
                }
            except:
                data = {}

            name = '{} {}'.format(name,  hid)

            self.info['Input'].append({
                name: data
            })
