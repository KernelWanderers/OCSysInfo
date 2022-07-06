import re
import wmi

from .cpuid import CPUID
from .win_enum import BUS_TYPE, MEDIA_TYPE, MEMORY_TYPE
from src.info import color_text
from src.util.codename_manager import CodenameManager
from src.util.codename import gpu as _gpu
from src.util.debugger import Debugger as debugger
from src.util.driver_type import protocol
from src.util.pci_root import pci_from_acpi_win
from src.error.cpu_err import cpu_err
from operator import itemgetter

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
            debugger.log_dbg("--> [WINDOWS]: Attempting to fetch CPU information...")
            self.cpu_info()
            debugger.log_dbg()

        if not "Motherboard" in self.off_data and not self.info.get("Motherboard", {}):
            debugger.log_dbg("--> [WINDOWS]: Attempting to fetch Motherboard information...")
            self.mobo_info()
            debugger.log_dbg()

        if not "GPU" in self.off_data and not self.info.get("GPU", []):
            debugger.log_dbg("--> [WINDOWS]: Attempting to fetch GPU information...")
            self.gpu_info()
            debugger.log_dbg()

        if not "Memory" in self.off_data and not self.info.get("Memory", []):
            debugger.log_dbg("--> [WINDOWS]: Attempting to fetch RAM information...")
            self.mem_info()
            debugger.log_dbg()

        if not "Network" in self.off_data and not self.info.get("Network", []):
            debugger.log_dbg("--> [WINDOWS]: Attempting to fetch NIC information...")
            self.net_info()
            debugger.log_dbg()

        if not "Audio" in self.off_data and not self.info.get("Audio", []):
            debugger.log_dbg("--> [WINDOWS]: Attempting to fetch Audio information...")
            self.audio_info()
            debugger.log_dbg()

        if not "Input" in self.off_data and not self.info.get("Input", []):
            debugger.log_dbg("--> [WINDOWS]: Attempting to fetch Input device information...")
            self.input_info()
            debugger.log_dbg()

        if not "Storage" in self.off_data and not self.info.get("Storage", []):
            debugger.log_dbg("--> [WINDOWS]: Attempting to fetch Storage information...")
            self.storage_info()
            debugger.log_dbg()

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
            debugger.log_dbg(color_text(
                "--> [CPU]: Attempting to fetch relevant information of current CPU... — (WMI)",
                "yellow"
            ))

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

            debugger.log_dbg(color_text(
                "--> [CPU]: Successfully obtained relevant information of current CPU! — (WMI)",
                "green"
            ))
        except Exception as e:
            debugger.log_dbg(color_text(
                "--> [CPU]: Failed to obtain critical information – this should not happen; aborting!" +
                f"\n\t^^^^^^^{str(e)}",
                "red"
            ))

            self.logger.critical(
                f"Failed to obtain CPU information. This should not happen. \n\t^^^^^^^^^{str(e)}",
                __file__,
            )

            cpu_err(e)


        else:
            debugger.log_dbg(color_text(
                "--> [CPU]: Attempting to fetch highest SSE version instruction set and SSSE3 availability...",
                "yellow"
            ))

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

            debugger.log_dbg(color_text(
                "--> [CPU]: Successfully obtained highest SSE version instruction set!",
                "green"
            ))

            if not self.offline:
                self.cnm = CodenameManager(model, manufacturer)

                if self.cnm.codename:
                    data["Codename"] = self.cnm.codename

            self.info["CPU"].append({model: data})

    def gpu_info(self):
        try:
            debugger.log_dbg(color_text(
                "--> [GPU]: Attempting to fetch list of GPU devices... — (WMI)",
                "yellow"
            ))

            GPUS = self.c.instances("Win32_VideoController")

            debugger.log_dbg(color_text(
                "--> [GPU]: Successfully obtained list of GPU devices! — (WMI)",
                "green"
            ))
        except Exception as e:
            debugger.log_dbg(color_text(
                "--> [GPU]: Failed to obtain list of GPU devices – critical! — (WMI)" +
                f"\n\t^^^^^^^{str(e)}",
                "red"
            ))

            self.logger.critical(
                f"Failed to obtain list of GPU devices (WMI)\n\t^^^^^^^^^{str(e)}",
                __file__,
            )
            return

        self.info["GPU"] = []

        for GPU in GPUS:
            try:
                debugger.log_dbg(color_text(
                    "--> [GPU]: Attempting to fetch GPU device name and identifier... — (WMI)",
                    "yellow"
                ))

                gpu = GPU.wmi_property("Name").value
                pci = GPU.wmi_property("PNPDeviceID").value

                match = re.search(
                    "(VEN_(\d|\w){4})\&(DEV_(\d|\w){4})", pci)

                debugger.log_dbg(color_text(
                    "--> [GPU]: Successfully obtained device name and identifier! — (WMI)",
                    "green"
                ))
            except Exception as e:
                debugger.log_dbg(color_text(
                    "--> [GPU]: Failed to obtain device name and identifier! — (WMI)" +
                    f"\n\t^^^^^^^{str(e)}",
                    "red"
                ))

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
                debugger.log_dbg(color_text(
                    f"--> [GPU]: Failed to construct PCI/ACPI paths for '{gpu}'! — (WMI)" +
                    f"\n\t^^^^^^^{str(e)}",
                    "red"    
                ))

                self.logger.warning(
                    f"Failed to construct PCI/ACPI paths for GPU device\n\t^^^^^^^^^{str(e)}",
                    __file__,
                )

            gpucname = _gpu(dev, ven)

            if gpucname:
                data["Codename"] = gpucname

            if not gpu:
                debugger.log_dbg(color_text(
                    "--> [GPU]: Failed to obtain GPU device – ignoring! — (WMI)",
                    "red"
                ))

                self.logger.warning(
                    "[POST]: Failed to obtain GPU device (WMI)", __file__
                )

                gpu = "Unknown GPU Device"

            self.info["GPU"].append({gpu: data})

    def mem_info(self):
        try:
            debugger.log_dbg(color_text(
                "--> [MEMORY]: Attempting to fetch RAM modules... — (WMI)",
                "yellow"
            ))

            RAM = self.c.instances("Win32_PhysicalMemory")

            debugger.log_dbg(color_text(
                "--> [MEMORY]: Successfully fetched RAM modules! — (WMI)",
                "green"
            ))
        except Exception as e:
            debugger.log_dbg(color_text(
                "--> [MEMORY]: Failed to fetch RAM modules – critical! — (WMI)" +
                f"\n\t^^^^^^^{str(e)}",
                "red"
            ))

            self.logger.critical(
                f"Failed to obtain list of RAM modules (WMI)\n\t^^^^^^^^^{str(e)}",
                __file__,
            )

            return

        self.info["Memory"] = []

        for module in RAM:
            try:
                debugger.log_dbg(color_text(
                    "--> [MEMORY]: Attempting to fetch information about RAM module... — (WMI)",
                    "yellow"
                ))

                bank            = module.wmi_property("BankLabel").value
                capacity        = module.wmi_property("Capacity").value
                channel         = module.wmi_property("DeviceLocator").value
                manufacturer    = module.wmi_property("Manufacturer").value
                mem_type        = module.wmi_property("SMBIOSMemoryType").value
                spid            = module.wmi_property("ConfiguredClockSpeed").value
                part_no         = module.wmi_property("PartNumber").value.strip()

                debugger.log_dbg(color_text(
                    "--> [MEMORY]: Successfully fetched information about RAM module! — (WMI)",
                    "green"
                ))
            except Exception as e:
                debugger.log_dbg(color_text(
                    "--> [MEMORY]: Failed to fetch information about RAM module! — (WMI)" +
                    f"\n\t^^^^^^^{str(e)}",
                    "red"
                ))

                self.logger.critical(
                    f"Failed to obtain information about RAM module (WMI)\n\t^^^^^^^^^{str(e)}",
                    __file__,
                )

                continue

            self.info["Memory"].append(
                {
                    f"{part_no} (Part-Number)": {
                        "Type": MEMORY_TYPE.get(mem_type) or "Unknown",
                        "Slot": {"Bank": bank, "Channel": channel},
                        "Frequency (MHz)": f"{spid} MHz",
                        "Manufacturer": manufacturer,
                        "Capacity": f"{round(int(capacity) / 0x100000)}MB",
                    }
                }
            )

    def net_info(self):
        try:
            debugger.log_dbg(color_text(
                "--> [Network]: Attempting to fetch list of Network controllers... — (WMI)",
                "yellow"
            ))

            NICS = self.c.instances("Win32_NetworkAdapter")

            debugger.log_dbg(color_text(
                "--> [Network]: Successfully fetched list of Network controllers! — (WMI)",
                "green"
            ))
        except Exception as e:
            debugger.log_dbg(color_text(
                "--> [Network]: Failted to fetch list of Network controllers – critical! — (WMI)" +
                f"\n\t^^^^^^^{str(e)}",
                "red"
            ))

            self.logger.critical(
                f"Failed to obtain list of Network controllers (WMI)\n\t^^^^^^^^^{str(e)}",
                __file__,
            )

            return
        
        self.info["Network"] = []

        for NIC in NICS:
            try:
                debugger.log_dbg(color_text(
                    "--> [Network]: Attempting to fetch identifier of current NIC... — (WMI)",
                    "yellow"
                ))

                path = NIC.wmi_property("PNPDeviceID").value
                
                if not path:
                    continue

                data = {}
                model = {}

                debugger.log_dbg(color_text(
                    "--> [Network]: Successfully obtained identifier of current NIC! — (WMI)",
                    "green"
                ))
            except Exception as e:
                debugger.log_dbg(color_text(
                    "--> [Network]: Failed to obtain identifier of current NIC – ignoring! — (WMI)" +
                    f"\n\t^^^^^^^{str(e)}",
                    "red"
                ))

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
                debugger.log_dbg(color_text(
                    "--> [Network]: Failed to obtain Device/Vendor ID(s) of current NIC – critical! — (WMI)",
                    "red"
                ))

                self.logger.warning(
                    "[POST]: Failed to obtain Network controller (WMI)",
                    __file__,
                )

                continue

            if self.offline:
                model = { "device": "Unknown Network Controller" }

                debugger.log_dbg(color_text(
                    "--> [Network]: Model name of current NIC unavailable – ignoring! — (WMI)",
                    "red"
                ))
            else:
                try:
                    model = (
                        self.pci.get_item(
                            dev[2:], ven[2:], types="pci" if not usb else "usb"
                        )
                        or {}
                    )
                except Exception as e:
                    model = { "device": "Unknown Network Controller" }

                    debugger.log_dbg(color_text(
                        "--> [Network]: Model name of current NIC can't be obtained – ignoring! — (WMI)" +
                        f"\n\t^^^^^^^{str(e)}",
                        "red"
                    ))

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
                debugger.log_dbg(color_text(
                    "--> [Network]: Failed to construct PCI/ACPI paths for current NIC – ignoring! — (WMI)" +
                    f"\n\t^^^^^^^{str(e)}",
                    "red"
                ))

                self.logger.warning(
                    f"Failed to construct PCI/ACPI paths for Network controller\n\t^^^^^^^^^{str(e)}",
                    __file__,
                )

            if not model and "unable to" in data["Device ID"].lower():
                continue

            debugger.log_dbg(color_text(
                "--> [Network]: Successfully parsed information for current NIC! — (WMI)",
                "green"
            ))

            self.info["Network"].append(
                {model.get("device", "Unknown Network Controller"): data}
            )

            model = {}

    def audio_info(self):
        try:
            debugger.log_dbg(color_text(
                "--> [Audio]: Attempting to obtain list of Audio controllers... — (WMI)",
                "yellow"
            ))

            HDA = self.c.instances("Win32_SoundDevice")

            debugger.log_dbg(color_text(
                "--> [Audio]: Successfully obtained list of Audio controllers! — (WMI)",
                "green"
            ))
        except Exception as e:
            debugger.log_dbg(color_text(
                "--> [Audio]: Failed to obtain list of Audio controllers – critical! — (WMI)" +
                f"\n\t^^^^^^^{str(e)}",
                "red"
            ))

            self.logger.critical(
                f"Failed to obtain list of Sound devices (WMI)\n\t^^^^^^^^^{str(e)}",
                __file__,
            )
            return

        self.info["Audio"] = []

        for AUDIO in HDA:
            try:
                debugger.log_dbg(color_text(
                    "--> [Audio]: Attempting to fetch identifier of current Audio controller... — (WMI)",
                    "yellow"
                ))

                path = AUDIO.wmi_property("PNPDeviceID").value

                if not path:
                    continue

                data = {}
                model = {}
                
                debugger.log_dbg(color_text(
                    "--> [Audio]: Successfully obtained identifier of current Audio controller! — (WMI)",
                    "green"
                ))
            except Exception as e:
                debugger.log_dbg(color_text(
                    "--> [Audio]: Failed to obtain identifier of current Audio controller! — (WMI)" +
                    f"\n\t^^^^^^^{str(e)}",
                    "red"
                ))

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

                            debugger.log_dbg(color_text(
                                "--> [Audio]: Model name of current Audio controller – unavailable! — (WMI)",
                                "red"
                            ))
                        else:
                            try:
                                model = self.pci.get_item(
                                    dev[2:], ven[2:])
                            except Exception as e:
                                model = { "device": "Unknown Sound Device" }

                                debugger.log_dbg(color_text(
                                    "--> [Audio]: Unable to obtain model name for Audio controller – ignoring! — (WMI)" +
                                    f"\n\t^^^^^^^{str(e)}",
                                    "red"
                                ))

                                self.logger.warning(
                                    f"Failed to obtain model for Sound device (WMI) – Non-critical, ignoring",
                                    __file__,
                                )
                            
            else:
                debugger.log_dbg(color_text(
                    "--> [Audio]: Failed to obtain Audio controller – critical! — (WMI)",
                    "red"
                ))

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
                debugger.log_dbg(color_text(
                    "--> [Audio]: Failed to construct PCI/ACPI paths for current Audio controller – ignoring! — (WMI)" +
                    f"\n\t^^^^^^^{str(e)}",
                    "red"
                ))

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

            debugger.log_dbg(color_text(
                "--> [Motherboard/Vendor]: Attempting to obtain information about motherboard/vendor... — (WMI)",
                "yellow"
            ))

            MOBO = self.c.instances("Win32_BaseBoard")[0]

            model = MOBO.wmi_property("Product").value
            manufacturer = MOBO.wmi_property("Manufacturer").value

            debugger.log_dbg(color_text(
                "--> [Motherboard/Vendor]: Successfully obtained information about motherboard/vendor! — (WMI)",
                "green"
            ))
        except Exception as e:
            debugger.log_dbg(color_text(
                "--> [Motherboard/Vendor]: Failed to obtain information about motherboard/vendor – critical! — (WMI)" +
                f"\n\t^^^^^^^{str(e)}",
                "red"
            ))

            self.logger.critical(
                f"Failed to obtain Motherboard details (WMI)\n\t^^^^^^^^^{str(e)}",
                __file__,
            )

            return

        self.info["Motherboard"] = {
            "Model": model, "Manufacturer": manufacturer}

    def storage_info(self):
        try:
            debugger.log_dbg(color_text(
                "--> [Storage]: Attempting to obtain list of Storage devices... — (WMI)",
                "yellow"
            ))

            # Credits to:
            # https://github.com/flagersgit
            STORAGE_DEV = wmi.WMI(namespace="Microsoft/Windows/Storage").query(
                "SELECT * FROM MSFT_PhysicalDisk"
            )

            debugger.log_dbg(color_text(
                "--> [Storage]: Successfully obtained list of Storage devices! — (WMI)",
                "green"
            ))
        except Exception as e:
            debugger.log_dbg(color_text(
                "--> [Storage]: Failed to obtain list of Storage devices – critical! — (WMI)" +
                f"\n\t^^^^^^^{str(e)}",
                "red"
            ))

            self.logger.critical(
                f"Failed to obtain list of Storage devices (WMI)\n\t^^^^^^^^^{str(e)}",
                __file__,
            )

            return

        self.info["Storage"] = []

        for STORAGE in STORAGE_DEV:
            try:
                debugger.log_dbg(color_text(
                    "--> [Storage]: Attempting to fetch information of Storage device... — (WMI)",
                    "yellow"
                ))

                model = STORAGE.wmi_property("FriendlyName").value

                if not model:
                    debugger.log_dbg(color_text(
                        "--> [Storage]: Failed to resolve “friendly name” for storage device – ignoring! — (WMI)",
                        "red"
                    ))

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

                debugger.log_dbg(color_text(
                    "--> [Storage]: Successfully obtained information of current Storage device! — (WMI)",
                    "green"
                ))
            except Exception as e:
                debugger.log_dbg(color_text(
                    "--> [Storage]: Failed to obtain information of current Storage device – ignoring! — (WMI)" +
                    f"\n\t^^^^^^^{str(e)}",
                    "red"
                ))

                self.logger.warning(
                    f"Failed to properly resolve storage device (WMI)\n\t^^^^^^^^^{str(e)}",
                    __file__,
                )

                continue

    def input_info(self):
        try:
            debugger.log_dbg(color_text(
                "--> [Input]: Attempting to fetch list of Input devices... — (WMI)",
                "yellow"
            ))

            KBS = self.c.instances("Win32_Keyboard")
            PDS = self.c.instances("Win32_PointingDevice")

            debugger.log_dbg(color_text(
                "--> [Input]: Successfully obtained list of Input devices! — (WMI)",
                "green"
            ))
        except Exception as e:
            debugger.log_dbg(color_text(
                "--> [Input]: Failed to obtain list of Input devices – critical! — (WMI)" +
                f"\n\t^^^^^^^{str(e)}",
                "red"
            ))

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
                debugger.log_dbg(color_text(
                    "--> [Input]: Attempting to fetch information about current Input device... — (WMI)",
                    "yellow"
                ))

                description = item.wmi_property("Description").value
                pnp_id = item.wmi_property("PNPDeviceID").value
                ven, prod = [x[2] for x in re.findall(r"(?<=(PID_)|(VID_))((\d|\w){4})", pnp_id)]

                d_type = protocol(pnp_id, self.logger, _wmi=self.c)

                if d_type:
                    description += f" ({d_type})"

                _items.append({
                    description: {
                        "Product ID": "0x" + prod,
                        "Vendor ID": "0x" + ven
                    }
                })

                debugger.log_dbg(color_text(
                    "--> [Input]: Successfully obtained information about current Input device! — (WMI)",
                    "green"
                ))
            except Exception as e:
                debugger.log_dbg(color_text(
                    "--> [Input]: Failed to obtain information about current Input device – ignoring! — (WMI)" +
                    f"\n\t^^^^^^^{str(e)}",
                    "red"
                ))

                self.logger.error(
                    f"Failed to obtain information about keyboard/pointing device (WMI)\n\t^^^^^^^^^{str(e)}",
                    __file__,
                )

                continue

        return _items
