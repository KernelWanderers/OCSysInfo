import re
import json
import os
import wmi
from .cpuid import CPUID
from util.codename import codename, gpu as _gpu
from util.pci_root import pci_from_acpi_win
from error.cpu_err import cpu_err
from root import root
from operator import itemgetter
from .win_enum import BUS_TYPE, MEDIA_TYPE, POINT_DEV_INTERFACE


class WindowsHardwareManager:
    """
    Instance, implementing `DeviceManager`, for extracting system information
    from Windows systems using the `WMI` infrastructure.

    https://docs.microsoft.com/en-us/windows/win32/wmisdk/wmi-start-page
    """

    def __init__(self, parent):
        self.info = parent.info
        self.pci = parent.pci
        self.logger = parent.logger
        self.cpu = {}
        self.c = wmi.WMI()

    def dump(self):
        self.cpu_info()
        self.gpu_info()
        self.net_info()
        self.audio_info()
        self.mobo_info()
        self.storage_info()
        self.input_info()

    # Credits: https://github.com/flababah/cpuid.py/blob/master/example.py#L25
    def is_set(self, cpu, leaf, subleaf, reg_idx, bit):
        regs = cpu(leaf, subleaf)

        return bool((1 << bit) & regs[reg_idx])

    def extf(self, cpu, leaf, subleaf):
        eax = cpu(leaf, subleaf)[0]

        return (eax >> 20) & 0xf

    def cpu_info(self):

        # Credits to https://github.com/flababah
        # for writing this wonderful utility.
        #
        # See: https://github.com/flababah/cpuid.py
        cpu = CPUID()
        data = {}

        try:
            CPU = self.c.instances('Win32_Processor')[0]

            # CPU Manufacturer (Intel and AMD codenames supported only.)
            manufacturer = CPU.wmi_property('Manufacturer').value

            # CPU model
            model = CPU.wmi_property('Name').value

            # Number of physical cores
            data['Cores'] = CPU.wmi_property('NumberOfCores').value

            # Number of logical processors (threads)
            data['Threads'] = CPU.wmi_property(
                'NumberOfLogicalProcessors').value

            self.cpu['model'] = model
        except Exception as e:
            self.logger.critical(
                f'Failed to obtain CPU information. This should not happen. \nSnippet relevant to former line^^^\t^^^{str(e)}')
            cpu_err(e)

        else:
            SSE = ['sse', 'sse2', 'sse3', 'sse4.1', 'sse4.2']
            SSE_OP = [
                (1, 0, 3, 25),  # SSE
                (1, 0, 3, 26),  # SSE2
                (1, 0, 2, 0),   # SSE3
                (1, 0, 2, 19),  # SSE4.1
                (1, 0, 2, 20)   # SSE4.2
            ]
            SSSE3 = self.is_set(cpu, 1, 0, 2, 9)

            highest = 'Unknown'

            if SSE:
                for i in range(len(SSE)):
                    if self.is_set(cpu, *SSE_OP[i]):
                        if highest.lower() == 'unknown':
                            highest = SSE[i].upper()

                        elif float(highest[3:] if highest[3:] else 1) < float(SSE[i][3:]):
                            highest = SSE[i].upper()

            data['SSE'] = highest
            data['SSSE3'] = 'Supported' if SSSE3 else 'Not Available'

            try:
                desc = CPU.wmi_property('Description').value
                fam = re.search(r'(?<=Family\s)\d+', desc)
                _model = re.search(r'(?<=Model\s)\d+', desc)
                stepping = re.search(r'(?<=Stepping\s)\d+', desc)

                # Chassis Types:
                #
                # Laptop        : 9
                # Notebook      : 10
                # Sub Notebook  : 14
                laptop = self.c.instances('Win32_SystemEnclosure')[
                    0].wmi_property('ChassisTypes').value[0] in (9, 10, 14)

                if not fam or \
                   not _model:
                    pass

                else:
                    fam = hex(int(fam.group()))
                    n = int(_model.group())

                    if stepping:
                        stepping = hex(int(stepping.group()))
                    else:
                        stepping = None

                    # Credits to:
                    # https://github.com/1Revenger1
                    extm = hex((n >> 0x4) & 0xf)
                    base = hex(n & 0xf)

                    extf = hex(self.extf(cpu, 1, 0))

                    vendor = 'intel' if 'intel' in manufacturer.lower() else 'amd'
                    _data = json.load(
                        open(os.path.join(root, 'src', 'uarch', 'cpu', f'{vendor}.json'), 'r'))

                    cname = codename(_data, extf,
                                     fam, extm, base, stepping=stepping, laptop=laptop)

                    if cname:
                        self.cpu['codename'] = cname if len(
                            cname) > 1 else cname[0]
            except Exception:
                self.logger.warning(
                    f'Failed to construct extended family – ({model})')
                pass

            self.info['CPU'].append({
                model: data
            })

    def gpu_info(self):
        try:
            GPUS = self.c.instances('Win32_VideoController')
        except Exception:
            return
        else:
            for GPU in GPUS:
                try:
                    gpu = GPU.wmi_property('Name').value
                    pci = GPU.wmi_property('PNPDeviceID').value
                    match = re.search(
                        '(VEN_(\d|\w){4})\&(DEV_(\d|\w){4})', pci)
                except Exception:
                    self.logger.warning('Failed to obtain GPU device (WMI)')
                    continue

                data = {}
                ven, dev = 'Unable to detect.', 'Unable to detect.'

                if match:
                    ven, dev = ['0x' + x.split('_')[1]
                                for x in match.group(0).split('&')]

                    if ven and dev:
                        data['Device ID'] = dev
                        data['Vendor'] = ven

                try:
                    paths = pci_from_acpi_win(self.c, gpu)

                    if paths:
                        pcip = paths.get('PCI Path', '')
                        acpi = paths.get('ACPI Path', '')

                        if pcip:
                            data['PCI Path'] = pcip

                        if acpi:
                            data['ACPI Path'] = acpi
                except Exception as e:
                    print(e)
                    pass

                gpucname = _gpu(dev, ven)

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

                if not gpu:
                    self.logger.warning(
                        '[POST]: Failed to obtain GPU device (WMI)')
                    continue

                self.info['GPU'].append({
                    gpu: data
                })

            if self.cpu.get('codename', None):
                self.info['CPU'][0][self.cpu['model']
                                    ]['Codename'] = self.cpu['codename']

    def net_info(self):
        try:
            NICS = self.c.instances('Win32_NetworkAdapter')
        except Exception:
            return
        else:
            for NIC in NICS:
                try:
                    path = NIC.wmi_property('PNPDeviceID').value
                    pci = 'pci' in path.lower()
                except Exception:
                    self.logger.warning(
                        'Failed to obtain Network controller (WMI)')
                    continue

                if pci:
                    match = re.search(
                        '(VEN_(\d|\w){4})\&(DEV_(\d|\w){4})', path)

                    ven, dev = 'Unable to detect.', 'Unable to detect.'

                    if match:
                        ven, dev = ['0x' + x.split('_')[1]
                                    for x in match.group(0).split('&')]

                    try:
                        model = self.pci.get_item(dev[2:], ven[2:])
                    except Exception:
                        continue

                    if not model:
                        self.logger.warning(
                            '[POST]: Failed to obtain Network controller (WMI)')
                        continue

                    self.info['Network'].append({
                        model.get('device'): {
                            'Device ID': dev,
                            'Vendor': ven
                        }
                    })

    def audio_info(self):
        try:
            HDA = self.c.instances('Win32_SoundDevice')
        except Exception:
            return
        else:
            for AUDIO in HDA:
                try:
                    path = AUDIO.wmi_property('PNPDeviceID').value
                    is_valid = 'hdaudio' in path.lower()
                except Exception:
                    self.logger.warning('Failed to obtain Sound device (WMI)')
                    continue

                if is_valid:
                    match = re.search(
                        '(VEN_(\d|\w){4})\&(DEV_(\d|\w){4})', path)

                    ven, dev = 'Unable to detect.', 'Unable to detect.'

                    if match:
                        ven, dev = ['0x' + x.split('_')[1]
                                    for x in match.group(0).split('&')]

                        try:
                            model = self.pci.get_item(dev[2:], ven[2:])
                        except Exception:
                            continue

                        if not model:
                            self.logger.warning(
                                '[POST]: Failed to obtain Sound device (WMI)')
                            continue

                        self.info['Audio'].append({
                            model.get('device'): {
                                'Device ID': dev,
                                'Vendor': ven
                            }
                        })

    def mobo_info(self):
        try:
            MOBO = self.c.instances('Win32_BaseBoard')[0]
            model = MOBO.wmi_property('Product').value
            manufacturer = MOBO.wmi_property('Manufacturer').value
        except Exception:
            self.logger.warning(
                'Failed to obtain Motherboard details (WMI)')
            return
        else:
            self.info['Motherboard'] = {
                'Model': model,
                'Manufacturer': manufacturer
            }

    def storage_info(self):
        try:
            # Credits to:
            # https://github.com/flagersgit
            STORAGE_DEV = wmi.WMI(
                namespace="Microsoft/Windows/Storage").query("SELECT * FROM MSFT_PhysicalDisk")
        except Exception:
            return

        for STORAGE in STORAGE_DEV:
            try:
                model = STORAGE.wmi_property('FriendlyName').value

                if not model:
                    self.logger.warning(
                        'Failed to resolve friendly name for storage device (WMI)')
                    model = "UNKNOWN"

                type = MEDIA_TYPE.get(
                    STORAGE.wmi_property('MediaType').value, 'Unspecified')
                ct_type, location = itemgetter('type', 'location')(BUS_TYPE.get(
                    STORAGE.wmi_property('BusType').value, 'Unknown'))

                self.info['Storage'].append({
                    model: {
                        'Type': type,
                        'Connector': ct_type,
                        'Location': location
                    }
                })
            except Exception:
                self.logger.warning(
                    'Failed to properly resolve storage device (WMI)')
                continue

    def input_info(self):
        try:
            KBS = self.c.instances('Win32_Keyboard')
            PDS = self.c.instances('Win32_PointingDevice')
        except Exception:
            return
        else:
            _kbs = self.get_kbpd(KBS)
            _pds = self.get_kbpd(PDS)

            for kb in _kbs:
                self.info['Input'].append(kb)

            for pd in _pds:
                self.info['Input'].append(pd)

    def get_kbpd(self, items):
        _items = []
        for item in items:
            try:
                data = {}

                description = item.wmi_property('Description').value
                devid = item.wmi_property('DeviceID').value

                data[description] = {
                    'Device ID': devid
                }

                try:
                    devint = POINT_DEV_INTERFACE.get(
                        item.wmi_property('DeviceInterface').value, None)

                    if devint:
                        data[description]['Interface'] = devint
                except Exception:
                    self.logger.warning(
                        f'Failed to obtain interface information for "{description}" (WMI)')
                    pass

                if not any(x in description.lower() for x in ('ps/2', 'hid', 'synaptics')):
                    continue

                _items.append(data)
            except Exception:
                self.logger.warning(
                    'Failed to obtain information about keyboard/pointing device (WMI)')
                continue

        return _items
