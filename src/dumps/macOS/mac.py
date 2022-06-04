import binascii
import subprocess
from src.dumps.macOS.ioreg import *
from src.error.cpu_err import cpu_err
from src.util.codename import gpu
from src.util.codename_manager import CodenameManager
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
            self.cpu_info()
        if (
            (not "Vendor" in self.off_data or
             not "Motherboard" in self.off_data) and
            not self.info.get("Vendor", {})
        ):
            self.vendor_info()
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

    def cpu_info(self):
        try:
            # Model of the CPU
            model = (
                subprocess.check_output(["sysctl", "machdep.cpu.brand_string"])
                .decode()
                .split(": ")[1]
                .strip()
            )

            self.cpu["model"] = model
        except Exception as e:
            self.logger.critical(
                f"Failed to obtain CPU information. This should not happen. \n\t^^^^^^^^^{str(e)}",
                __file__,
            )
            cpu_err(e)

        self.info["CPU"] = []

        if ".vendor" in subprocess.check_output(["sysctl", "machdep.cpu"]).decode():
            try:
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
            except Exception as e:
                self.logger.warning(
                    f"Failed to access CPUID instruction – ({model})\n\t^^^^^^^^^{str(e)}",
                    __file__,
                )
                self.vendor = None
                features = None
        else:
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
            VENDOR = corefoundation_to_native(
                IORegistryEntryCreateCFProperties(
                    next(
                        ioiterator_to_list(
                            IOServiceGetMatchingServices(
                                kIOMasterPortDefault,
                                IOServiceMatching(b"IOPlatformExpertDevice"),
                                None
                            )[1]
                        )
                    ),
                    None,
                    kCFAllocatorDefault,
                    kNilOptions
                )
            )[1]

            model = VENDOR.get("model").decode().replace("\x00", "")
            manuf = VENDOR.get("manufacturer").decode().replace("\x00", "")

            self.info["Vendor"] = {
                "Model": model,
                "Manufacturer": manuf
            }
        except Exception:
            self.logger.warning(
                f"Failed to obtain vendor model/manufacturer for machine – Non-critical, ignoring.",
                __file__
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

        # Obtain generator instance, whose values are `CFDictionary`-ies
        interface = ioiterator_to_list(
            IOServiceGetMatchingServices(
                kIOMasterPortDefault, device, None
            )[1]
        )
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
                    not default and

                    # If both return true, that means
                    # we aren't dealing with a GPU device.
                    not "gpu" in device.get("IONameMatched", "").lower() and
                    not "AGX" in device.get("CFBundleIdentifierKernel", "")
                ):
                    continue
            except Exception:
                continue

            try:
                model = device.get("model", None)

                if not model:
                    continue

                if default:
                    model = bytes(model).decode()
                    model = model[0: len(model) - 1]
            except Exception as e:
                self.logger.error(
                    "Failed to obtain GPU device model (IOKit)"
                    + f"\n\t^^^^^^^^^{str(e)}",
                    __file__,
                )
                continue

            try:
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

                    data["Cores"] = (
                        str(gpuconf.get("num_cores")) + " Cores")
                    data["NE Cores"] = (str(gpuconf.get(
                        "num_gps")) + " Neural Engine Cores") if gpuconf.get("num_mgpus") else None
                    data["Generation"] = (
                        "Generation " + str(gpuconf.get("gpu_gen"))) if gpuconf.get("gpu_gen") else None

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
                        i, device.get("acpi-path", ""), self.logger)

                    pcip = path.get("PCI Path", "")
                    acpi = path.get("ACPI Path", "")

                    if pcip:
                        data["PCI Path"] = pcip

                    if acpi:
                        data["ACPI Path"] = acpi
            except Exception as e:
                self.logger.error(
                    "Failed to obtain vendor/device id for GPU device (IOKit)"
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

        if self.vendor == "apple":
            return

        # Special thanks to [Flagers](https://github.com/flagersgit) for this.
        #
        # Source: https://github.com/KernelWanderers/OCSysInfo/pull/10
        interface = corefoundation_to_native(
            IORegistryEntryCreateCFProperties(
                IORegistryEntryFromPath(
                    kIOMasterPortDefault, b"IODeviceTree:/memory"
                ),
                None,
                kCFAllocatorDefault,
                kNilOptions,
            )[1]
        )

        self.info["Memory"] = []
        modules = []
        part_no = []
        sizes = []
        length = None

        for prop in interface:
            val = interface[prop]

            if type(val) == bytes:
                if "reg" in prop.lower() and length:
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
                        self.logger.warning(
                            f"Failed to decode bytes for RAM module (IOKit/MemInfo)\n\t^^^^^^^^^{str(e)}",
                            __file__,
                        )
                        continue

            if "part-number" in prop:
                length = len(val)

                for i in range(length):
                    modules.append({f"{val[i]} (Part-Number)": {}})
                    part_no.append(f"{val[i]} (Part-Number)")

            else:
                if not length:
                    return

                for i in range(length):
                    key = ""
                    value = None

                    if "dimm-types" in prop.lower():
                        key = "Type"
                        value = val[i]

                    elif "slot-names" in prop.lower():
                        key = "Slot"
                        try:
                            bank, channel = val[i].split("/")

                            value = {"Bank": bank, "Channel": channel}
                        except Exception as e:
                            self.logger.error(
                                f"Failed to obtain BANK/Channel values for RAM module! (IOKit/MemInfo)\n\t^^^^^^^^^{str(e)}",
                                __file__,
                            )

                    elif "dimm-speeds" in prop.lower():
                        key = "Frequency (MHz)"
                        value = val[i]

                    elif "dimm-manufacturer" in prop.lower():
                        key = "Manufacturer"
                        value = val[i]

                    elif "reg" in prop.lower():
                        key = "Capacity"
                        value = f"{sizes[i]}MB"

                    if key and value:
                        try:
                            modules[i][part_no[i]][key] = value
                        except Exception:
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

        # Obtain generator instance, whose values are `CFDictionary`-ies
        interface = ioiterator_to_list(
            IOServiceGetMatchingServices(
                kIOMasterPortDefault, device, None
            )[1]
        )
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
                        binascii.b2a_hex(bytes(reversed(device.get("device-id")))).decode()[
                            4:
                        ]
                    )
                    ven = "0x" + (
                        binascii.b2a_hex(bytes(reversed(device.get("vendor-id")))).decode()[
                            4:
                        ]
                    )

                    path = construct_pcip_osx(
                        i, device.get("acpi-path", ""), self.logger)

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
                    if IOObjectConformsTo(i, b'IO80211Controller'):
                        model = {"device": device.get("IOModel")}

                        data = {
                            "IOClass": device.get("IOClass"),
                            "Vendor": device.get("IOVendor")
                        }
            except Exception as e:
                self.logger.critical(
                    f"Failed to obtain vendor/device id for Network controller (IOKit)\n\t^^^^^^^^^{str(e)}",
                    __file__,
                )
                continue

            if self.offline and not model.get("device"):
                model = {"device": "Unknown Network Controller"}
            else:
                if default:
                    try:
                        model = self.pci.get_item(dev[2:], ven[2:])
                    except Exception:
                        model = {"device": "Unknown Network Controller"}

                        self.logger.warning(
                            f"Failed to obtain model for Network controller (IOKit) – Non-critical, ignoring",
                            __file__,
                        )

            if model:
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

        # Obtain generator instance, whose values are `CFDictionary`-ies
        interface = ioiterator_to_list(
            IOServiceGetMatchingServices(
                kIOMasterPortDefault, _device, None
            )[1]
        )
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
                    continue

                try:
                    dev = "0x" + hex(device.get("IOHDACodecVendorID"))[6:]
                    ven = "0x" + hex(device.get("IOHDACodecVendorID"))[2:6]

                    data = {"Device ID": dev, "Vendor": ven}
                except Exception as e:
                    self.logger.error(
                        "Failed to obtain vendor/device id of HDA codec device (IOKit)\n"
                        + f"\n\t^^^^^^^^^{str(e)}",
                        __file__,
                    )
                    continue

                if self.offline:
                    model = "N/A"
                else:
                    try:
                        model = self.pci.get_item(
                            dev[2:], ven[2:]).get("device", "")
                    except Exception:
                        model = "N/A"

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
                    self.logger.error(
                        "Failed to obtain vendor/device id of HDA codec device (IOKit)\n"
                        + f"\n\t^^^^^^^^^{str(e)}",
                        __file__,
                    )
                    continue

                if self.offline:
                    model = "N/A"
                else:
                    try:
                        model = self.pci.get_item(
                            dev[2:], ven[2:]).get("device", "")
                    except Exception:
                        model = "N/A"

                        self.logger.warning(
                            f"Failed to obtain model for Sound Device (IOKit) – Non-critical, ignoring",
                            __file__,
                        )

            path = construct_pcip_osx(
                i, device.get("acpi-path", ""), self.logger)

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

        device = {"IOProviderClass": "IOBlockStorageDevice"}

        interface = ioiterator_to_list(
            IOServiceGetMatchingServices(
                kIOMasterPortDefault, device, None
            )[1]
        )
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
                continue

            try:
                # Name of the storage device.
                name = product.get("Product Name").strip()
                # Type of storage device (SSD, HDD, etc.)
                _type = product.get("Medium Type").strip()

                # Type of connector (SATA, USB, SCSI, etc.)
                ct_type = protocol.get("Physical Interconnect").strip()
                # Whether or not this device is internal or external.
                location = protocol.get(
                    "Physical Interconnect Location").strip()

                if ct_type.lower() == "pci-express":
                    _type = "Non-Volatile Memory Express (NVMe)"
                else:
                    _type = self.STORAGE.get(_type, _type)
            except Exception as e:
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
        device = {"IOProviderClass": "IOHIDDevice"}

        interface = ioiterator_to_list(
            IOServiceGetMatchingServices(
                kIOMasterPortDefault, device, None
            )[1]
        )
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
                continue

            if hid:
                hid = " (" + hid + ")"

            if any("{}{}".format(name, hid) in k for k in self.info["Input"]):
                continue

            try:
                dev = hex(device.get("ProductID"))
                ven = hex(device.get("VendorID"))

                data = {"Device ID": dev, "Vendor": ven}
            except Exception as e:
                self.logger.error(
                    "Failed to obtain vendor/device id for Input device (IOKit)"
                    + f"\n\t^^^^^^^^^{str(e)}",
                    __file__,
                )
                data = {}

            name = "{}{}".format(name, hid)

            self.info["Input"].append({name: data})

            IOObjectRelease(i)
