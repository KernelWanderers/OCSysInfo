import binascii
import dumps.macOS.ioreg as ioreg
import subprocess

from managers.devicemanager import DeviceManager


class MacHardwareManager:
    """
    Instance, implementing `DeviceManager`, for extracting system information
    from macOS using the `IOKit` framework.

    https://developer.apple.com/documentation/iokit
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
        # Full list of features for this CPU.
        features = subprocess.getoutput('sysctl machdep.cpu.features')

        data = {
            # Amount of cores for this processor.
            'Cores': subprocess.getoutput('sysctl machdep.cpu.core_count').split(': ')[1] + " cores",

            # Amount of threads for this processor.
            'Threads': subprocess.getoutput('sysctl machdep.cpu.thread_count').split(': ')[1] + " threads"
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

        # Model of the CPU
        model = subprocess.getoutput(
            'sysctl -a | grep "brand_string"').split(': ')[1]

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

            model = bytes(device.get('model')).decode()

            dev = (binascii.b2a_hex(
                bytes(reversed(device.get('device-id')))).decode()[4:])  # Reverse the byte sequence, and format it using `binascii` – remove leading 0s

            ven = (binascii.b2a_hex(
                bytes(reversed(device.get('vendor-id')))).decode()[4:])  # Reverse the byte sequence, and format it using `binascii` – remove leading 0s

            igpu = self.intel.get(dev, {})

            if igpu:
                CPU = self.info['CPU'][0][list(
                    self.info['CPU'][0].keys())[0]]

                self.info['CPU'][0] = {
                    list(self.info['CPU'][0].keys())[0]: {
                        **CPU,
                        'Codename': igpu.get('codename')
                    }
                }

            self.info['GPU'].append({
                model: {
                    'Device ID': "0x" + dev,
                    'Vendor': "0x" + ven,
                }
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

            dev = (binascii.b2a_hex(
                bytes(reversed(device.get('device-id')))).decode()[4:])  # Reverse the byte sequence, and format it using `binascii` – remove leading 0s

            ven = (binascii.b2a_hex(
                bytes(reversed(device.get('vendor-id')))).decode()[4:])  # Reverse the byte sequence, and format it using `binascii` – remove leading 0s

            model = self.pci.get_item(dev, ven)

            if model:
                model = model.get('device')

            self.info['Network'].append({
                model: {
                    'Device ID': "0x" + dev,
                    'Vendor': "0x" + ven,
                }
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

                ven = hex(device.get('IOHDACodecVendorID'))[2:6]
                dev = hex(device.get('IOHDACodecVendorID'))[6:]

                model = self.pci.get_item(dev, ven)

                if model:
                    model = model.get('device')

            else:
                dev = (binascii.b2a_hex(
                    bytes(reversed(device.get('device-id')))).decode()[4:])  # Reverse the byte sequence, and format it using `binascii` – remove leading 0s

                ven = (binascii.b2a_hex(
                    bytes(reversed(device.get('vendor-id')))).decode()[4:])  # Reverse the byte sequence, and format it using `binascii` – remove leading 0s

                model = self.pci.get_item(dev, ven).get('device')

            self.info['Audio'].append({
                model: {
                    'Device ID': "0x" + dev,
                    'Vendor': "0x" + ven,
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
            "IOProviderClass": "IOHIDDevice"
        }

        interface = ioreg.ioiterator_to_list(ioreg.IOServiceGetMatchingServices(
            ioreg.kIOMasterPortDefault, device, None)[1])

        for i in interface:

            device = ioreg.corefoundation_to_native(ioreg.IORegistryEntryCreateCFProperties(
                i, None, ioreg.kCFAllocatorDefault, ioreg.kNilOptions))[1]

            name = device.get('Product')
            hid = device.get('Transport')

            if any("{} ({})".format(name, hid) in k for k in self.info['Input']):
                continue

            ven = hex(device.get('VendorID'))
            dev = hex(device.get('ProductID'))

            name = "{} ({})".format(name, hid)

            self.info['Input'].append({
                name: {
                    'Vendor': ven,
                    'Device ID': dev
                }
            })
