import binascii
import math
import subprocess
from src.dumps.macOS.ioreg import *
from src.error.cpu_err import cpu_err
from src.info import color_text
from src.util.codename import gpu
from src.util.codename_manager import CodenameManager
from src.util.debugger import Debugger as debugger
from src.util.pci_root import construct_pcip_osx


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
        self.offline = parent.offline
        self.off_data = parent.off_data
        self.vendor = ""
        self.cpu = {}

        self.STORAGE = {
            "Solid State": "Solid State Drive (SSD)",
            "Rotational": "Hard Disk Drive (HDD)",
        }

    def dump(self):
        if not "CPU" in self.off_data and not self.info.get("CPU", []):
            debugger.log_dbg("--> [OSX]: Attempting to fetch CPU information...")
            self.cpu_info()
            debugger.log_dbg()

        if (
            not "Vendor" in self.off_data or not "Motherboard" in self.off_data
        ) and not self.info.get("Vendor", {}):
            debugger.log_dbg("--> [OSX]: Attempting to fetch Baseboard information...")
            self.vendor_info()
            debugger.log_dbg()

        if not "GPU" in self.off_data and not self.info.get("GPU", []):
            debugger.log_dbg("--> [OSX]: Attempting to fetch GPU information...")
            self.gpu_info()
            debugger.log_dbg()

        if not "Memory" in self.off_data and not self.info.get("Memory", []):
            debugger.log_dbg("--> [OSX]: Attempting to fetch RAM information...")
            self.mem_info()
            debugger.log_dbg()

        if not "Network" in self.off_data and not self.info.get("Network", []):
            debugger.log_dbg("--> [OSX]: Attempting to fetch NIC information...")
            self.net_info()
            debugger.log_dbg()

        if not "Audio" in self.off_data and not self.info.get("Audio", []):
            debugger.log_dbg("--> [OSX]: Attempting to fetch Audio information...")
            self.audio_info()
            debugger.log_dbg()

        if not "Input" in self.off_data and not self.info.get("Input", []):
            debugger.log_dbg(
                "--> [OSX]: Attempting to fetch Input device information..."
            )
            self.input_info()
            debugger.log_dbg()

        if not "Storage" in self.off_data and not self.info.get("Storage", []):
            debugger.log_dbg("--> [OSX]: Attempting to fetch Storage information...")
            self.storage_info()
            debugger.log_dbg()

        if not "Display" in self.off_data and not self.info.get("Display", []):
            debugger.log_dbg("--> [OSX]: Attempting to fetch Display information...")
            self.display_info()
            debugger.log_dbg()

    def cpu_info(self):
        try:
            debugger.log_dbg(
                color_text(
                    "--> [CPU]: Attempting to fetch relevant information of current CPU... — (SYSCTL)",
                    "yellow",
                )
            )

            # Model of the CPU
            model = (
                subprocess.check_output(["sysctl", "machdep.cpu.brand_string"])
                .decode()
                .split(": ")[1]
                .strip()
            )

            self.cpu["model"] = model

            debugger.log_dbg(
                color_text(
                    "--> [CPU]: Successfully obtained relevant information of current CPU! — (SYSCTL)",
                    "green",
                )
            )
        except Exception as e:
            debugger.log_dbg(
                color_text(
                    "--> [CPU]: Failed to obtain critical information – this should not happen; aborting! — (SYSCTL)"
                    + f"\n\t^^^^^^^{str(e)}",
                    "red",
                )
            )

            self.logger.critical(
                f"Failed to obtain CPU information. This should not happen. \n\t^^^^^^^^^{str(e)}",
                __file__,
            )

            cpu_err(e)

        self.info["CPU"] = []

        if ".vendor" in subprocess.check_output(["sysctl", "machdep.cpu"]).decode():
            try:
                debugger.log_dbg(
                    color_text(
                        "--> [CPU]: Attempting to fetch highest SSE version instruction set and SSSE3 availability... — (SYSCTL)",
                        "yellow",
                    )
                )

                # Manufacturer/Vendor of this CPU
                self.vendor = (
                    "intel"
                    if "intel"
                    in subprocess.check_output(["sysctl", "machdep.cpu.vendor"])
                    .decode()
                    .split(": ")[1]
                    .strip()
                    .lower()
                    else "amd"
                )

                # Full list of features for this CPU.
                features = (
                    subprocess.check_output(["sysctl", "machdep.cpu.features"])
                    .decode()
                    .strip()
                )

                debugger.log_dbg(
                    color_text(
                        "--> [CPU]: Successfully obtained highest SSE version instruction set! — (SYSCTL)",
                        "green",
                    )
                )
            except Exception as e:
                debugger.log_dbg(
                    color_text(
                        "--> [CPU]: Successfully obtained highest SSE version instruction set! — (SYSCTL)"
                        + f"\n\t^^^^^^^{str(e)}",
                        "red",
                    )
                )

                self.logger.warning(
                    f"Failed to access CPUID instruction – ({model})\n\t^^^^^^^^^{str(e)}",
                    __file__,
                )

                self.vendor = None
                features = None
        else:
            debugger.log_dbg(
                color_text(
                    "--> [CPU]: Unable to fetch instruction sets list – Apple ARM64 machine - ignoring! — (SYSCTL)",
                    "red",
                )
            )

            self.vendor = "apple"
            features = None

        data = {
            # Amount of cores for this processor.
            "Cores": subprocess.check_output(["sysctl", "machdep.cpu.core_count"])
            .decode()
            .split(": ")[1]
            .strip()
            + " cores",
            # Amount of threads for this processor.
            "Threads": subprocess.check_output(["sysctl", "machdep.cpu.thread_count"])
            .decode()
            .split(": ")[1]
            .strip()
            + " threads",
        }

        # This will fail if the CPU is _not_
        # of an x86-like architecture, which
        # traditionally uses the CPUID instruction.
        #
        # See: https://en.wikipedia.org/wiki/CPUID
        if features:
            # Highest supported SSE version.
            data["SSE"] = sorted(
                list(
                    filter(
                        lambda f: "sse" in f.lower() and not "ssse" in f.lower(),
                        features.split(": ")[1].split(" "),
                    )
                ),
                reverse=True,
            )[0]

            # Whether or not SSSE3 support is present.
            data["SSSE3"] = (
                "Supported" if features.lower().find("ssse3") > -1 else "Not Available"
            )

        if not self.offline:
            self.cnm = CodenameManager(model, self.vendor)

            if self.cnm.codename:
                data["Codename"] = self.cnm.codename

        self.info["CPU"].append({model: data})

    def vendor_info(self):
        try:
            debugger.log_dbg(
                color_text(
                    "--> [Motherboard/Vendor]: Attempting to obtain information about motherboard/vendor... — (IOKit)",
                    "yellow",
                )
            )

            VENDOR = corefoundation_to_native(
                IORegistryEntryCreateCFProperties(
                    next(
                        ioiterator_to_list(
                            IOServiceGetMatchingServices(
                                kIOMasterPortDefault,
                                IOServiceMatching(b"IOPlatformExpertDevice"),
                                None,
                            )[1]
                        )
                    ),
                    None,
                    kCFAllocatorDefault,
                    kNilOptions,
                )
            )[1]

            model = VENDOR.get("model").decode().replace("\x00", "")
            manuf = VENDOR.get("manufacturer").decode().replace("\x00", "")

            self.info["Vendor"] = {"Model": model, "Manufacturer": manuf}

            debugger.log_dbg(
                color_text(
                    "--> [Motherboard/Vendor]: Successfully obtained information about motherboard/vendor! — (IOKit)",
                    "green",
                )
            )
        except Exception as e:
            debugger.log_dbg(
                color_text(
                    "--> [Motherboard/Vendor]: Failed to obtain information about motherboard/vendor – critical! — (IOKit)"
                    + f"\n\t^^^^^^^{str(e)}",
                    "red",
                )
            )

            self.logger.warning(
                f"Failed to obtain vendor model/manufacturer for machine – Non-critical, ignoring.",
                __file__,
            )

            return

    def gpu_info(self, default=True):
        if default:
            device = {
                "IOProviderClass": "IOPCIDevice",
                # Bit mask matching, ensuring that the 3rd byte is one of the display controller (0x03).
                "IOPCIClassMatch": "0x03000000&0xff000000",
            }
        else:
            device = {"IONameMatched": "gpu*"}

        debugger.log_dbg(
            color_text(
                "--> [GPU]: Attempting to fetch list of GPU devices... — (IOKit)",
                "yellow",
            )
        )

        # Obtain generator instance, whose values are `CFDictionary`-ies
        interface = ioiterator_to_list(
            IOServiceGetMatchingServices(kIOMasterPortDefault, device, None)[1]
        )

        if interface:
            debugger.log_dbg(
                color_text(
                    "--> [GPU]: Successfully obtained list of GPU devices! — (IOKit)",
                    "green",
                )
            )
        else:
            debugger.log_dbg(
                color_text(
                    "--> [GPU]: Failed to obtain list of GPU devices – critical! — (IOKit)",
                    "red",
                )
            )

            return

        self.info["GPU"] = []

        # Loop through the generator returned from `ioiterator_to_list()`
        for i in interface:
            data = {}

            # Obtain CFDictionaryRef of the current PCI/AppleARM device.
            device = corefoundation_to_native(
                IORegistryEntryCreateCFProperties(
                    i, None, kCFAllocatorDefault, kNilOptions
                )
            )[1]

            # I don't know why there needs to be
            # a try clause here, but it does.
            try:
                # For Apple's M1 iGFX
                if (
                    not default
                    and
                    # If both return true, that means
                    # we aren't dealing with a GPU device.
                    not "gpu" in device.get("IONameMatched", "").lower()
                    and not "AGX" in device.get("CFBundleIdentifierKernel", "")
                ):
                    continue
            except Exception:
                continue

            try:
                debugger.log_dbg(
                    color_text(
                        "--> [GPU]: Attempting to fetch GPU device model... — (IOKit)",
                        "yellow",
                    )
                )

                model = device.get("model", None)

                if not model:
                    continue

                if default:
                    model = bytes(model).decode()
                    model = model[0 : len(model) - 1]

                debugger.log_dbg(
                    color_text(
                        "--> [GPU]: Successfully obtained GPU device model! — (IOKit)",
                        "green",
                    )
                )
            except Exception as e:
                debugger.log_dbg(
                    color_text(
                        "--> [GPU]: Failed to obtain GPU device model – critical! — (IOKit)"
                        + f"\n\t^^^^^^^{str(e)}",
                        "red",
                    )
                )

                self.logger.error(
                    "Failed to obtain GPU device model (IOKit)"
                    + f"\n\t^^^^^^^^^{str(e)}",
                    __file__,
                )

                continue

            try:
                debugger.log_dbg(
                    color_text(
                        "--> [GPU]: Attempting to fetch other GPU information... — (IOKit)",
                        "yellow",
                    )
                )

                if default:
                    # Reverse the byte sequence, and format it using `binascii` – remove leading 0s
                    dev = "0x" + (
                        binascii.b2a_hex(
                            bytes(reversed(device.get("device-id")))
                        ).decode()[4:]
                    )
                else:
                    gpuconf = device.get("GPUConfigurationVariable", {})
                    dev = ""

                    data["Cores"] = str(gpuconf.get("num_cores")) + " Cores"
                    data["NE Cores"] = (
                        (str(gpuconf.get("num_gps")) + " Neural Engine Cores")
                        if gpuconf.get("num_mgpus")
                        else None
                    )
                    data["Generation"] = (
                        ("Generation " + str(gpuconf.get("gpu_gen")))
                        if gpuconf.get("gpu_gen")
                        else None
                    )

                # Reverse the byte sequence, and format it using `binascii` – remove leading 0s
                ven = "0x" + (
                    binascii.b2a_hex(bytes(reversed(device.get("vendor-id")))).decode()[
                        4:
                    ]
                )

                data["Vendor ID"] = ven

                if dev:
                    data["Device ID"] = dev

                if default:
                    path = construct_pcip_osx(
                        i, device.get("acpi-path", ""), self.logger
                    )

                    pcip = path.get("PCI Path", "")
                    acpi = path.get("ACPI Path", "")

                    if pcip:
                        data["PCI Path"] = pcip

                    if acpi:
                        data["ACPI Path"] = acpi

                debugger.log_dbg(
                    color_text(
                        "--> [GPU]: Successfully obtained other GPU information! — (IOKit)",
                        "green",
                    )
                )
            except Exception as e:
                debugger.log_dbg(
                    color_text(
                        "--> [GPU]: Failed to obtain other GPU information – ignoring! — (IOKit)"
                        + f"\n\t^^^^^^^{str(e)}",
                        "red",
                    )
                )

                self.logger.error(
                    "Failed to obtain other information for GPU device (IOKit)"
                    + f"\n\t^^^^^^^^^{str(e)}",
                    __file__,
                )

                dev, ven = "", ""
                data = {}

            if default:
                gpucname = gpu(dev, ven)

                if gpucname:
                    data["Codename"] = gpucname

            self.info["GPU"].append({model: data})

            IOObjectRelease(i)

        if default and self.vendor == "apple":
            self.gpu_info(default=False)

    def mem_info(self):

        debugger.log_dbg(
            color_text(
                "--> [MEMORY]: Attempting to fetch RAM modules... — (IOKit)", "yellow"
            )
        )

        if self.vendor == "apple":
            debugger.log_dbg(
                color_text(
                    "--> [MEMORY]: Unable to fetch RAM modules – RAM is built into the CPU! — (IOKit)",
                    "red",
                )
            )

            return

        # Special thanks to [Flagers](https://github.com/flagersgit) for this.
        #
        # Source: https://github.com/KernelWanderers/OCSysInfo/pull/10
        interface = corefoundation_to_native(
            IORegistryEntryCreateCFProperties(
                IORegistryEntryFromPath(kIOMasterPortDefault, b"IODeviceTree:/memory"),
                None,
                kCFAllocatorDefault,
                kNilOptions,
            )[1]
        )

        if interface:
            debugger.log_dbg(
                color_text(
                    "--> [MEMORY]: Successfully fetched RAM modules! — (IOKit)", "green"
                )
            )
        else:
            debugger.log_dbg(
                color_text(
                    "--> [MEMORY]: Failed to fetch RAM modules – critical! — (IOKit)",
                    "red",
                )
            )

            return

        self.info["Memory"] = []
        modules = []
        part_no = []
        sizes = []
        length = None

        for prop in interface:
            val = interface[prop]

            if not length and "part-number" not in prop:
                debugger.log_dbg(
                    color_text(
                        "--> [MEMORY]: No length specified for this RAM module – critical! — (IOKit/Memory)",
                        "red",
                    )
                )

            if type(val) == bytes:
                if "reg" in prop.lower():
                    for i in range(length):
                        try:
                            # Converts non-0 values from the 'reg' property
                            # into readable integer values representing the memory capacity.
                            sizes.append(
                                [
                                    round(n * 0x010000 / 0x10)
                                    for n in val.replace(b"\x00", b"")
                                ][i]
                            )
                        except Exception as e:
                            debugger.log_dbg(
                                color_text(
                                    "--> [MEMORY]: Failed to convert value to readable size – critical! — (IOKit/Memory)"
                                    + f"\n\t^^^^^^^{str(e)}",
                                    "red",
                                )
                            )

                            self.logger.error(
                                f"Failed to convert value to readable size (IOKit/MemInfo)\n\t^^^^^^^^^{str(e)}",
                                __file__,
                            )

                            modules = []
                            break

                else:
                    try:
                        val = [
                            x.decode()
                            for x in val.split(b"\x00")
                            if type(x) == bytes and x.decode().strip()
                        ]
                    except Exception as e:
                        debugger.log_dbg(
                            color_text(
                                "--> [MEMORY]: Failed to decode bytes of RAM module – critical! — (IOKit/Memory)"
                                + f"\n\t^^^^^^^{str(e)}",
                                "red",
                            )
                        )

                        self.logger.warning(
                            f"Failed to decode bytes for RAM module (IOKit/MemInfo)\n\t^^^^^^^^^{str(e)}",
                            __file__,
                        )

                        continue

            if "part-number" in prop:
                length = len(val)

                for i in range(length):
                    debugger.log_dbg(
                        color_text(
                            "--> [MEMORY]: Obtained part-number of current RAM module! — (IOKit/Memory)",
                            "green",
                        )
                    )

                    modules.append({f"{val[i]} (Part-Number)": {}})
                    part_no.append(f"{val[i]} (Part-Number)")

            else:
                for i in range(length):
                    key = ""
                    value = None

                    if "dimm-types" in prop.lower():
                        debugger.log_dbg(
                            color_text(
                                "--> [MEMORY]: Obtained DIMM type of current RAM module! — (IOKit/Memory)",
                                "green",
                            )
                        )

                        key = "Type"
                        value = val[i]

                    elif "slot-names" in prop.lower():
                        key = "Slot"

                        try:
                            bank, channel = val[i].split("/")

                            value = {"Bank": bank, "Channel": channel}

                            debugger.log_dbg(
                                color_text(
                                    "--> [MEMORY]: Obtained location of current RAM module! — (IOKit/Memory)",
                                    "green",
                                )
                            )
                        except Exception as e:
                            debugger.log_dbg(
                                color_text(
                                    "--> [MEMORY]: Failed to obtain location of current RAM module – ignoring! — (IOKit/Memory)"
                                    + f"\n\t^^^^^^^{str(e)}",
                                    "red",
                                )
                            )

                            self.logger.error(
                                f"Failed to obtain BANK/Channel values for RAM module! (IOKit/MemInfo)\n\t^^^^^^^^^{str(e)}",
                                __file__,
                            )

                    elif "dimm-speeds" in prop.lower():
                        debugger.log_dbg(
                            color_text(
                                "--> [MEMORY]: Obtained clock-speed of current RAM module! — (IOKit/Memory)",
                                "green",
                            )
                        )

                        key = "Frequency (MHz)"
                        value = val[i]

                    elif "dimm-manufacturer" in prop.lower():
                        debugger.log_dbg(
                            color_text(
                                "--> [MEMORY]: Obtained manufacturer of current RAM module! — (IOKit/Memory)",
                                "green",
                            )
                        )

                        key = "Manufacturer"
                        value = val[i]

                    elif "reg" in prop.lower():
                        debugger.log_dbg(
                            color_text(
                                "--> [MEMORY]: Obtained capacity size (in MBs) of current RAM module! — (IOKit/Memory)",
                                "green",
                            )
                        )

                        key = "Capacity"
                        value = f"{sizes[i]}MB"

                    if key and value:
                        try:
                            modules[i][part_no[i]][key] = value
                        except Exception as e:
                            debugger.log_dbg(
                                color_text(
                                    "--> [MEMORY]: Couldn't properly determine information for current RAM module – critical! — (IOKit/Memory)"
                                    + f"\n\t^^^^^^^{str(e)}",
                                    "red",
                                )
                            )

                            self.logger.warning(
                                "Couldn't properly determine information for RAM modules (IOKit/MemInfo)",
                                __file__,
                            )

                            modules = []
                            break

        self.info["Memory"] = modules

    def net_info(self, default=True):

        if default:
            device = {
                "IOProviderClass": "IOPCIDevice",
                # Bit mask matching, ensuring that the 3rd byte is one of the network controller (0x02).
                "IOPCIClassMatch": "0x02000000&0xff000000",
            }
        else:
            device = {"IOProviderClass": "IOPlatformDevice"}

        debugger.log_dbg(
            color_text(
                "--> [Network]: Attempting to fetch list of NICs... — (IOKit)", "yellow"
            )
        )

        # Obtain generator instance, whose values are `CFDictionary`-ies
        interface = ioiterator_to_list(
            IOServiceGetMatchingServices(kIOMasterPortDefault, device, None)[1]
        )

        if interface:
            debugger.log_dbg(
                color_text(
                    "--> [Network]: Successfully obtained list of NICs! — (IOKit)",
                    "green",
                )
            )
        else:
            debugger.log_dbg(
                color_text(
                    "--> [Network]: Failed to obtain list of NICs – critical! — (IOKit)",
                    "red",
                )
            )

            return

        self.info["Network"] = []

        # Loop through the generator returned from `ioiterator_to_list()`
        for i in interface:
            data = {}
            model = {}

            # Obtain CFDictionaryRef of the current PCI device.
            device = corefoundation_to_native(
                IORegistryEntryCreateCFProperties(
                    i, None, kCFAllocatorDefault, kNilOptions
                )
            )[1]

            try:
                if default:
                    dev = "0x" + (
                        binascii.b2a_hex(
                            bytes(reversed(device.get("device-id")))
                        ).decode()[4:]
                    )
                    ven = "0x" + (
                        binascii.b2a_hex(
                            bytes(reversed(device.get("vendor-id")))
                        ).decode()[4:]
                    )

                    path = construct_pcip_osx(
                        i, device.get("acpi-path", ""), self.logger
                    )

                    pcip = path.get("PCI Path", "")
                    acpi = path.get("ACPI Path", "")

                    data = {
                        # Reverse the byte sequence, and format it using `binascii` – remove leading 0s
                        "Device ID": dev,
                        # Reverse the byte sequence, and format it using `binascii` – remove leading 0s
                        "Vendor": ven,
                    }

                    if pcip:
                        data["PCI Path"] = pcip

                    if acpi:
                        data["ACPI Path"] = acpi

                else:
                    if IOObjectConformsTo(i, b"IO80211Controller"):
                        model = {"device": device.get("IOModel")}

                        data = {
                            "IOClass": device.get("IOClass"),
                            "Vendor": device.get("IOVendor"),
                        }
            except Exception as e:
                debugger.log_dbg(
                    color_text(
                        "--> [Network]: Failed to obtain other information of NIC – critical! — (IOKit)"
                        + f"\n\t^^^^^^^{str(e)}",
                        "red",
                    )
                )

                self.logger.critical(
                    f"Failed to obtain vendor/device id for Network controller (IOKit)\n\t^^^^^^^^^{str(e)}",
                    __file__,
                )

                continue

            if self.offline and not model.get("device"):
                debugger.log_dbg(
                    color_text(
                        "--> [Network]: Model name of current NIC can't be obtained – ignoring! — (IOKit)",
                        "red",
                    )
                )

                model = {"device": "Unknown Network Controller"}
            else:
                if default:
                    try:
                        model = self.pci.get_item(dev[2:], ven[2:])
                    except Exception as e:
                        model = {"device": "Unknown Network Controller"}

                        debugger.log_dbg(
                            color_text(
                                "--> [Network]: Unable to obtain model name of current NIC – ignoring! — (IOKit)"
                                + f"\n\t^^^^^^^{str(e)}",
                                "red",
                            )
                        )

                        self.logger.warning(
                            f"Failed to obtain model for Network controller (IOKit) – Non-critical, ignoring",
                            __file__,
                        )

            if model:
                debugger.log_dbg(
                    color_text(
                        "--> [Network]: Successfully parsed information for current NIC! — (IOKit)",
                        "green",
                    )
                )

                model = model.get("device")

                self.info["Network"].append({model: data})

            IOObjectRelease(i)

        if default and self.vendor == "apple":
            return self.net_info(False)

    def audio_info(self, default=False):

        # TODO: implementation for Apple ARM64
        #       audio controllers.
        if self.vendor == "apple":
            return

        if default:
            _device = {
                "IOProviderClass": "IOPCIDevice",
                # Bit mask matching, ensuring that the 3rd byte is one of the multimedia controller (0x04).
                "IOPCIClassMatch": "0x04000000&0xff000000",
            }
        else:
            _device = {"IOProviderClass": "IOHDACodecDevice"}

        debugger.log_dbg(
            color_text(
                "--> [Audio]: Attempting to fetch list of Audio controllers... — (IOKit)",
                "yellow",
            )
        )

        # Obtain generator instance, whose values are `CFDictionary`-ies
        interface = ioiterator_to_list(
            IOServiceGetMatchingServices(kIOMasterPortDefault, _device, None)[1]
        )

        if interface:
            debugger.log_dbg(
                color_text(
                    "--> [Audio]: Successfully obtained list of Audio controllers! — (IOKit)",
                    "green",
                )
            )
        else:
            debugger.log_dbg(
                color_text(
                    "--> [Audio]: Failed to obtain list of Audio controllers! — (IOKit)",
                    "red",
                )
            )

            return

        self.info["Audio"] = []

        # Loop through the generator returned from `ioiterator_to_list()`
        for i in interface:

            # Obtain CFDictionaryRef of the current PCI device.
            device = corefoundation_to_native(
                IORegistryEntryCreateCFProperties(
                    i, None, kCFAllocatorDefault, kNilOptions
                )
            )[1]

            data = {}

            if not default:
                # Ensure it's the AppleHDACodec device
                if device.get("DigitalAudioCapabilities"):
                    debugger.log_dbg(
                        color_text(
                            "--> [Audio]: Invalid HDA codec device – ignoring! — (IOKit)",
                            "red",
                        )
                    )

                    continue

                try:
                    dev = "0x" + hex(device.get("IOHDACodecVendorID"))[6:]
                    ven = "0x" + hex(device.get("IOHDACodecVendorID"))[2:6]

                    data = {"Device ID": dev, "Vendor": ven}
                except Exception as e:
                    debugger.log_dbg(
                        color_text(
                            "--> [Audio]: Failed to obtain vendor/device ID of HDA codec device – critical! — (IOKit)"
                            + f"\n\t^^^^^^^{str(e)}",
                            "red",
                        )
                    )

                    self.logger.error(
                        "Failed to obtain vendor/device id of HDA codec device (IOKit)\n"
                        + f"\n\t^^^^^^^^^{str(e)}",
                        __file__,
                    )

                    continue

                if self.offline:
                    debugger.log_dbg(
                        color_text(
                            "--> [Audio]: Model name of HDA codec device can't be obtained – ignoring! — (IOKit)",
                            "red",
                        )
                    )

                    model = "N/A"
                else:
                    try:
                        model = self.pci.get_item(dev[2:], ven[2:]).get("device", "")
                    except Exception as e:
                        model = "N/A"

                        debugger.log_dbg(
                            color_text(
                                "--> [Audio]: Unable to obtain model name of HDA codec device – ignoring! — (IOKit)"
                                + f"\n\t^^^^^^^{str(e)}",
                                "red",
                            )
                        )

                        self.logger.warning(
                            f"Failed to obtain model for Sound Device (IOKit) – Non-critical, ignoring",
                            __file__,
                        )

            else:
                try:
                    # Reverse the byte sequence, and format it using `binascii` – remove leading 0s
                    dev = "0x" + (
                        binascii.b2a_hex(
                            bytes(reversed(device.get("device-id")))
                        ).decode()[4:]
                    )

                    # Reverse the byte sequence, and format it using `binascii` – remove leading 0s
                    ven = "0x" + (
                        binascii.b2a_hex(
                            bytes(reversed(device.get("vendor-id")))
                        ).decode()[4:]
                    )

                    data = {"Device ID": dev, "Vendor": ven}
                except Exception as e:
                    debugger.log_dbg(
                        color_text(
                            "--> [Audio]: Failed to obtain vendor/device ID of HDA codec device – critical! — (IOKit)"
                            + f"\n\t^^^^^^^{str(e)}",
                            "red",
                        )
                    )

                    self.logger.error(
                        "Failed to obtain vendor/device id of HDA codec device (IOKit)\n"
                        + f"\n\t^^^^^^^^^{str(e)}",
                        __file__,
                    )

                    continue

                if self.offline:
                    debugger.log_dbg(
                        color_text(
                            "--> [Audio]: Model name of HDA codec device can't be obtained – ignoring! — (IOKit)",
                            "red",
                        )
                    )

                    model = "N/A"
                else:
                    try:
                        model = self.pci.get_item(dev[2:], ven[2:]).get("device", "")
                    except Exception as e:
                        model = "N/A"

                        debugger.log_dbg(
                            color_text(
                                "--> [Audio]: Unable to obtain model name of HDA codec device – ignoring! — (IOKit)"
                                + f"\n\t^^^^^^^{str(e)}",
                                "red",
                            )
                        )

                        self.logger.warning(
                            f"Failed to obtain model for Sound Device (IOKit) – Non-critical, ignoring",
                            __file__,
                        )

            path = construct_pcip_osx(i, device.get("acpi-path", ""), self.logger)

            pcip = path.get("PCI Path", "")
            acpi = path.get("ACPI Path", "")

            if pcip:
                data["PCI Path"] = pcip

            if acpi:
                data["ACPI Path"] = acpi

            self.info["Audio"].append({model: data})

            IOObjectRelease(i)

        # If we don't find any AppleHDACodec devices (i.e. if it's a T2 Mac, try to find any multimedia controllers.)
        # This _will_ also fail on non-x86* architectures.
        #
        # See: https://en.wikipedia.org/wiki/Intel_High_Definition_Audio#Host_controller
        if not default:
            self.audio_info(True)

    def storage_info(self):

        debugger.log_dbg(
            color_text(
                "--> [Storage]: Attempting to fetch list of Storage devices... — (IOKit)",
                "yellow",
            )
        )

        device = {"IOProviderClass": "IOBlockStorageDevice"}

        interface = ioiterator_to_list(
            IOServiceGetMatchingServices(kIOMasterPortDefault, device, None)[1]
        )

        if interface:
            debugger.log_dbg(
                color_text(
                    "--> [Storage]: Successfully obtained list of Storage devices! — (IOKit)",
                    "green",
                )
            )
        else:
            debugger.log_dbg(
                color_text(
                    "--> [Storage]: Failed to obtain list of Storage devices! — (IOKit)",
                    "red",
                )
            )

            return

        self.info["Storage"] = []

        for i in interface:

            device = corefoundation_to_native(
                IORegistryEntryCreateCFProperties(
                    i, None, kCFAllocatorDefault, kNilOptions
                )
            )[1]

            product = device.get("Device Characteristics")
            protocol = device.get("Protocol Characteristics")

            if not product or not protocol:
                debugger.log_dbg(
                    color_text(
                        "--> [Storage]: Failed to obtain basic information of Storage device – critical! — (IOKit)",
                        "red",
                    )
                )

                continue

            try:
                debugger.log_dbg(
                    color_text(
                        "--> [Storage]: Attempting to obtain verbose information of Storage device... — (IOKit)",
                        "yellow",
                    )
                )

                # Name of the storage device.
                name = product.get("Product Name").strip()

                # Type of storage device (SSD, HDD, etc.)
                _type = product.get("Medium Type").strip()

                # Type of connector (SATA, USB, SCSI, etc.)
                ct_type = protocol.get("Physical Interconnect").strip()

                # Whether or not this device is internal or external.
                location = protocol.get("Physical Interconnect Location").strip()

                if ct_type.lower() == "pci-express":
                    _type = "Non-Volatile Memory Express (NVMe)"
                else:
                    _type = self.STORAGE.get(_type, _type)

                debugger.log_dbg(
                    color_text(
                        "--> [Storage]: Successfully obtained verbose information of Storage device! — (IOKit)",
                        "green",
                    )
                )
            except Exception as e:
                debugger.log_dbg(
                    color_text(
                        "--> [Storage]: Failed to obtain verbose information of Storage device – critical! — (IOKit)"
                        + f"\n\t^^^^^^^{str(e)}",
                        "red",
                    )
                )

                self.logger.error(
                    "Failed to construct valid format for storage device (IOKit)"
                    + f"\n\t^^^^^^^^^{str(e)}",
                    __file__,
                )

                continue

            self.info["Storage"].append(
                {name: {"Type": _type, "Connector": ct_type, "Location": location}}
            )

            IOObjectRelease(i)

    def input_info(self):

        debugger.log_dbg(
            color_text(
                "--> [Input]: Attempting to obtain list of Input devices... — (IOKit)",
                "yellow",
            )
        )

        device = {"IOProviderClass": "IOHIDDevice"}

        interface = ioiterator_to_list(
            IOServiceGetMatchingServices(kIOMasterPortDefault, device, None)[1]
        )

        if interface:
            debugger.log_dbg(
                color_text(
                    "--> [Input]: Successfully obtained list of Input devices! — (IOKit)",
                    "green",
                )
            )
        else:
            debugger.log_dbg(
                color_text(
                    "--> [Input]: Failed to obtain list of Input devices – critical! — (IOKit)",
                    "red",
                )
            )

            return

        self.info["Input"] = []

        for i in interface:

            device = corefoundation_to_native(
                IORegistryEntryCreateCFProperties(
                    i, None, kCFAllocatorDefault, kNilOptions
                )
            )[1]

            name = device.get("Product", "")
            hid = device.get("Transport", "")

            if not name:
                debugger.log_dbg(
                    color_text(
                        "--> [Input]: Failed to obtain basic information of Input device... — (IOKit)",
                        "red",
                    )
                )

                continue

            if hid:
                debugger.log_dbg(
                    color_text(
                        "--> [Input]: Succesfully obtained transport information of Input device! — (IOKit)",
                        "green",
                    )
                )

                hid = " (" + hid + ")"
            else:
                debugger.log_dbg(
                    color_text(
                        "--> [Input]: Failed to obtain transport information of Input device – ignoring! — (IOKit)",
                        "red",
                    )
                )

            if any("{}{}".format(name, hid) in k for k in self.info["Input"]):
                continue

            try:
                dev = hex(device.get("ProductID"))
                ven = hex(device.get("VendorID"))

                data = {"Device ID": dev, "Vendor": ven}
            except Exception as e:
                debugger.log_dbg(
                    color_text(
                        "--> [Input]: Failed to obtain vendor/device ID of Input device – ignoring! — (IOKit)"
                        + f"\n\t^^^^^^^{str(e)}",
                        "red",
                    )
                )

                self.logger.error(
                    "Failed to obtain vendor/device id for Input device (IOKit)"
                    + f"\n\t^^^^^^^^^{str(e)}",
                    __file__,
                )

                data = {}

            name = "{}{}".format(name, hid)

            self.info["Input"].append({name: data})

            IOObjectRelease(i)

    def display_info(self):

        debugger.log_dbg(
            color_text(
                "--> [Display]: Attempting to obtain information about the current displays... — (IOKit)",
                "yellow",
            )
        )

        device = {"IOProviderClass": "IODisplay"}

        interface = ioiterator_to_list(
            IOServiceGetMatchingServices(kIOMasterPortDefault, device, None)[1]
        )

        if not interface:
            debugger.log_dbg(
                color_text(
                    "--> [Display]: Failed to obtain list of Display devices – critical! — (IOKit)",
                    "red",
                )
            )

            return

        debugger.log_dbg(
            color_text(
                "--> [Display]: Successfully obtained list of Display devices! — (IOKit)",
                "green",
            )
        )

        self.info["Displays"] = []

        for i in interface:
            device = corefoundation_to_native(
                IORegistryEntryCreateCFProperties(
                    i, None, kCFAllocatorDefault, kNilOptions
                )
            )[1]

            edid = bytes(device.get("IODisplayEDID", ""))
            const_h = b"\x00\xFF\xFF\xFF\xFF\xFF\xFF\x00"

            # Verify header integrity
            if edid[0x0:0x8] != const_h:
                debugger.log_dbg(
                    color_text(
                        f"--> [Display]: Failed to verify file integrity for Display device's EDID data! Skipping... — (IOKit)",
                        "yellow",
                    )
                )
                continue

            connector_t = {
                0x01: "DUMMY",
                0x02: "LVDS/eDP",
                0x04: "DVI (Dual Link)",
                0x10: "VGA",
                0x80: "S-Video",
                0x200: "DVI (Single Link)",
                0x400: "DisplayPort",
                0x800: "HDMI",
            }

            product = hex(int(device.get("DisplayProductID", "")))
            vendor = hex(int(device.get("DisplayVendorID", "")))
            serial = device.get("DisplaySerialNumber", "")
            plane = device.get("IODisplayPrefsKey", "")
            parent = ""
            gpus = self.info["GPU"]
            ver_rev = (edid[0x12], edid[0x13])
            name = "UNKNOWN DISPLAY DEVICE"

            connector_obj = IORegistryEntrySearchCFProperty (
                i,
                "IOService".encode(),
                "connector-type",
                kCFAllocatorDefault,
                kIORegistryIterateRecursively | kIORegistryIterateParents
            )

            if not connector_obj:
                continue

            connector = connector_t.get(connector_obj, "UNKNOWN CONNECTOR")

            CFRelease (connector_obj)

            # Horizontal —  first value
            # Vertical   —  second value
            # Portrait   —  third value indicating whether
            #               or not the current display is in portait mode.
            #                   0 = Landscape
            #                   1 = Portrait
            #                  -1 = Unknown resolution/dimensions
            res = (0, 0, 0)
            ratios = {0: [16, 10], 1: [4, 3], 2: [5, 4], 3: [16, 9]}
            ratio = ratios[
                int(str((edid[0x27] >> 6) & 1) + str((edid[0x27] >> 7) & 1), 2)
            ]

            # Dimensions of the display in cm.
            horizontal = edid[0x15]
            vertical = edid[0x16]

            # Screen size in inches.
            screen_size = math.floor(
                round(math.sqrt((horizontal**2) + (vertical**2)) * 0.393701)
            )

            if screen_size:
                debugger.log_dbg(
                    color_text(
                        f"--> [Display]: Successfully detected screen size of {screen_size}”! — (IOKit)",
                        "green",
                    )
                )

            # Aspect ratio.
            aspect_rat = ratio[0] / ratio[1]

            # Vertical addressable video in lines.
            #
            # Also known as, “vertical resolution”.
            ver_adr_vid = ((edid[0x3D] & 0xF0) << 4) | edid[0x3B]

            # Horizontal resolution
            #
            # Source: https://glenwing.github.io/docs/VESA-EEDID-A2.pdf
            #       Thank me for the pain later.
            hor_adr_vid = 8 * math.floor((ver_adr_vid * aspect_rat) / 8)

            # If both bytes are equal to 0,
            # then aspect ratio and screen size
            # are undefined.
            if horizontal == 0 and vertical == 0:
                res = (0, 0, -1)

            # Display is in Landscape mode.
            elif horizontal != 0:
                res = (hor_adr_vid, ver_adr_vid, 0)

            # Display is in Portrait mode.
            elif vertical != 0:
                ratio.reverse()

                res = (ver_adr_vid, hor_adr_vid, 1)

            if ratio:
                debugger.log_dbg(
                    color_text(
                        f"--> [Display]: Successfully detected aspect ratio of {ratio[0]}:{ratio[1]}! — (IOKit)",
                        "green",
                    )
                )

            if res != (0, 0, -1):
                debugger.log_dbg(
                    color_text(
                        f"--> [Display]: Successfully detected {res[0]}x{res[1]} resolution in {'Portrait' if res[-1] else 'Landscape'} mode! — (IOKit)",
                        "green",
                    )
                )

            else:
                debugger.log_dbg(
                    color_text(
                        "--> [Display]: Failed to detect resolution data for Display device. (IOKit)",
                        "yellow",
                    )
                )

            # Ranges of possible monitor descriptors
            # for EDID v1.3 and EDID v1.4
            #
            # See more:
            #   - https://glenwing.github.io/docs/VESA-EEDID-A1.pdf
            #   - https://glenwing.github.io/docs/VESA-EEDID-A2.pdf
            ranges = [(0x48, 0x59), (0x5A, 0x6B), (0x6C, 0x7D)]

            if ver_rev == (1, 3) or ver_rev == (1, 4) or ver_rev == (2, 0):
                for (start, end) in ranges:
                    if b"\xFC" in edid[start : start + 4]:
                        name = (
                            edid[start + 5 : end]
                            + (b"\x0A\x20" if len(edid[start + 5 : end]) < 13 else b"")
                        ).decode()

                        name = name.replace("\n", "").replace(" ", "")

            for gpu in gpus:
                for key in gpu.keys():
                    debugger.log_dbg(
                        color_text(
                            f"--> [Display]: Attempting to find information about parent for {vendor}:{product}... — (IOKit)",
                            "yellow",
                        )
                    )

                    acpi = gpu[key].get("ACPI Path", "").replace("\\_SB.", "")
                    correct = 0

                    parts = acpi.split(".")

                    for part in parts:
                        if part.lower() in plane.lower():
                            correct += 1

                    if int((correct * 100) / len(parts)) > 50:
                        parent = f"({key})"

                if parent:
                    debugger.log_dbg(
                        color_text(
                            "--> [Display]: Successfully found information about parent for Display device! — (IOKit)",
                            "green",
                        )
                    )

                else:
                    debugger.log_dbg(
                        color_text(
                            "--> [Display]: Failed to find information about parent for Display device! — (IOKit)",
                            "red",
                        )
                    )

                self.info["Displays"].append(
                    {
                        f"{name} {parent}": {
                            "Product ID": product,
                            "Vendor ID": vendor,
                            "Serial": hex(serial),
                            "Resolution": f"{res[0]}x{res[1]}",
                            "Size (in inches)": f"{screen_size}”",
                            "Display mode": "Portrait" if res[-1] else "Landscape",
                            "Connector": connector,
                            "Aspect ratio": f"{ratio[0]}:{ratio[1]}",
                        }
                    }
                )

            IOObjectRelease(i)
