import re
import wmi
from src.util.codename_manager import CodenameManager
from .cpuid import CPUID
from src.util.codename import gpu as _gpu
from src.util.driver_type import protocol
from src.util.pci_root import pci_from_acpi_win
from src.error.cpu_err import cpu_err
from operator import itemgetter
from .win_enum import BUS_TYPE, MEDIA_TYPE, MEMORY_TYPE


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
        self.offline = parent.offline
        self.off_data = parent.off_data
        self.cpu = {}
        self.c = wmi.WMI()

    def dump(self):
        if not "CPU" in self.off_data and not self.info.get("CPU", []):
            self.cpu_info()
        if not "Motherboard" in self.off_data and not self.info.get("Motherboard", {}):
            self.mobo_info()
        if not "GPU" in self.off_data and not self.info.get("GPU", []):
            self.gpu_info()
        if not "Memory" in self.off_data and not self.info.get("Memory", []):
            self.mem_info()
        if not "Network" in self.off_data and not self.info.get("Network", []):
            self.net_info()
        if not "Audio" in self.off_data and not self.info.get("Audio", []):
            self.audio_info()
        if not "Input" in self.off_data and not self.info.get("Input", []):
            self.input_info()
        if not "Storage" in self.off_data and not self.info.get("Storage", []):
            self.storage_info()

    # Credits: https://github.com/flababah/cpuid.py/blob/master/example.py#L25
    def is_set(self, cpu, leaf, subleaf, reg_idx, bit):
        regs = cpu(leaf, subleaf)

        return bool((1 << bit) & regs[reg_idx])

    def cpu_info(self):

        # Credits to https://github.com/flababah
        # for writing this wonderful utility.
        #
        # See: https://github.com/flababah/cpuid.py
        cpu = CPUID()
        data = {}
        self.info["CPU"] = []

        try:
            CPU = self.c.instances("Win32_Processor")[0]

            # CPU Manufacturer (Intel and AMD codenames supported only.)
            manufacturer = CPU.wmi_property("Manufacturer").value

            # CPU model
            model = CPU.wmi_property("Name").value

            # Number of physical cores
            data["Cores"] = CPU.wmi_property("NumberOfCores").value

            # Number of logical processors (threads)
            data["Threads"] = CPU.wmi_property(
                "NumberOfLogicalProcessors").value

            self.cpu["model"] = model
        except Exception as e:
            self.logger.critical(
                f"Failed to obtain CPU information. This should not happen. \n\t^^^^^^^^^{str(e)}",
                __file__,
            )
            cpu_err(e)


        else:
            SSE = ["sse", "sse2", "sse3", "sse4.1", "sse4.2"]
            SSE_OP = [
                (1, 0, 3, 25),  # SSE
                (1, 0, 3, 26),  # SSE2
                (1, 0, 2, 0),   # SSE3
                (1, 0, 2, 19),  # SSE4.1
                (1, 0, 2, 20),  # SSE4.2
            ]
            SSSE3 = self.is_set(cpu, 1, 0, 2, 9)

            highest = "Unknown"

            if SSE:
                for i in range(len(SSE)):
                    if self.is_set(cpu, *SSE_OP[i]):
                        if highest.lower() == "unknown":
                            highest = SSE[i].upper()

                        elif float(highest[3:] if highest[3:] else 1) < float(
                            SSE[i][3:]
                        ):
                            highest = SSE[i].upper()

            data["SSE"] = highest
            data["SSSE3"] = "Supported" if SSSE3 else "Not Available"

            if not self.offline:
                self.cnm = CodenameManager(model, manufacturer)

                if self.cnm.codename:
                    data["Codename"] = self.cnm.codename

            self.info["CPU"].append({model: data})

    def gpu_info(self):
        try:
            GPUS = self.c.instances("Win32_VideoController")
        except Exception as e:
            self.logger.critical(
                f"Failed to obtain list of GPU devices (WMI)\n\t^^^^^^^^^{str(e)}",
                __file__,
            )
            return

        self.info["GPU"] = []

        for GPU in GPUS:
            try:
                gpu = GPU.wmi_property("Name").value
                pci = GPU.wmi_property("PNPDeviceID").value
                match = re.search(
                    "(VEN_(\d|\w){4})\&(DEV_(\d|\w){4})", pci)
            except Exception as e:
                self.logger.error(
                    f"Failed to obtain GPU device (WMI)\n\t^^^^^^^^^{str(e)}",
                    __file__,
                )
                continue

            data = {}
            ven, dev = "Unable to detect.", "Unable to detect."

            if match:
                ven, dev = [
                    "0x" + x.split("_")[1] for x in match.group(0).split("&")
                ]

                if ven and dev:
                    data["Device ID"] = dev
                    data["Vendor"] = ven

            try:
                paths = pci_from_acpi_win(self.c, pci, self.logger)

                if paths:
                    pcip = paths.get("PCI Path", "")
                    acpi = paths.get("ACPI Path", "")

                    if pcip:
                        data["PCI Path"] = pcip

                    if acpi:
                        data["ACPI Path"] = acpi
            except Exception as e:
                self.logger.warning(
                    f"Failed to construct PCI/ACPI paths for GPU device\n\t^^^^^^^^^{str(e)}",
                    __file__,
                )

            gpucname = _gpu(dev, ven)

            if gpucname:
                data["Codename"] = gpucname

            if not gpu:
                self.logger.warning(
                    "[POST]: Failed to obtain GPU device (WMI)", __file__
                )
                gpu = "Unknown GPU Device"

            self.info["GPU"].append({gpu: data})

    def mem_info(self):
        try:
            RAM = self.c.instances("Win32_PhysicalMemory")
        except Exception as e:
            self.logger.critical(
                f"Failed to obtain list of RAM modules (WMI)\n\t^^^^^^^^^{str(e)}",
                __file__,
            )
            return

        self.info["Memory"] = []

        for module in RAM:
            try:
                bank = module.wmi_property("BankLabel").value
                capacity = module.wmi_property("Capacity").value
                channel = module.wmi_property("DeviceLocator").value
                manufacturer = module.wmi_property("Manufacturer").value
                type = module.wmi_property("SMBIOSMemoryType").value
                spid = module.wmi_property("ConfiguredClockSpeed").value
                part_no = module.wmi_property("PartNumber").value.strip()
            except Exception as e:
                self.logger.critical(
                    f"Failed to obtain information about RAM module (WMI)\n\t^^^^^^^^^{str(e)}",
                    __file__,
                )
                continue

            self.info["Memory"].append(
                {
                    f"{part_no} (Part-Number)": {
                        "Type": MEMORY_TYPE.get(type) or "Unknown",
                        "Slot": {"Bank": bank, "Channel": channel},
                        "Frequency (MHz)": f"{spid} MHz",
                        "Manufacturer": manufacturer,
                        "Capacity": f"{round(int(capacity) / 0x100000)}MB",
                    }
                }
            )

    def net_info(self):
        try:
            NICS = self.c.instances("Win32_NetworkAdapter")
        except Exception as e:
            self.logger.critical(
                f"Failed to obtain list of Network controllers (WMI)\n\t^^^^^^^^^{str(e)}",
                __file__,
            )
            return
        
        self.info["Network"] = []

        for NIC in NICS:
            try:
                path = NIC.wmi_property("PNPDeviceID").value
                if not path:
                    continue

                data = {}
                model = {}
            except Exception as e:
                self.logger.warning(
                    f"Failed to obtain Network controller (WMI)\n\t^^^^^^^^^{str(e)}",
                    __file__,
                )
                continue

            usb = False
            match = re.search(
                "((VEN_(\d|\w){4})\&(DEV_(\d|\w){4}))|((VID_(\d|\w){4})\&(PID_(\d|\w){4}))",
                path,
            )

            ven, dev = "Unable to detect.", "Unable to detect."

            if match:
                ven, dev = [
                    "0x" + x.split("_")[1] for x in match.group(0).split("&")
                ]
            else:
                self.logger.warning(
                    "[POST]: Failed to obtain Network controller (WMI)",
                    __file__,
                )
                continue

            if self.offline:
                model = { "device": "Unknown Network Controller" }
            else:
                try:
                    model = (
                        self.pci.get_item(
                            dev[2:], ven[2:], types="pci" if not usb else "usb"
                        )
                        or {}
                    )
                except Exception:
                    model = { "device": "Unknown Network Controller" }

                    self.logger.warning(
                        f"Failed to obtain model for Network controller (WMI) – Non-critical, ignoring",
                        __file__,
                    )

            data = {"Device ID": dev, "Vendor": ven}

            try:
                paths = pci_from_acpi_win(self.c, path, self.logger)

                if paths:
                    pcip = paths.get("PCI Path", "")
                    acpi = paths.get("ACPI Path", "")

                    if pcip:
                        data["PCI Path"] = pcip

                    if acpi:
                        data["ACPI Path"] = acpi
            except Exception as e:
                self.logger.warning(
                    f"Failed to construct PCI/ACPI paths for Network controller\n\t^^^^^^^^^{str(e)}",
                    __file__,
                )

            if not model and "unable to" in data["Device ID"].lower():
                continue

            self.info["Network"].append(
                {model.get("device", "Unknown Network Controller"): data}
            )

            model = {}

    def audio_info(self):
        try:
            HDA = self.c.instances("Win32_SoundDevice")
        except Exception as e:
            self.logger.critical(
                f"Failed to obtain list of Sound devices (WMI)\n\t^^^^^^^^^{str(e)}",
                __file__,
            )
            return

        self.info["Audio"] = []

        for AUDIO in HDA:
            try:
                path = AUDIO.wmi_property("PNPDeviceID").value
                if not path:
                    continue

                data = {}
                model = {}
            except Exception as e:
                self.logger.error(
                    f"Failed to obtain Sound device (WMI)\n\t^^^^^^^^^{str(e)}",
                    __file__,
                )
                continue

            match = re.search(
                "((VEN_(\d|\w){4})\&(DEV_(\d|\w){4}))|((VID_(\d|\w){4})\&(PID_(\d|\w){4}))",
                path,
            )

            ven, dev = "Unable to detect.", "Unable to detect."

            if match:
                ven, dev = [
                    "0x" + x.split("_")[1] for x in match.group(0).split("&")
                ]

                if not "unable to" in ven.lower():
                    if "10ec" in ven.lower():
                        model = {
                            "device": f"Realtek ALC{hex(int(dev, 16))[2:]}"}
                    else:
                        if self.offline:
                            model = { "device": "Unknown Sound Device" }
                        else:
                            try:
                                model = self.pci.get_item(
                                    dev[2:], ven[2:])
                            except Exception:
                                model = { "device": "Unknown Sound Device" }

                                self.logger.warning(
                                    f"Failed to obtain model for Sound device (WMI) – Non-critical, ignoring",
                                    __file__,
                                )
                            
            else:
                self.logger.warning(
                    "[POST]: Failed to obtain Sound device (WMI)", __file__
                )
                continue

            data = {"Device ID": dev, "Vendor": ven}

            try:
                paths = pci_from_acpi_win(self.c, path, self.logger)

                if paths:
                    pcip = paths.get("PCI Path", "")
                    acpi = paths.get("ACPI Path", "")

                    if pcip:
                        data["PCI Path"] = pcip

                    if acpi:
                        data["ACPI Path"] = acpi
            except Exception as e:
                self.logger.warning(
                    f"Failed to construct PCI/ACPI paths for Sound device\n\t^^^^^^^^^{str(e)}",
                    __file__,
                )

            if not model and "unable to" in data["Device ID"].lower():
                continue

            self.info["Audio"].append(
                {model.get("device", "Unknown Sound Device"): data}
            )

            model = {}

    def mobo_info(self):
        try:
            self.info["Motherboard"] = {}

            MOBO = self.c.instances("Win32_BaseBoard")[0]
            model = MOBO.wmi_property("Product").value
            manufacturer = MOBO.wmi_property("Manufacturer").value
        except Exception as e:
            self.logger.critical(
                f"Failed to obtain Motherboard details (WMI)\n\t^^^^^^^^^{str(e)}",
                __file__,
            )
            return

        self.info["Motherboard"] = {
            "Model": model, "Manufacturer": manufacturer}

    def storage_info(self):
        try:
            # Credits to:
            # https://github.com/flagersgit
            STORAGE_DEV = wmi.WMI(namespace="Microsoft/Windows/Storage").query(
                "SELECT * FROM MSFT_PhysicalDisk"
            )
        except Exception as e:
            self.logger.critical(
                f"Failed to obtain list of Storage devices (WMI)\n\t^^^^^^^^^{str(e)}",
                __file__,
            )
            return

        self.info["Storage"] = []

        for STORAGE in STORAGE_DEV:
            try:
                model = STORAGE.wmi_property("FriendlyName").value

                if not model:
                    self.logger.warning(
                        "Failed to resolve friendly name for storage device (WMI)",
                        __file__,
                    )
                    model = "UNKNOWN"

                type = MEDIA_TYPE.get(
                    STORAGE.wmi_property("MediaType").value, "Unspecified"
                )
                ct_type, location = itemgetter("type", "location")(
                    BUS_TYPE.get(STORAGE.wmi_property(
                        "BusType").value, "Unknown")
                )

                if "nvme" in ct_type.lower():
                    type = "NVMe"
                    ct_type = "PCI Express"

                self.info["Storage"].append(
                    {model: {"Type": type, "Connector": ct_type, "Location": location}}
                )
            except Exception as e:
                self.logger.warning(
                    f"Failed to properly resolve storage device (WMI)\n\t^^^^^^^^^{str(e)}",
                    __file__,
                )
                continue

    def input_info(self):
        try:
            KBS = self.c.instances("Win32_Keyboard")
            PDS = self.c.instances("Win32_PointingDevice")
        except Exception as e:
            self.logger.critical(
                f"Failed to obtain list of Input devices (WMI)\n\t^^^^^^^^^{str(e)}",
                __file__,
            )
            return

        self.info["Input"] = []

        _kbs = self.get_kbpd(KBS)
        _pds = self.get_kbpd(PDS)

        for kb in _kbs:
            self.info["Input"].append(kb)

        for pd in _pds:
            self.info["Input"].append(pd)

    def get_kbpd(self, items):
        _items = []

        for item in items:
            try:
                description = item.wmi_property("Description").value
                pnp_id = item.wmi_property("PNPDeviceID").value

                d_type = protocol(pnp_id, self.logger, _wmi=self.c)

                if d_type:
                    description += f" ({d_type})"

                _items.append(
                    {description: {}})
            except Exception as e:
                self.logger.error(
                    f"Failed to obtain information about keyboard/pointing device (WMI)\n\t^^^^^^^^^{str(e)}",
                    __file__,
                )
                continue

        return _items
