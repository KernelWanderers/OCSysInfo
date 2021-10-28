import binascii
import json
import os
import dumps.macOS.ioreg as ioreg
import subprocess
from error.cpu_err import cpu_err
from util.codename import codename, gpu
from util.pci_root import pci_from_acpi_osx
from root import root


class MacHardwareManager:
    """
    Instance, implementing `DeviceManager`, for extracting system information
    from macOS using the `IOKit` framework.

    https://developer.apple.com/documentation/iokit
    """

    def __init__(self, parent):
        self.info = parent.info
        self.pci = parent.pci
        self.logger = parent.logger
        self.cpu = {}

        self.STORAGE = {
            'Solid State': 'Solid State Drive (SSD)',
            'Rotational': 'Hard Disk Drive (HDD)',
        }

    def dump(self):
        self.cpu_info()
        self.gpu_info()
        self.net_info()
        self.audio_info()
        self.storage_info()
        self.input_info()

    def cpu_info(self):
        try:
            # Model of the CPU
            model = subprocess.check_output([  # dont forget to fix.
                'sysctl', 'machdep.cpu.brand_string']).decode().split(': ')[1].strip()

            self.cpu['model'] = model
        except Exception as e:
            self.logger.critical(
                f'Failed to obtain CPU information. This should not happen. \nSnippet relevant to former line^^^\t^^^{str(e)}')
            cpu_err(e)

        try:
            # Manufacturer/Vendor of this CPU;
            # Used for determining which JSON to use.
            vendor = 'intel' if 'intel' in subprocess.check_output([
                'sysctl', 'machdep.cpu.vendor'
            ]).decode().split(': ')[1].strip().lower() else 'amd'

            # Full list of features for this CPU.
            features = subprocess.check_output([
                'sysctl', 'machdep.cpu.features']).decode().strip()
        except Exception:
            self.logger.warning(
                f'Failed to access CPUID instruction – ({model})')
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

        try:
            try:
                stepping = hex(int(subprocess.check_output(
                    ['sysctl', 'machdep.cpu.stepping']
                ).decode().split(': ')[1].strip()))
            except Exception:
                stepping = None

            extf = hex(int(subprocess.check_output(
                ['sysctl', 'machdep.cpu.extfamily']
            ).decode().split(': ')[1].strip()))

            fam = hex(int(subprocess.check_output(
                ['sysctl', 'machdep.cpu.family']
            ).decode().split(': ')[1].strip()))

            n = int(subprocess.check_output(
                ['sysctl', 'machdep.cpu.model']
            ).decode().split(': ')[1].strip())

            laptop = 'book' in subprocess.check_output(
                ['sysctl', 'hw.model']
            ).decode().lower()

            # Credits to:
            # https://github.com/1Revenger1
            extm = hex((n >> 4) & 0xf)
            base = hex(n & 0xf)

            _data = json.load(
                open(os.path.join(root, 'src',
                                  'uarch', 'cpu', f'{vendor}.json'), 'r')
            )

            cname = codename(_data, extf,
                             fam, extm, base, stepping=stepping, laptop=laptop)

            if cname:
                self.cpu['codename'] = cname if len(cname) > 1 else cname[0]
        except Exception:
            self.logger.warning(
                f'Failed to construct extended family – ({model})')
            pass

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

    def gpu_info(self, default=False):

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
            except Exception:
                self.logger.warning(
                    'Failed to obtain GPU device model (IOKit)')
                continue

            try:
                # Reverse the byte sequence, and format it using `binascii` – remove leading 0s
                dev = '0x' + (binascii.b2a_hex(
                    bytes(reversed(device.get('device-id')))).decode()[4:])
                # Reverse the byte sequence, and format it using `binascii` – remove leading 0s
                ven = '0x' + (binascii.b2a_hex(
                    bytes(reversed(device.get('vendor-id')))).decode()[4:])

                path = pci_from_acpi_osx(device.get('acpi-path', ''))

                data = {
                    'Device ID': dev,
                    'Vendor': ven
                }

                pcip = path.get('PCI Path', '')
                acpi = path.get('ACPI Path', '')

                if pcip:
                    data['PCI Path'] = pcip

                if acpi:
                    data['ACPI Path'] = acpi
            except Exception:
                self.logger.warning(
                    'Failed to obtain vendor/device id for GPU device (IOKit)')
                data = {}

            gpucname = gpu(dev, ven)

            if gpucname:
                data['Codename'] = gpucname

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
                                                            'uarch', 'gpu', f'intel_gpu.json'), 'r'))
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

                    except Exception:
                        self.logger.warning(
                            f"Failed to obtain codename for {self.cpu.get('model')}")

            self.info['GPU'].append({
                model: data
            })

            ioreg.IOObjectRelease(i)

        if self.cpu.get('codename', None):
            self.info['CPU'][0][self.cpu['model']
                                ]['Codename'] = self.cpu['codename']

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

                path = pci_from_acpi_osx(device.get('acpi-path', ''))

                data = {
                    # Reverse the byte sequence, and format it using `binascii` – remove leading 0s
                    'Device ID': dev,

                    # Reverse the byte sequence, and format it using `binascii` – remove leading 0s
                    'Vendor': ven
                }

                pcip = path.get('PCI Path', '')
                acpi = path.get('ACPI Path', '')

                if pcip:
                    data['PCI Path'] = pcip

                if acpi:
                    data['ACPI Path'] = acpi
            except Exception:
                self.logger.warning(
                    'Failed to obtain vendor/device id for Network controller (IOKit)')
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

            data = {}

            if default == False:
                # Ensure it's the AppleHDACodec device
                if device.get('DigitalAudioCapabilities'):
                    continue

                try:
                    dev = '0x' + hex(device.get('IOHDACodecVendorID'))[6:]
                    ven = '0x' + hex(device.get('IOHDACodecVendorID'))[2:6]

                    data = {
                        'Device ID': dev,
                        'Vendor': ven
                    }
                except Exception as e:
                    self.logger.warning(
                        'Failed to obtain vendor/device id of HDA codec device (IOKit)\n' +
                        f'\t^^^^^^^^^{str(e)}')
                    continue

                model = self.pci.get_item(dev[2:], ven[2:])

                if model:
                    model = model.get('device')
                else:
                    model = 'N/A'

            else:
                try:
                    # Reverse the byte sequence, and format it using `binascii` – remove leading 0s
                    dev = '0x' + (binascii.b2a_hex(
                        bytes(reversed(device.get('device-id')))).decode()[4:])

                    # Reverse the byte sequence, and format it using `binascii` – remove leading 0s
                    ven = '0x' + (binascii.b2a_hex(
                        bytes(reversed(device.get('vendor-id')))).decode()[4:])

                    data = {
                        'Device ID': dev,
                        'Vendor': ven
                    }
                except Exception as e:
                    self.logger.warning(
                        'Failed to obtain vendor/device id of HDA codec device (IOKit)\n' +
                        f'\t^^^^^^^^^{str(e)}')
                    continue

                model = self.pci.get_item(dev[2:], ven[2:]).get('device', '')

                if not model:
                    model = 'N/A'

            path = pci_from_acpi_osx(device.get('acpi-path', ''))

            pcip = path.get('PCI Path', '')
            acpi = path.get('ACPI Path', '')

            if pcip:
                data['PCI Path'] = pcip

            if acpi:
                data['ACPI Path'] = acpi

            self.info['Audio'].append({
                model: data
            })

            ioreg.IOObjectRelease(i)

        # If we don't find any AppleHDACodec devices (i.e. if it's a T2 Mac, try to find any multimedia controllers.)
        # This _will_ also fail on non-x86* architectures.
        #
        # See: https://en.wikipedia.org/wiki/Intel_High_Definition_Audio#Host_controller
        if not default:
            self.audio_info(default=True)

    def storage_info(self):

        device = {
            'IOProviderClass': 'IOBlockStorageDevice'
        }

        interface = ioreg.ioiterator_to_list(ioreg.IOServiceGetMatchingServices(
            ioreg.kIOMasterPortDefault, device, None
        )[1])

        for i in interface:

            device = ioreg.corefoundation_to_native(ioreg.IORegistryEntryCreateCFProperties(
                i, None, ioreg.kCFAllocatorDefault, ioreg.kNilOptions
            ))[1]

            product = device.get('Device Characteristics')
            protocol = device.get('Protocol Characteristics')

            if not product or not protocol:
                continue

            try:
                # Name of the storage device.
                name = product.get('Product Name').strip()
                # Type of storage device (SSD, HDD, etc.)
                _type = product.get('Medium Type').strip()

                # Type of connector (SATA, USB, SCSI, etc.)
                ct_type = protocol.get('Physical Interconnect').strip()
                # Whether or not this device is internal or external.
                location = protocol.get(
                    'Physical Interconnect Location').strip()

                if ct_type.lower() == "pci-express":
                    _type = "Non-Volatile Memory Express (NVMe)"
                else:
                    _type = self.STORAGE.get(_type, _type)
            except Exception:
                self.logger.warning(
                    'Failed to construct valid format for storage device (IOKit)')
                continue

            self.info['Storage'].append({
                name: {
                    'Type': _type,
                    'Connector': ct_type,
                    'Location': location
                }
            })

            ioreg.IOObjectRelease(i)

    def input_info(self):
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
                hid = " (" + hid + ")"

            if any('{}{}'.format(name, hid) in k for k in self.info['Input']):
                continue

            try:
                dev = hex(device.get('ProductID'))
                ven = hex(device.get('VendorID'))

                data = {
                    'Device ID': dev,
                    'Vendor': ven
                }
            except Exception:
                self.logger.warning(
                    'Failed to obtain vendor/device id for Input device (IOKit)')
                data = {}

            name = '{}{}'.format(name,  hid)

            self.info['Input'].append({
                name: data
            })

            ioreg.IOObjectRelease(i)
