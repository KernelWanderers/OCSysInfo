import os
import re
import subprocess
from src.error.cpu_err import cpu_err
from src.util.codename import gpu
from src.util.pci_root import pci_from_acpi_linux
from src.util.codename_manager import CodenameManager
from .dmi_decode import get_string_entry, MEMORY_TYPE


class LinuxHardwareManager:
    """
    Instance, implementing `DeviceManager`, for extracting system information
    from Linux using the `sysfs` pseudo file system.

    https://www.kernel.org/doc/html/latest/admin-guide/sysfs-rules.html
    """

    def __init__(self, parent):
        self.info = parent.info
        self.pci = parent.pci
        self.logger = parent.logger

    def dump(self):
        self.cpu_info()
        self.mobo_info()
        self.gpu_info()
        self.mem_info()
        self.net_info()
        self.audio_info()
        self.input_info()
        self.block_info()

    def cpu_info(self):
        try:
            cpus = open("/proc/cpuinfo", "r").read()
        except Exception as e:
            self.logger.critical(
                f"Failed to obtain CPU information. This should not happen. \n\t^^^^^^^^^{str(e)}",
                __file__,
            )
            cpu_err(e)

        cpu = cpus.split("\n\n")

        if not cpu:
            return

        cpu = cpu[0]  # Get only the first CPU identifier.

        model = re.search(r"(?<=model name\t\: ).+(?=\n)", cpu)
        flagers = re.search(r"(?<=flags\t\t\: ).+(?=\n)", cpu)
        cores = re.search(r"(?<=cpu cores\t\: ).+(?=\n)", cpu)
        vendor = None

        data = {}

        if model:
            model = model.group()
            data = {model: {}}
            vendor = "intel" if "intel" in model.lower() else "amd"
        else:
            self.logger.critical(
                "Failed to obtain basic CPU information (PROC_FS)", __file__
            )
            exit(0)

        if flagers:
            flagers = flagers.group()

            # List of supported SSE instructions.
            data[model]["SSE"] = list(
                sorted(
                    [
                        flag.replace("_", ".")
                        for flag in flagers.split(" ")
                        if "sse" in flag.lower() and not "ssse" in flag.lower()
                    ],
                    reverse=True,
                )
            )[0].upper()
            data[model]["SSSE3"] = (
                "Supported" if "ssse3" in flagers else "Not Available"
            )

        if cores:
            data[model]["Cores"] = cores.group()

        try:
            # Count the amount of times 'processor'
            # is matched, since threads are enumerated
            # individually.
            data[model]["Threads"] = (
                open("/proc/cpuinfo", "r").read().count("processor")
            )
        except Exception as e:
            self.logger.error(
                f"Failed to resolve thread count for {model} (PROC_FS)\n\t^^^^^^^^^{str(e)}",
                __file__,
            )
            pass

        self.cnm = CodenameManager(model, vendor)

        if self.cnm.codename:
            data[model]["Codename"] = self.cnm.codename

        self.info.get("CPU").append(data)

    def gpu_info(self):

        # Because DD wanted this for WSL*.
        if not os.path.exists("/sys/class/drm"):
            return

        for file in os.listdir("/sys/class/drm/"):

            # DRM devices (not FBDev) are enumerated with the format `cardX`
            # inside of sysfs's DRM directory. So we look for those, and traverse
            # them. We look for the `device` and `vendor` file, which should always be there.
            if "card" in file and not "-" in file:
                path = f"/sys/class/drm/{file}/device"
                data = {}

                try:
                    ven = open(f"{path}/vendor", "r").read().strip()
                    dev = open(f"{path}/device", "r").read().strip()

                    model = self.pci.get_item(dev[2:], ven[2:]).get("device")

                    data = {"Device ID": dev, "Vendor": ven}
                except Exception as e:
                    self.logger.warning(
                        f"Failed to obtain vendor/device id for GPU device (SYS_FS/DRM)\n\t^^^^^^^^^{str(e)}",
                        __file__,
                    )
                    continue

                try:
                    pcir = pci_from_acpi_linux(path, self.logger)

                    if pcir:
                        acpi = pcir.get("ACPI Path")
                        pcip = pcir.get("PCI Path")

                        if acpi:
                            data["ACPI Path"] = acpi

                        if pcip:
                            data["PCI Path"] = pcip
                except Exception as e:
                    self.logger.error(
                        f"Failed during ACPI/PCI path construction (SYS_FS/DRM)\n\t^^^^^^^^^{str(e)}"
                    )

                gpucname = gpu(dev, ven)

                if gpucname:
                    data["Codename"] = gpucname

                self.info.get("GPU").append({model: data})

    # Special thanks to the following individuals:
    #
    #   - [Quist](https://github.com/nadiaholmquist)
    #   - [Flagers](https://github.com/flagersgit)
    #   - [Joshj23](https://github.com/joshj23)
    #   - [Rusty bits](https://github.com/rusty-bits)
    #
    # for contributing greatly to this portion.
    #
    # It wouldn't even exist without them.
    def mem_info(self):
        print(
            "\nWe apologise for the inconvenience, but we really need you to run this specific call as sudo."
        )
        print("It's for extracting information about your system's RAM modules.")
        print("It's simply running: 'sudo cat /sys/firmware/dmi/entries/17-*/raw'\n")
        response = input(
            "You can feel free to respond with 'N' if you don't wish to proceed with this! Or 'Y' if you do: "
        )

        if "y" in response.lower():

            # DMI table dump of memory slot entries.
            #
            # Type 17 indicates a memory slot device.
            parent_dir = [
                p
                for p in os.scandir("/sys/firmware/dmi/entries")
                if "17-" in p.path.split("/")[-1]
            ]

            for child_dir in parent_dir:

                # The contents of the binary file.
                value = subprocess.check_output(
                    [
                        "sudo",
                        "cat",
                        f"{child_dir.path}/raw",
                    ]
                )
                data = {}
                part_no = ""

                if "dimm" in value.upper().decode("latin-1").strip().lower():
                    length_field = value[0x1]
                    strings = value[length_field : len(value)].split(b"\0")

                    try:
                        """
                        ---------------------
                        |    Part Number    |
                        ---------------------
                        
                        Obtains the value at offset 1Ah, which indicates at which index, pre-sanitisation,
                        in the `strings` list the real string value is stored.
                        
                        Which is: `strings[value[0x1A] - 1]`, after obtaining it, it decodes it to `ascii`.
                        
                        Special thanks to [Quist](https://github.com/nadiaholmquist) for this.
                        """
                        part_no = get_string_entry(strings, value[0x1A]).strip() + " (Part Number)"
                        data[part_no] = {}
                    except Exception as e:
                        self.logger.warning(
                            f"Unable to determine part number for memory (RAM) module (SYS_FS/DMI)\n\t^^^^^^^^^{str(e)}",
                            __file__,
                        )
                        continue
                    
                    try:
                        # The type value is stored at offset 12h
                        type = MEMORY_TYPE[value[0x12]]
                        
                        data[part_no]["Type"] = type
                    except Exception as e:
                        self.logger.warning(
                            f"Unable to determine type of memory (RAM) module (SYS_FS/DMI)\n\t^^^^^^^^{str(e)}",
                            __file__,
                        )
                        data[part_no]["Type"] = "UNKNOWN"

                    try:
                        # Explanation same as for Part Number.
                        channel = get_string_entry(strings, value[0x10])
                        bank = get_string_entry(strings, value[0x11])

                        data[part_no]["Slot"] = {"Channel": channel, "Bank": bank}
                    except Exception as e:
                        self.logger.warning(
                            f"Unable to determine slot location for memory (RAM) module (SYS_FS/DMI)\n\t^^^^^^^^^{str(e)}",
                            __file__,
                        )
                        continue

                    try:
                        # Explanation same as for Part Number.
                        manufacturer = get_string_entry(strings, value[0x17])

                        data[part_no]["Manufacturer"] = manufacturer
                    except Exception as e:
                        self.logger.warning(
                            f"Unable to determine manufacturer for memory (RAM) module (SYS_FS/DMI)\n\t^^^^^^^^^^^^{str(e)}",
                            __file__,
                        )
                        continue

                    try:
                        """
                        ---------------------
                        |      CAPACITY     |
                        ---------------------

                        Looks at the 2 bytes at offset 0Ch to hopefully determine its size;
                        in case the of these 2 bytes is equal to 0x7FFF, it looks at the 4 bytes
                        at offset 1Ch.

                        In the case that the value at offset 0Ch is equal to 0xFFFF,
                        it would mean that the size is unknown.
                        """

                        """
                        2 bytes, at offset 0Ch
                        
                        We convert it into an integer from the bytes values, specifying
                        that it is in LE (little endian) format.
                        
                        Meaning, it will properly accommodate the values to represent its BE (big endian)
                        value in the end.
                        
                        For example,
                            (  Little  )  (   Big   )
                            '\x00\x10' -> '\x10\x00'
                            
                        Finally, '\x10\x00' will yield `4096` in decimal (0x1000 in hexadecimal);
                        which is correct. This was done on a system with 4x4GB memory modules.
                        
                        Aka, 4x4096MB modules, in this case--since the 15th bit value is `0`, 
                        meaning it's represented in MB, and not KB.
                        """
                        size = int.from_bytes(value[0x0C:0x0E], "little")

                        if size == 0xFFFF:
                            data["Capacity"] = "UNKNOWN SIZE"

                        # In cases where the individual memory module's
                        # capacity is `n >= (32GB-1MB)`, the value at 0Ch
                        # will be `0x7FFF`; meaning we should look at 1Ch instead.
                        elif size == 0x7FFF:
                            # 4 bytes, at offset 1Ch
                            size = int(
                                "".join(reversed(value.hex()[0x1C : 0x1C + 0x4])), 16
                            )

                        # Whether or not the value is represented in KB or MB
                        #
                        # 0 - MB
                        # 1 - KB
                        rep = "MB" if (size >> 15) & 1 == 0 else "KB"

                        data[part_no]["Capacity"] = f"{size}{rep}"
                    except Exception as e:
                        self.logger.warning(
                            f"Unable to determine size for memory (RAM) module (SYS_FS/DMI)\n\t^^^^^^^^^{str(e)}",
                            __file__,
                        )
                        continue

                self.info["Memory"].append(data)
        else:
            print("Cancelled, bailing memory detection...")

    def net_info(self):
        for file in os.listdir("/sys/class/net"):
            path = f"/sys/class/net/{file}/device"
            data = {}

            # We ensure that the enumerated directory in the sysfs net
            # directory is a valid card, since it'll contain a `vendor` and
            # `device` file.
            if os.path.isfile("{}/device".format(path)):
                try:
                    ven = open(f"{path}/vendor", "r").read().strip()
                    dev = open(f"{path}/device", "r").read().strip()

                    data = {"Device ID": dev, "Vendor": ven}

                    model = self.pci.get_item(dev[2:], ven[2:]).get("device")
                except Exception as e:
                    self.logger.error(
                        f"Failed to obtain vendor/device id for Network controller (SYS_FS/NET)\n\t^^^^^^^^^{str(e)}",
                        __file__,
                    )
                    return

                try:
                    pcir = pci_from_acpi_linux(path, self.logger)

                    if pcir:
                        acpi = pcir.get("ACPI Path")
                        pcip = pcir.get("PCI Path")

                        if acpi:
                            data["ACPI Path"] = acpi

                        if pcip:
                            data["PCI Path"] = pcip
                except Exception as e:
                    self.logger.error(
                        f"Failed during ACPI/PCI path construction (SYS_FS/NET)\n\t^^^^^^^^^{str(e)}"
                    )

                else:
                    self.info.get("Network").append({model: data})

    def audio_info(self):
        for file in os.listdir("/sys/class/sound"):

            # Sound devices are enumerated similarly to DRM devices,
            # with the format `cardX`, so we look for those, and look
            # for `vendor` and `device` files.
            if "card" in file.lower() and not "-" in file.lower():
                path = f"/sys/class/sound/{file}/device"
                data = {}

                try:
                    ven = open(f"{path}/vendor", "r").read().strip()
                    dev = open(f"{path}/device", "r").read().strip()

                    data = {"Device ID": dev, "Vendor": ven}
                    model = self.pci.get_item(dev[2:], ven[2:]).get("device")
                except Exception as e:
                    self.logger.warning(
                        f"Failed to obtain vendor/device id for Audio controller (SYS_FS/SOUND)\n\t^^^^^^^^^{str(e)}",
                        __file__,
                    )
                    continue

                try:
                    pcir = pci_from_acpi_linux(f"{path}", self.logger)

                    if pcir:
                        acpi = pcir.get("ACPI Path")
                        pcip = pcir.get("PCI Path")

                        if acpi:
                            data["ACPI Path"] = acpi

                        if pcip:
                            data["PCI Path"] = pcip
                except Exception as e:
                    self.logger.error(
                        f"Failed during ACPI/PCI path construction (SYS_FS/SOUND)\n\t^^^^^^^^^{str(e)}"
                    )

                try:
                    dirs = [n for n in os.listdir(path) if "hdaudio" in n.lower()]

                    for dir in dirs:
                        chip_name = open(f"{path}/{dir}/chip_name", "r").read().strip()

                        if "alc" in chip_name.lower():
                            data["ALC Codec"] = chip_name
                except Exception as e:
                    self.logger.warning(
                        f"Failed to obtain ALC codec for Audio controller (SYS_FS/SOUND)\n\t^^^^^^^^^{str(e)}"
                    )

                else:
                    self.info.get("Audio").append({model: data})

    def mobo_info(self):

        # Details about the motherboard is
        # located in /sys/devices/virtual/dmi/id
        #
        # So we simply look for `board_name` and
        # `board_vendor` to extract its model name,
        # and its vendor's name.
        try:
            path = "/sys/devices/virtual/dmi/id"

            model = open(f"{path}/board_name", "r").read().strip()
            vendor = open(f"{path}/board_vendor", "r").read().strip()
        except Exception as e:
            self.logger.critical(
                f"Failed to obtain Motherboard details (SYS_FS/DMI)\n\t^^^^^^^^^{str(e)}",
                __file__,
            )
            return

        if model:
            data = {"Model": model}

            if vendor:
                data["Vendor"] = vendor

            self.info["Motherboard"] = data

    def input_info(self):

        # This is the simplest way of reliably
        # obtaining the path of the input devices
        # located in sysfs. Ironically, by looking
        # into procfs.
        #
        # Out of the things we look for,
        # it contains the device name, and its sysfs path.
        try:
            devices = open("/proc/bus/input/devices", "r").read().strip()
            sysfs = []
        except Exception as e:
            self.logger.critical(
                f"Failed to obtain Input devices (SYS_FS/INPUT) — THIS GENERALLY SHOULD NOT HAPPEN ON LAPTOP DEVICES.\n\t^^^^^^^^^{str(e)}",
                __file__,
            )
            return

        for device in devices.split("\n\n"):
            for line in device.split("\n"):
                if "sysfs" in line.lower():
                    sysfs.append("/sys{}".format(line.split("=")[1]))

        for path in sysfs:
            # RMI4 devices, probably SMBus
            # TODO: I2C RMI4 devices
            if "rmi4" in path.lower():
                # Check for passed-through devices like trackpad
                if "fn" in path:
                    continue

                if (not os.path.isfile(f"{path}/name")) or (
                    not os.path.isfile(f"{path}/id/vendor")
                ):
                    self.logger.warning(
                        "Failed to identify device using the RMI4 protocol (SYS_FS/INPUT) – Non-critical, ignoring",
                        __file__,
                    )
                    continue

                try:
                    prod_id = open(f"{path}/name", "r").read().strip()
                    vendor = open(f"{path}/id/vendor", "r").read().strip()
                except Exception as e:
                    self.logger.error(
                        f"Failed to obtain product/vendor id of device using the RMI4 protocol (SYS_FS/INPUT) – Non-critical, ignoring\n\t^^^^^^^^^{str(e)}",
                        __file__,
                    )
                    continue

                self.info["Input"].append(
                    {
                        "Synaptics SMbus Trackpad": {
                            "Device ID": prod_id,
                            "Vendor": vendor,
                        }
                    }
                )

            # PS2 devices
            if "i8042" in path.lower():
                if not os.path.isfile(f"{path}/name"):
                    self.logger.warning(
                        "Failed to identify PS2 device (SYS_FS/INPUT) – Non-critical, ignoring",
                        __file__,
                    )
                    continue

                try:
                    name = open(f"{path}/name").read().strip()
                except Exception as e:
                    self.logger.error(
                        f"Failed to obtain PS2 device name (SYS_FS/INPUT) – Non-critical, ignoring\n\t^^^^^^^^^{str(e)}",
                        __file__,
                    )
                    continue

                port = re.search("\d+(?=\/input)", path)

                self.info["Input"].append({name: {"PS2 Port": port.group()}})

            # Thinkpad hotkeys (HKEYs ACPI device)
            # Also includes Battery level controls, LED control, etc
            if "thinkpad_acpi" in path.lower():
                self.info["Input"].append({"Thinkpad Fn Keys": {}})

            # TODO: Handle I2C HID
            if not "usb" in path.lower():
                continue

            if os.path.isfile("{}/id/vendor".format(path)):
                try:
                    dev = "0x" + open(f"{path}/id/product", "r").read().strip()
                    ven = "0x" + open(f"{path}/id/vendor", "r").read().strip()
                except Exception as e:
                    self.logger.warning(
                        f"Failed to obtain device/vendor id of ambiguous Input device (SYS_FS/INPUT) – Non-critical, ignoring\n\t^^^^^^^^^{str(e)}",
                        __file__,
                    )
                    continue

                else:
                    if ven and dev:
                        name = self.pci.get_item(dev[2:], ven[2:], types="usb")

                        if not name:
                            self.logger.warning(
                                "Failed to identify ambiguous Input device (SYS_FS/INPUT) – Non-critical, ignoring",
                                __file__,
                            )
                            continue

                        self.info["Input"].append(
                            {
                                name.get("device", "Unknown"): {
                                    "Device ID": dev,
                                    "Vendor": ven,
                                }
                            }
                        )

    def block_info(self):
        # Block devices are found under /sys/block/
        # For each device, we check its
        # `model`, `rotational`, device file name, and `removable`
        # to report its Model, Type, Connector and Location

        for folder in os.listdir("/sys/block"):
            path = f"/sys/block/{folder}"  # folder of the block device

            # TODO: mmcblk detection e.g. eMMC storage
            if (not "nvme" in folder) and (not "sd" in folder):
                continue

            # Check properties of the block device
            try:
                model = open(f"{path}/device/model", "r").read().strip()
                rotational = open(f"{path}/queue/rotational", "r").read().strip()
                removable = open(f"{path}/removable", "r").read().strip()

                # FIXME: USB block devices all report as HDDs?
                drive_type = (
                    "Solid State Drive (SSD)"
                    if rotational == "0"
                    else "Hard Disk Drive (HDD)"
                )
                location = "Internal" if removable == "0" else "External"

                if "nvme" in folder:
                    connector = "PCIe"

                    # Uses PCI vendor,device ids to get a vendor for the NVMe block device
                    dev = open(f"{path}/device/device/device", "r").read().strip()
                    ven = open(f"{path}/device/device/vendor", "r").read().strip()
                    vendor = self.pci.get_item(dev[2:], ven[2:]).get("vendor", "")

                elif "sd" in folder:
                    # TODO: Choose correct connector type for block devices that use the SCSI subsystem
                    connector = "SCSI"
                    vendor = open(f"{path}/device/vendor", "r").read().strip()

                else:
                    connector = "Unknown"

            except Exception as e:
                self.logger.error(
                    f"Failed to obtain block device info (SYS_FS/BLOCK) – Non-critical, ignoring",
                    __file__,
                )
                return

            self.info["Storage"].append(
                {
                    f"{vendor} {model}": {
                        "Type": drive_type,
                        "Connector": connector,
                        "Location": location,
                    }
                }
            )
