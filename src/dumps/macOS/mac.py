import asyncio
import binascii
import dumps.macOS.ioreg as ioreg
import subprocess
from managers.devicemanager import DeviceManager
from managers.pciids import PCIIDs

'''
Instance, extending `DeviceManager`, for extracting system information
from macOS using IOKit.
'''


class MacHardwareManager(DeviceManager):
    def cpu_info(self):
        # Full list of features for this CPU.
        features = subprocess.getoutput('sysctl machdep.cpu.features')

        # Highest supported SSE version.
        self.info.get('CPU')['SSE'] = sorted(list(filter(lambda f: 'sse' in f.lower(
        ) and not 'ssse' in f.lower(), features.split(': ')[1].split(' '))), reverse=True)[0]

        # Whether or not SSSE3 support is present.
        self.info.get('CPU')['SSSE3'] = 'Supported' if features.lower().find(
            'ssse3') > -1 else 'Not Available'

        # Model of the CPU
        self.info.get('CPU')['Model'] = subprocess.getoutput(
            'sysctl -a | grep "brand_string"').split(': ')[1]

    def ubi_info(self, mask: str, type: str, device='') -> None:

        if not len(device):
            device = {
                'IOProviderClass': 'IOPCIDevice',
                'IOPCIClassMatch': '0x{}000000&0xff000000'.format(mask)
            }

        # Obtain generator instance, whose values are `CFDictionary`-ies
        interface = ioreg.ioiterator_to_list(ioreg.IOServiceGetMatchingServices(
            ioreg.kIOMasterPortDefault,
            # Bit mask matching, ensuring that the 3rd byte is one of the specified controller.
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

            model = asyncio.run(PCIIDs().get_item(dev, ven))

            self.info.get(type).append({
                model: {
                    'Device ID': dev,
                    'Vendor': ven,
                }
            })

            ioreg.IOObjectRelease(i)

    def gpu_info(self):
        self.ubi_info('03', 'GPU')

    def net_info(self):
        self.ubi_info('02', 'Network')

    def audio_info(self):

        # Obtain generator instance, whose values are `CFDictionary`-ies
        interface = ioreg.ioiterator_to_list(ioreg.IOServiceGetMatchingServices(
            ioreg.kIOMasterPortDefault,
            {'IOProviderClass': 'IOHDACodecDevice'},
            None)[1])

        # Loop through the generator returned from `ioiterator_to_list()`
        for i in interface:

            # Obtain CFDictionaryRef of the current PCI device.
            device = ioreg.corefoundation_to_native(ioreg.IORegistryEntryCreateCFProperties(
                i, None, ioreg.kCFAllocatorDefault, ioreg.kNilOptions))[1]

            if device.get('DigitalAudioCapabilities'):
                continue

            ven = hex(device.get('IOHDACodecVendorID'))[2:6]
            dev = hex(device.get('IOHDACodecVendorID'))[6:]

            model = asyncio.run(PCIIDs().get_item(deviceID=dev, ven=ven))

            self.info.get('Audio').append({
                model: {
                    'Device ID': dev,
                    'Vendor': ven,
                }
            })

            ioreg.IOObjectRelease(i)

        if not self.info.get('Audio'):
            self.ubi_info('04', 'Audio')
