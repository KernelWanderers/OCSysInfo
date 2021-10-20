import ctypes
import pathlib
import re
import json
import os
import wmi
from managers.devicemanager import DeviceManager
from util.codename import codename
from .cpuid import CPUID
from error.cpu_err import cpu_err
from root import root


class WindowsHardwareManager:
    """
    Instance, implementing `DeviceManager`, for extracting system information
    from Windows systems using the `WMI` infrastructure.

    https://docs.microsoft.com/en-us/windows/win32/wmisdk/wmi-start-page
    """

    def __init__(self, parent: DeviceManager):
        self.info = parent.info
        self.pci = parent.pci
        self.c = wmi.WMI()

    def dump(self):
        self.cpu_info()
        self.gpu_info()
        self.net_info()
        self.audio_info()
        self.mobo_info()
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
        except Exception as e:
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

                if not fam or \
                   not _model:
                    pass

                else:
                    fam = hex(int(fam.group()))
                    n = int(_model.group())

                    # Credits to:
                    # https://github.com/1Revenger1
                    extm = hex((n >> 0x4) & 0xf)
                    base = hex(n & 0xf)

                    extf = hex(self.extf(cpu, 1, 0))

                    vendor = 'intel' if 'intel' in manufacturer.lower() else 'amd'
                    _data = json.load(
                        open(os.path.join(root, 'src', 'uarch', f'{vendor}.json'), 'r'))

                    cname = codename(_data, extf.upper(),
                                     fam.upper(), extm.upper(), base.upper())

                    if cname:
                        data['Codename'] = cname
            except:
                pass

            self.info['CPU'].append({
                model: data
            })

    def gpu_info(self):
        try:
            GPUS = self.c.instances('Win32_VideoController')
        except:
            return
        else:
            for GPU in GPUS:
                try:
                    gpu = GPU.wmi_property('Name').value
                    pci = GPU.wmi_property('PNPDeviceID').value
                    match = re.search(
                        '(VEN_(\d|\w){4})\&(DEV_(\d|\w){4})', pci)
                except:
                    continue

                ven, dev = 'Unable to detect.', 'Unable to detect.'

                if match:
                    ven, dev = ['0x' + x.split('_')[1]
                                for x in match.group(0).split('&')]

                if not gpu:
                    continue

                self.info['GPU'].append({
                    gpu: {
                        'Device ID': dev,
                        'Vendor': ven
                    }
                })

    def net_info(self):
        try:
            NICS = self.c.instances('Win32_NetworkAdapter')
        except:
            return
        else:
            for NIC in NICS:
                try:
                    path = NIC.wmi_property('PNPDeviceID').value
                    pci = 'pci' in path.lower()
                except:
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
                    except:
                        continue

                    if not model:
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
        except:
            return
        else:
            for AUDIO in HDA:
                try:
                    path = AUDIO.wmi_property('PNPDeviceID').value
                    is_valid = 'hdaudio' in path.lower()
                except:
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
                        except:
                            continue

                        if not model:
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
        except:
            return
        else:
            self.info['Motherboard'] = {
                'Model': model,
                'Manufacturer': manufacturer
            }

    def input_info(self):
        try:
            KBS = self.c.instances('Win32_Keyboard')
            PDS = self.c.instances('Win32_PointingDevice')
        except:
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
                description = item.wmi_property('Description').value
                devid = item.wmi_property('DeviceID').value

                if not any(x in description.lower() for x in ('ps/2', 'hid', 'synaptics')):
                    continue

                _items.append({
                    description: {
                        'Device ID': devid
                    }
                })
            except:
                continue

        return _items
