import subprocess
import binascii
import dumps.macOS.ioreg as ioreg
from managers.devicemanager import DeviceManager

class MacHardwareManager(DeviceManager):
    def cpu_info(self):
        # Full list of features for this CPU.
        features = subprocess.getoutput('sysctl machdep.cpu.features')

        # Highest supported SSE version.
        self.info.get('CPU')['SSE'] = sorted(list(filter(lambda f: "sse" in f.lower(
        ) and not "ssse" in f.lower(), features.split(': ')[1].split(' '))), reverse=True)[0]

        # Whether or not SSSE3 support is present.
        self.info.get('CPU')['SSSE3'] = "Supported" if features.lower().find(
            "ssse3") > -1 else "Not Available"

        # Model of the CPU
        self.info.get('CPU')['Model'] = subprocess.getoutput(
            'sysctl -a | grep "brand_string"').split(': ')[1]

    def gpu_info(self):
        interface = ioreg.ioiterator_to_list(ioreg.IOServiceGetMatchingServices(
            ioreg.kIOMasterPortDefault,
            {"IOProviderClass": "IOPCIDevice",
                "IOPCIClassMatch": "0x03000000&0xff000000"},
            None)[1])

        # Loop through the generator returned from `ioiterator_to_list()`
        for i in interface:
            # Obtain CFDictionaryRef of the current PCI device.
            device = ioreg.corefoundation_to_native(ioreg.IORegistryEntryCreateCFProperties(
                i, None, ioreg.kCFAllocatorDefault, ioreg.kNilOptions))[1]

            # Ensure we're accessing the device only if it exists.
            if device:
                # Check if the current device contains a `pciX,Y` in its `IOName`.
                if "IOName" in device and "display" in device['IOName']:
                    gpu = {
                        'model': ioreg.ioname_t_to_str(bytes(device.get('model'))),
                        'device': (binascii.b2a_hex(
                            bytes(reversed(device.get('device-id')))).decode()[4:]),  # Reverse the byte sequence, and format it using `binascii` – remove leading 0s
                        'vendor': (binascii.b2a_hex(
                            bytes(reversed(device.get('vendor-id')))).decode()[4:])  # Reverse the byte sequence, and format it using `binascii` – remove leading 0s
                    }

                    self.info['GPU'].append(gpu)

                ioreg.IOObjectRelease(i)

    """
    Method which @DhinakG implemented for detecting a Wireless Card:
    https://github.com/dortania/OpenCore-Legacy-Patcher/blob/main/resources/device_probe.py#L115
    """

    def net_info(self):
        interface = ioreg.ioiterator_to_list(ioreg.IOServiceGetMatchingServices(
            ioreg.kIOMasterPortDefault,
            {"IOProviderClass": "IOPCIDevice",
                "IOPCIClassMatch": "0x02000000&0xff000000"},  #
            None)[1])

        for i in interface:
            device = ioreg.corefoundation_to_native(ioreg.IORegistryEntryCreateCFProperties(
                i, None, ioreg.kCFAllocatorDefault, ioreg.kNilOptions))[1]

            if device:
                print(device)
