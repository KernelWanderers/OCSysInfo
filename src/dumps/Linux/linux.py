import os
import re
import subprocess
from sys import exit
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
        self.offline = parent.offline
        self.off_data = parent.off_data

    def dump(self):
        if not "CPU" in self.off_data and not self.info.get("CPU", []):
            debugger.log_dbg("--> [LINUX]: Attempting to fetch CPU information...")
            self.cpu_info()
            debugger.log_dbg()

        if not "Motherboard" in self.off_data and not self.info.get("Motherboard", {}):
            debugger.log_dbg("--> [LINUX]: Attempting to fetch Baseboard information...")
            self.mobo_info()
            debugger.log_dbg()

        if not "GPU" in self.off_data and not self.info.get("GPU", []):
            debugger.log_dbg("--> [LINUX]: Attempting to fetch GPU information...")
            self.gpu_info()
            debugger.log_dbg()

        if not "Memory" in self.off_data and not self.info.get("Memory", []):
            debugger.log_dbg("--> [LINUX]: Attempting to fetch RAM information...")
            self.mem_info()
            debugger.log_dbg()

        if not "Network" in self.off_data and not self.info.get("Network", []):
            debugger.log_dbg("--> [LINUX]: Attempting to fetch NIC information...")
            self.net_info()
            debugger.log_dbg()

        if not "Audio" in self.off_data and not self.info.get("Audio", []):
            debugger.log_dbg("--> [LINUX]: Attempting to fetch Audio information...")
            self.audio_info()
            debugger.log_dbg()

        if not "Input" in self.off_data and not self.info.get("Input", []):
            debugger.log_dbg("--> [LINUX]: Attempting to fetch Input device information...")
            self.input_info()
            debugger.log_dbg()

        if not "Storage" in self.off_data and not self.info.get("Storage", []):
            debugger.log_dbg("--> [LINUX]: Attempting to fetch Storage information...")
            self.block_info()
            debugger.log_dbg()

    def cpu_info(self):
        try:
            debugger.log_dbg(color_text(
                "--> [CPU]: Attempting to fetch relevant information of current CPU... — (PROC_FS)",
                "yellow"
            ))

            cpus = open("/proc/cpuinfo", "r").read()

            debugger.log_dbg(color_text(
                "--> [CPU]: Successfully obtained relevant information of current CPU! — (PROC_FS)",
                "green"
            ))
        except Exception as e:
            debugger.log_dbg(color_text(
                "--> [CPU]: Failed to fetch relevant information of current CPU! — (PROC_FS)",
                "red"
            ))

            self.logger.critical(
                f"Failed to obtain CPU information. This should not happen. \n\t^^^^^^^^^{str(e)}",
                __file__,
            )

            cpu_err(e)

        self.info["CPU"] = []

        architecture = subprocess.run(
            ['uname', '-m'], capture_output=True, text=True)

        # Check if the architecture is ARM.
        if architecture.stdout == "aarch64\n" or "arm" in architecture.stdout:
            debugger.log_dbg(color_text(
                "--> [CPU]: Detected ARM chip – continuing... — (PROC_FS)",
                "cyan"
            ))
            
            data = {}

            # Get the name of the CPU.
            model = re.search(r"(?<=Hardware\t\: ).+(?=\n)", cpus)

            if not model:
                debugger.log_dbg(color_text(
                    "--> [CPU]: Failed to obtain model name of current CPU – critical! — (PROC_FS)",
                    "red"
                ))

                cpu_err("AMBIGUOUS ISSUE")

                return

            # Get the ARM version of the CPU
            arm_version = re.search(r"(?<=CPU architecture\: ).+(?=\n)", cpus)
            model = model.group()
            data = {model: {}}

            try:
                # Count the amount of times 'processor'
                # is matched, since threads are enumerated individually.
                threads = cpus.count("processor")
                data[model]["Threads"] = (threads)
            except Exception as e:
                debugger.log_dbg(color_text(
                    "--> [CPU]: Failed to thread count of current CPU – ignoring! — (PROC_FS)",
                    "red"
                ))

                self.logger.error(
                    f"Failed to resolve thread count for {model} (PROC_FS)\n\t^^^^^^^^^{str(e)}",
                    __file__,
                )
                pass

            data[model]["ARM Version"] = arm_version.group()

            self.info.get("CPU").append(data)

            debugger.log_dbg(color_text(
                "--> [CPU]: Successfully obtained relevant information of current CPU! — (PROC_FS)",
                "green"
            ))

            return

        cpu = cpus.split("\n\n")

        if not cpu:
            return

        cpu = cpu[0]  # Get only the first CPU identifier.

        model = re.search(r"(?<=model name\t\: ).+(?=\n)", cpu)

        if not model:
            debugger.log_dbg(color_text(
                "--> [CPU]: Failed to obtain model name of current CPU – critical! — (PROC_FS)",
                "red"
            ))

            self.logger.critical(
                "Failed to obtain basic CPU information (PROC_FS)", __file__
            )

            cpu_err("AMBIGUOUS ISSUE")

        else:
            model = model.group()

        flagers = re.search(r"(?<=flags\t\t\: ).+(?=\n)", cpu)
        cores = re.search(r"(?<=cpu cores\t\: ).+(?=\n)", cpu)
        data = {model: {}}
        vendor = "intel" if "intel" in model.lower() else "amd"


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

            debugger.log_dbg(color_text(
                "--> [CPU]: Successfully obtained highest supported SSE version and SSSE3 availability. — (PROC_FS)",
                "green"
            ))

        if cores:
            data[model]["Cores"] = cores.group()
            debugger.log_dbg(color_text(
                "--> [CPU]: Successfully obtained core count of current CPU! — (PROC_FS)",
                "green"
            ))

        try:
            # Count the amount of times 'processor'
            # is matched, since threads are enumerated
            # individually.
            data[model]["Threads"] = (
                open("/proc/cpuinfo", "r").read().count("processor")
            )

            debugger.log_dbg(color_text(
                "--> [CPU]: Successfully obtained thread count of current CPU! — (PROC_FS)",
                "green"
            ))
        except Exception as e:
            debugger.log_dbg(color_text(
                f"--> [CPU]: Failed to resolve threac count for {model} – critical! — (PROC_FS)",
                "green"
            ))

            self.logger.error(
                f"Failed to resolve thread count for {model} (PROC_FS)\n\t^^^^^^^^^{str(e)}",
                __file__,
            )

            pass

        if not self.offline:
            self.cnm = CodenameManager(model, vendor)

            if self.cnm.codename:
                data[model]["Codename"] = self.cnm.codename

        self.info.get("CPU").append(data)

    def gpu_info(self):

        # Because DD wanted this for WSL*.
        if not os.path.exists("/sys/class/drm"):
            debugger.log_dbg(color_text(
                "--> [GPU]: WSL detected – skipping! — (SYS_FS/DRM)",
                "cyan"
            ))

            return

        self.info["GPU"] = []

        for file in os.listdir("/sys/class/drm/"):

            # DRM devices (not FBDev) are enumerated with the format `cardX`
            # inside of sysfs's DRM directory. So we look for those, and traverse
            # them. We look for the `device` and `vendor` file, which should always be there.
            if "card" in file and not "-" in file:
                path = f"/sys/class/drm/{file}/device"
                data = {}

                try:
                    debugger.log_dbg(color_text(
                        "--> [GPU]: Attempting to fetch device/vendor IDs... — (SYS_FS/DRM)",
                        "yellow"
                    ))

                    ven = open(f"{path}/vendor", "r").read().strip()
                    dev = open(f"{path}/device", "r").read().strip()

                    data = {"Device ID": dev, "Vendor": ven}

                    debugger.log_dbg(color_text(
                        "--> [GPU]: Successfully obtained IDs! — (SYS_FS/DRM)",
                        "green"
                    ))
                except Exception as e:
                    debugger.log_dbg(color_text(
                        "--> [GPU]: Failed to obtain IDs – critical! — (SYS_FS/DRM)",
                        "red"
                    ))

                    self.logger.critical(
                        f"Failed to obtain vendor/device id for GPU device (SYS_FS/DRM)\n\t^^^^^^^^^{str(e)}",
                        __file__,
                    )

                    continue

                if self.offline:
                    debugger.log_dbg(color_text(
                        "--> [GPU]: Model name is unobtainable - system is offline – ignoring! — (SYS_FS/DRM)",
                        "red"
                    ))

                    model = "Unknown GPU Device"
                else:
                    try:
                        debugger.log_dbg(color_text(
                            "--> [GPU]: Attempting to fetch model... — (SYS_FS/DRM)",
                            "yellow"
                        ))

                        model = self.pci.get_item(
                            dev[2:], ven[2:]).get("device")

                        debugger.log_dbg(color_text(
                            "--> [GPU]: Successfully obtained model! — (SYS_FS/DRM)",
                            "green"
                        ))
                    except Exception:
                        model = "Unknown GPU Device"

                        debugger.log_dbg(color_text(
                            "--> [GPU]: Failed to obtain model – ignoring! — (SYS_FS/DRM)",
                            "red"
                        ))

                        self.logger.warning(
                            f"Failed to obtain model for GPU Device (SYS_FS/DRM) – Non-critical, ignoring",
                            __file__,
                        )

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
                    debugger.log_dbg(color_text(
                        "--> [GPU]: Failed during PCI/ACPI path construction – ignoring! — (SYS_FS/DRM)",
                        "red"
                    ))

                    self.logger.error(
                        f"Failed during ACPI/PCI path construction (SYS_FS/DRM)\n\t^^^^^^^^^{str(e)}"
                    )

                gpucname = gpu(dev, ven)

                if gpucname:
                    data["Codename"] = gpucname

                self.info["GPU"].append({model: data})

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
        if not os.path.isdir("/sys/firmware/dmi/entries"):
            debugger.log_dbg(color_text(
                "--> [RAM]: Individual DMI table entries don't exist – skipping RAM detection! — (SYS_FS/DMI)",
                "red"
            ))

            return

        print(
            "\nWe apologise for the inconvenience, but we really need you to run this specific call as sudo."
        )
        print("It's for extracting information about your system's RAM modules.")
        print("It's simply running: 'sudo cat /sys/firmware/dmi/entries/17-*/raw'\n")

        response = input(
            "You can feel free to respond with 'N' if you don't wish to proceed with this! Or 'Y' if you do: "
        )

        if "n" in response.lower():
            print("Cancelled, bailing memory detection...")

            debugger.log_dbg(color_text(
                "--> [RAM]: Memory detection cancelled – bailing! — (SYS_FS/DMI)",
                "cyan"
            ))

            return

        self.info["Memory"] = []

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
                strings = value[length_field: len(value)].split(b"\0")

                try:
                    debugger.log_dbg(color_text(
                        "--> [RAM]: Attempting to obtain Part-Number... — (SYS_FS/DMI)",
                        "yellow"
                    ))

                    """
                    ---------------------
                    |    Part Number    |
                    ---------------------

                    Obtains the value at offset 1Ah, which indicates at which index, pre-sanitisation,
                    in the `strings` list the real string value is stored.

                    Which is: `strings[value[0x1A] - 1]`, after obtaining it, it decodes it to `ascii`.

                    Special thanks to [Quist](https://github.com/nadiaholmquist) for this.
                    """
                    part_no = get_string_entry(
                        strings, value[0x1A]).strip() + " (Part Number)"
                    data[part_no] = {}

                    debugger.log_dbg(color_text(
                        "--> [RAM]: Successfully obtained Part-Number! — (SYS_FS/DMI)",
                        "green"
                    ))
                except Exception as e:
                    debugger.log_dbg(color_text(
                        "--> [RAM]: Failed to obtain Part-Number – critical! — (SYS_FS/DMI)" +
                        f"\n\t^^^^^^^{str(e)}",
                        "red"
                    ))

                    self.logger.warning(
                        f"Unable to determine part number for memory (RAM) module (SYS_FS/DMI)\n\t^^^^^^^^^{str(e)}",
                        __file__,
                    )

                    continue

                try:
                    debugger.log_dbg(color_text(
                        "--> [RAM]: Attempting to obtain DIMM type... — (SYS_FS/DMI)",
                        "yellow"
                    ))

                    # The DIMM type value is stored at offset 12h
                    data[part_no]["Type"] = MEMORY_TYPE[value[0x12]]

                    debugger.log_dbg(color_text(
                        "--> [RAM]: Successfully obtained DIMM type! — (SYS_FS/DMI)",
                        "green"
                    ))
                except Exception as e:
                    debugger.log_dbg(color_text(
                        "--> [RAM]: Failed to obtain DIMM type – ignoring! — (SYS_FS/DMI)" +
                        f"\n\t^^^^^^^{str(e)}",
                        "red"
                    ))

                    self.logger.warning(
                        f"Unable to determine type of memory (RAM) module (SYS_FS/DMI)\n\t^^^^^^^^{str(e)}",
                        __file__,
                    )

                    data[part_no]["Type"] = "UNKNOWN"

                try:
                    debugger.log_dbg(color_text(
                        "--> [RAM]: Attempting to obtain DIMM location... — (SYS_FS/DMI)",
                        "yellow"
                    ))

                    # Explanation same as for Part Number.
                    data[part_no]["Slot"] = {
                        "Channel": get_string_entry(strings, value[0x10]), 
                        "Bank": get_string_entry(strings, value[0x11])
                    }

                    debugger.log_dbg(color_text(
                        "--> [RAM]: Successfully obtained DIMM location! — (SYS_FS/DMI)",
                        "green"
                    ))
                except Exception as e:
                    debugger.log_dbg(color_text(
                        "--> [RAM]: Failed to obtain DIMM location – critical! — (SYS_FS/DMI)" +
                        f"\n\t^^^^^^^{str(e)}",
                        "red"
                    ))

                    self.logger.warning(
                        f"Unable to determine slot location for memory (RAM) module (SYS_FS/DMI)\n\t^^^^^^^^^{str(e)}",
                        __file__,
                    )

                    continue

                try:
                    debugger.log_dbg(color_text(
                        "--> [RAM]: Attempting to obtain manufacturer... — (SYS_FS/DMI)",
                        "yellow"
                    ))

                    # Explanation same as for Part Number.
                    data[part_no]["Manufacturer"] = get_string_entry(strings, value[0x17])

                    debugger.log_dbg(color_text(
                        "--> [RAM]: Successfully obtained manufacturer! — (SYS_FS/DMI)",
                        "green"
                    ))
                except Exception as e:
                    debugger.log_dbg(color_text(
                        "--> [RAM]: Failed to obtain manufacturer – critical! — (SYS_FS/DMI)" +
                        f"\n\t^^^^^^^{str(e)}",
                        "red"
                    ))

                    self.logger.warning(
                        f"Unable to determine manufacturer for memory (RAM) module (SYS_FS/DMI)\n\t^^^^^^^^^^^^{str(e)}",
                        __file__,
                    )

                    continue

                try:
                    debugger.log_dbg(color_text(
                        "--> [RAM]: Attempting to obtain RAM module capacity... — (SYS_FS/DMI)",
                        "yellow"
                    ))

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
                        debugger.log_dbg(color_text(
                            "--> [RAM]: Failed to determine capacity – ignoring! — (SYS_FS/DMI)",
                            "red"
                        ))

                        data["Capacity"] = "UNKNOWN SIZE"

                    # In cases where the individual memory module's
                    # capacity is `n >= (32GB-1MB)`, the value at 0Ch
                    # will be `0x7FFF`; meaning we should look at 1Ch instead.
                    elif size == 0x7FFF:
                        # 4 bytes, at offset 1Ch
                        size = int(
                            "".join(
                                reversed(value.hex()[0x1C: 0x1C + 0x4])), 16
                        )

                    # Whether or not the value is represented in KB or MB
                    #
                    # 0 - MB
                    # 1 - KB
                    rep = "MB" if (size >> 15) & 1 == 0 else "KB"

                    data[part_no]["Capacity"] = f"{size}{rep}"

                    if "unknown" not in data["Capacity"].lower():
                        debugger.log_dbg(color_text(
                            "--> [RAM]: Successfully obtained capacity size! — (SYS_FS/DMI)",
                            "green"
                        ))
                except Exception as e:
                    debugger.log_dbg(color_text(
                        "--> [RAM]: Failed to obtain capacity size – critical! — (SYS_FS/DMI)" +
                        f"\n\t^^^^^^^{str(e)}",
                        "red"
                    ))

                    self.logger.warning(
                        f"Unable to determine size for memory (RAM) module (SYS_FS/DMI)\n\t^^^^^^^^^{str(e)}",
                        __file__,
                    )
                    
                    continue

            self.info["Memory"].append(data)

    def net_info(self):
        if not os.path.isdir("/sys/class/net"):
            debugger.log_dbg(color_text(
                "--> [Network]: Network controllers are not enumerated – critical! — (SYS_FS/NET)",
                "red"
            ))

            return

        self.info["Network"] = []

        for file in os.listdir("/sys/class/net"):
            path = f"/sys/class/net/{file}/device"
            data = {}

            # We ensure that the enumerated directory in the sysfs net
            # directory is a valid card, since it'll contain a `vendor` and
            # `device` file.
            if os.path.isfile("{}/device".format(path)):
                try:
                    debugger.log_dbg(color_text(
                        "--> [Network]: Attempting to obtain device/vendor IDs of current NIC... — (SYS_FS/NET)",
                        "yellow"
                    ))

                    ven = open(f"{path}/vendor", "r").read().strip()
                    dev = open(f"{path}/device", "r").read().strip()

                    data = {"Device ID": dev, "Vendor": ven}

                except Exception as e:
                    debugger.log_dbg(color_text(
                        "--> [Network]: Failed to obtain IDs of current NICs – critical! — (SYS_FS/NET)" +
                        f"\n\t^^^^^^^{str(e)}",
                        "red"
                    ))

                    self.logger.error(
                        f"Failed to obtain vendor/device id for Network controller (SYS_FS/NET)\n\t^^^^^^^^^{str(e)}",
                        __file__,
                    )

                    return

                if self.offline:
                    debugger.log_dbg(color_text(
                        "--> [Network]: Cannot obtain model of current NIC - machine is offline – ignoring! — (SYS_FS/NET)",
                        "red"
                    ))

                    model = "Unknown Network Controller"
                else:
                    try:
                        debugger.log_dbg(color_text(
                            "--> [Network]: Attempting to obtain model of current NIC... — (SYS_FS/NET)",
                            "yellow"
                        ))

                        model = self.pci.get_item(
                            dev[2:], ven[2:]).get("device")
                    except Exception:
                        model = "Unknown Network Controller"

                        debugger.log_dbg(color_text(
                            "--> [Network]: Failed to obtain model of current NIC – ignoring! — (SYS_FS/NET)" +
                            f"\n\t^^^^^^^{str(e)}",
                            "red"
                        ))

                        self.logger.warning(
                            f"Failed to obtain model for Network Controller (SYS_FS/NET) – Non-critical, ignoring",
                            __file__,
                        )

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
                    debugger.log_dbg(color_text(
                        "--> [Network]: Failed during PCI/ACPI path construction – ignoring! — (SYS_FS/NET)" +
                        f"\n\t^^^^^^^{str(e)}",
                        "red"
                    ))

                    self.logger.error(
                        f"Failed during ACPI/PCI path construction (SYS_FS/NET)\n\t^^^^^^^^^{str(e)}"
                    )

                self.info["Network"].append({model: data})

    def audio_info(self):
        if not os.path.isabs("/sys/class/sound"):
            debugger.log_dbg(color_text(
                "--> [Audio]: Audio controllers are not enumerated – critical! — (SYS_FS/SOUND)",
                "red"
            ))

            return

        self.info["Audio"] = []
        
        for file in os.listdir("/sys/class/sound"):

            # Sound devices are enumerated similarly to DRM devices,
            # with the format `cardX`, so we look for those, and look
            # for `vendor` and `device` files.
            if "card" in file.lower() and not "-" in file.lower():
                path = f"/sys/class/sound/{file}/device"
                data = {}

                try:
                    debugger.log_dbg(color_text(
                        "--> [Audio]: Attempting to obtain device/vendor IDs of current Audio controller... — (SYS_FS/SOUND)",
                        "yellow"
                    ))

                    ven = open(f"{path}/vendor", "r").read().strip()
                    dev = open(f"{path}/device", "r").read().strip()

                    data = {"Device ID": dev, "Vendor": ven}

                    debugger.log_dbg(color_text(
                        "--> [Audio]: Successfully obtained IDs of current Audio controller! — (SYS_FS/SOUND)",
                        "green"
                    ))
                except Exception as e:
                    debugger.log_dbg(color_text(
                        "--> [Audio]: Failed to obtain IDs of current Audio controller – critical! — (SYS_FS/SOUND)" +
                        f"\n\t^^^^^^^{str(e)}",
                        "red"
                    ))

                    self.logger.warning(
                        f"Failed to obtain vendor/device id for Audio device/controller (SYS_FS/SOUND)\n\t^^^^^^^^^{str(e)}",
                        __file__,
                    )

                    continue

                if self.offline:
                    debugger.log_dbg(color_text(
                        "--> [Audio]: Cannot obtain model of current Audio controller - machine is offline – ignoring! — (SYS_FS/SOUND)",
                        "red"
                    ))

                    model = "Unknown Sound Device"
                else:
                    try:
                        debugger.log_dbg(color_text(
                            "--> [Audio]: Attempting to obtain model of current Audio controller... — (SYS_FS/SOUND)",
                            "yellow"
                        ))

                        model = self.pci.get_item(
                            dev[2:], ven[2:]).get("device")

                        debugger.log_dbg(color_text(
                            "--> [Audio]: Successfully obtained model of current Audio controller! — (SYS_FS/SOUND)",
                            "green"
                        ))
                    except Exception as e:
                        model = "Unknown Sound Device"

                        debugger.log_dbg(color_text(
                            "--> [Audio]: Failed to obtain model of current Audio controller – ignoring! — (SYS_FS/SOUND)" +
                            f"\n\t^^^^^^^{str(e)}",
                            "red"
                        ))

                        self.logger.warning(
                            f"Failed to obtain model for Audio device/controller (SYS_FS/SOUND) – Non-critical, ignoring",
                            __file__,
                        )

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
                    debugger.log_dbg(color_text(
                        "--> [Audio]: Failed during PCI/ACPI path construction – ignoring! — (SYS_FS/SOUND)" +
                        f"\n\t^^^^^^^{str(e)}",
                        "red"
                    ))

                    self.logger.error(
                        f"Failed during ACPI/PCI path construction (SYS_FS/SOUND)\n\t^^^^^^^^^{str(e)}"
                    )

                try:
                    debugger.log_dbg(color_text(
                        "--> [Audio]: Attempting to obtain HDA codec for all matching devices... — (SYS_FS/SOUND)",
                        "yellow"
                    ))

                    dirs = [n for n in os.listdir(
                        path) if "hdaudio" in n.lower()]

                    for dir in dirs:
                        if not os.path.isfile(f"{path}/{dir}/chip_name"):
                            continue

                        chip_name = open(
                            f"{path}/{dir}/chip_name", "r").read().strip()

                        debugger.log_dbg(color_text(
                            f"--> [Audio]: Obtained '{chip_name}' codec! — (SYS_FS/SOUND)",
                            "green"
                        ))

                        data["Codec"] = chip_name
                except Exception as e:
                    debugger.log_dbg(color_text(
                        "--> [Audio]: Failed to obtain HDA codec of device! — (SYS_FS/SOUND)" +
                        f"\n\t^^^^^^^{str(e)}",
                        "red"
                    ))

                    self.logger.warning(
                        f"Failed to obtain HDA codec of device (SYS_FS/SOUND)\n\t^^^^^^^^^{str(e)}"
                    )

                self.info.get("Audio").append({model: data})

    def mobo_info(self):

        # Details about the motherboard is
        # located in /sys/devices/virtual/dmi/id
        #
        # So we simply look for `board_name` and
        # `board_vendor` to extract its model name,
        # and its vendor's name.
        try:
            debugger.log_dbg(color_text(
                f"--> [Baseboard]: Attempting to obtain information about baseboard... — (SYS_FS/DMI)",
                "yellow"
            ))

            model = open(f"/sys/devices/virtual/dmi/id/board_name", "r").read().strip()
            vendor = open(f"/sys/devices/virtual/dmi/id/board_vendor", "r").read().strip()
        except Exception as e:
            self.logger.critical(
                f"Failed to obtain Motherboard details (SYS_FS/DMI)\n\t^^^^^^^^^{str(e)}",
                __file__,
            )

            return

        if not model:
            return

        debugger.log_dbg(color_text(
            f"--> [Baseboard]: Successfully obtained information about baseboard! — (SYS_FS/DMI)",
            "green"
        ))

        self.info["Motherboard"] = {}

        data = {"Model": model}

        if vendor:
            data["Vendor"] = vendor

        self.info["Motherboard"] = data

    def input_info(self):

        if not os.path.isdir("/proc/bus/input/devices"):
            debugger.log_dbg(color_text(
                "--> [Input]: Input devices not enumerated – critical! — (SYS_FS/INPUT)",
                "red"
            ))

            return
        
        self.info["Input"] = []

        # This is the simplest way of reliably
        # obtaining the path of the input devices
        # located in sysfs. Ironically, by looking
        # into procfs.
        #
        # Out of the things we look for,
        # it contains the device name, and its sysfs path.
        try:
            debugger.log_dbg(color_text(
                "--> [Input]: Attempting to obtain list of input devices... — (SYS_FS/INPUT)",
                "yellow"
            ))

            devices = open("/proc/bus/input/devices", "r").read().strip()
            sysfs = []
        except Exception as e:
            debugger.log_dbg(color_text(
                "--> [Input]: Failed to obtain input devices – critical! — (SYS_FS/INPUT)" +
                f"\n\t^^^^^^^{str(e)}",
                "red"
            ))

            self.logger.critical(
                f"Failed to obtain Input devices (SYS_FS/INPUT) — THIS GENERALLY SHOULD NOT HAPPEN ON LAPTOP DEVICES.\n\t^^^^^^^^^{str(e)}",
                __file__,
            )

            return

        for device in devices.split("\n\n"):
            for line in device.split("\n"):
                if "sysfs" in line.lower():
                    sysfs.append("/sys{}".format(line.split("=")[1]))

        if sysfs:
            debugger.log_dbg(color_text(
                "--> [Input]: Successfully obtained sysfs paths of input devices! — (SYS_FS/INPUT)",
                "green"
            ))

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
                    debugger.log_dbg(color_text(
                        "--> [Input]: Failed to identify device using the RMI4 protocol – skipping! — (SYS_FS/INPUT)",
                        "red"
                    ))

                    self.logger.warning(
                        "Failed to identify device using the RMI4 protocol (SYS_FS/INPUT) – Skipping",
                        __file__,
                    )

                    continue

                try:
                    debugger.log_dbg(color_text(
                        "--> [Input]: Attempting to obtain product/vendor IDs of device using the RMI4 protocol... — (SYS_FS/INPUT)",
                        "yellow"
                    ))

                    prod_id = open(f"{path}/name", "r").read().strip()
                    vendor = open(f"{path}/id/vendor", "r").read().strip()

                    debugger.log_dbg(color_text(
                        "--> [Input]: Successfully obtained product/vendor IDs! — (SYS_FS/INPUT)",
                        "green"
                    ))
                except Exception as e:
                    debugger.log_dbg(color_text(
                        "--> [Input]: Failed to obtain product/vendor IDs of device using the RMI4 protocol – skipping! — (SYS_FS/INPUT)" +
                        f"\n\t^^^^^^^{str(e)}",
                        "red"
                    ))

                    self.logger.error(
                        f"Failed to obtain product/vendor id of device using the RMI4 protocol (SYS_FS/INPUT) – Skipping",
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
                    debugger.log_dbg(color_text(
                        "--> [Input]: Failed to identify PS2 device – skipping! — (SYS_FS/INPUT)",
                        "red"
                    ))

                    self.logger.warning(
                        "Failed to identify PS2 device (SYS_FS/INPUT) – Non-critical, ignoring",
                        __file__,
                    )

                    continue

                try:
                    debugger.log_dbg(color_text(
                        "--> [Input]: Attempting to obtain name of PS2 device... — (SYS_FS/INPUT)",
                        "yellow"
                    ))

                    name = open(f"{path}/name").read().strip()

                    debugger.log_dbg(color_text(
                        "--> [Input]: Successfully obtained name! — (SYS_FS/INPUT)",
                        "green"
                    ))
                except Exception:
                    debugger.log_dbg(color_text(
                        "--> [Input]: Failed to obtain name of PS2 device – skipping! — (SYS_FS/INPUT)" +
                        f"\n\t^^^^^^^{str(e)}",
                        "red"
                    ))

                    self.logger.warning(
                        f"Failed to obtain PS2 device name (SYS_FS/INPUT) – Non-critical, ignoring",
                        __file__,
                    )

                    continue

                port = re.search("\d+(?=\/input)", path)

                if port:
                    debugger.log_dbg(color_text(
                        "--> [Input]: Successfully detected PS2 port of device! — (SYS_FS/INPUT)",
                        "green"
                    ))

                    port = port.group()
                
                else:
                    debugger.log_dbg(color_text(
                        "--> [Input]: Failed to detect PS2 port of device – ignoring! — (SYS_FS/INPUT)",
                        "green"
                    ))

                    port = "UNKNOWN"


                self.info["Input"].append({name: {"PS2 Port": port}})

            # Thinkpad hotkeys (HKEYs ACPI device)
            # Also includes Battery level controls, LED control, etc
            if "thinkpad_acpi" in path.lower():
                debugger.log_dbg(color_text(
                    "--> [Input]: Detected HKEYs ACPI device! — (SYS_FS/INPUT)",
                    "cyan"
                ))
                self.info["Input"].append({"Thinkpad Fn Keys": {}})

            # I2C devices (over RMI4 _or_ HID)
            if "i2c" in path.lower():
                _data = {}

                if not os.path.isfile(f"{path}/id"):
                    debugger.log_dbg(color_text(
                        "--> [Input]: Failed to obtain device/vendor ID of I2C device – ignoring! — (SYS_FS/INPUT)",
                        "red"
                    ))

                    self.logger.warning(
                        "Failed to obtain device/vendor id of I2C device (SYS_FS/INPUT) – Non-critical, ignoring",
                        __file__,
                    )

                    name = {"device": "Ambiguous Input Device (I2C)"}

                try:
                    debugger.log_dbg(color_text(
                        "--> [Input]: Attempting to obtain device/vendor ID of I2C device... — (SYS_FS/INPUT)",
                        "yellow"
                    ))

                    ven = open(f"{path}/id/vendor").read().strip()
                    dev = open(f"{path}/id/device").read().strip()

                    _data = {
                        "Device ID": dev,
                        "Vendor ID": ven,
                    }

                    debugger.log_dbg(color_text(
                        "--> [Input]: Successfully obtained device/vendor ID of of I2C device! — (SYS_FS/INPUT)",
                        "green"
                    ))
                except Exception as e:
                    debugger.log_dbg(color_text(
                        "--> [Input]: Failed to obtain device/vendor ID of of I2C device... — (SYS_FS/INPUT)" +
                        f"\n\t^^^^^^^{str(e)}",
                        "red"
                    ))

                    self.logger.warning(
                        f"Failed to obtain device/vendor id of I2C device (SYS_FS/INPUT) – Non-critical, ignoring",
                        __file__,
                    )

                    continue

                self.info["Input"].append({
                    name.get("device"): _data
                })

            # TODO: Handle I2C HID
            if not "usb" in path.lower():
                debugger.log_dbg(color_text(
                    "--> [Input]: Detected I2C HID device – skipping due to lack of implementation! — (SYS_FS/INPUT)",
                    "cyan"
                ))

                continue

            if os.path.isfile(f"{path}/id/vendor"):
                debugger.log_dbg(color_text(
                    "--> [Input]: Detected ambiguous input device! — (SYS_FS/INPUT)",
                    "cyan"
                ))

                try:
                    debugger.log_dbg(color_text(
                        "--> [Input]: Attempting to obtain product/vendor IDs of ambiguous input device... — (SYS_FS/INPUT)",
                        "yellow"
                    ))

                    dev = "0x" + open(f"{path}/id/product", "r").read().strip()
                    ven = "0x" + open(f"{path}/id/vendor", "r").read().strip()

                    debugger.log_dbg(color_text(
                        "--> [Input]: Successfully obtained IDs! — (SYS_FS/INPUT)",
                        "green"
                    ))
                except Exception as e:
                    debugger.log_dbg(color_text(
                        "--> [Input]: Failed to obtain product/vendor IDs of ambiguous input device – skipping! — (SYS_FS/INPUT)" +
                        f"\n\t^^^^^^^{str(e)}",
                        "red"
                    ))

                    self.logger.warning(
                        f"Failed to obtain device/vendor id of ambiguous Input device (SYS_FS/INPUT) – Non-critical, ignoring",
                        __file__,
                    )

                    continue

                if ven and dev:
                    if self.offline:
                        debugger.log_dbg(color_text(
                            "--> [Input]: Cannot obtain model of ambiguous input device - machine is offline – ignoring! — (SYS_FS/INPUT)",
                            "red"
                        ))

                        name = {"device": "Unknown Input Device"}

                    else:
                        try:
                            debugger.log_dbg(color_text(
                                "--> [Input]: Attempting to obtain model of ambiguous input device... — (SYS_FS/INPUT)",
                                "yellow"
                            ))

                            name = self.pci.get_item(
                                dev[2:], ven[2:], types="usb")

                            debugger.log_dbg(color_text(
                                "--> [Input]: Successfully obtained model of ambiguous input device! — (SYS_FS/INPUT)",
                                "green"
                            ))
                        except Exception as e:
                            name = {"device": "Unknown Input Device"}

                            debugger.log_dbg(color_text(
                                "--> [Input]: Failed to obtain model of ambiguous input device – ignoring! — (SYS_FS/INPUT)" +
                                f"\n\t^^^^^^^{str(e)}",
                                "red"
                            ))

                            self.logger.warning(
                                f"Failed to obtain model for Input device (SYS_FS/INPUT) – Non-critical, ignoring",
                                __file__,
                            )

                    self.info["Input"].append(
                        {
                            name.get("device", "Unknown Input Device"): {
                                "Device ID": dev,
                                "Vendor": ven,
                            }
                        }
                    )

    def block_info(self):
        if not os.path.isdir("/sys/block"):
            debugger.log_dbg(color_text(
                "--> [Storage]: Storage devices are not enumerated – critical! — (SYS_FS/BLOCK)",
                "red"
            ))

            return

        self.info["Storage"] = []
        
        # Block devices are found under /sys/block/
        # For each device, we check its
        # `model`, `rotational`, device file name, and `removable`
        # to report its Model, Type, Connector and Location
        for folder in os.listdir("/sys/block"):
            # Enclosing directory of
            # this block device.
            path = f"/sys/block/{folder}"

            # TODO: mmcblk detection e.g. eMMC storage
            if (not "nvme" in folder) and (not "sd" in folder):
                debugger.log_dbg(color_text(
                    "--> [Storage]: Unsupported storage device detected – skipping! — (SYS_FS/BLOCK)",
                    "red"
                ))

                continue

            # Check properties of the block device
            try:
                debugger.log_dbg(color_text(
                    "--> [Storage]: Fetching relevant information of current Storage device... — (SYS_FS/BLOCK)",
                    "yellow"
                ))

                model = open(f"{path}/device/model", "r").read().strip()
                rotational = open(
                    f"{path}/queue/rotational", "r").read().strip()
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
                    drive_type = "Non-Volatile Memory Express (NVMe)"

                    # Uses PCI vendor & device ids to get a vendor for the NVMe block device
                    dev = open(f"{path}/device/device/device",
                               "r").read().strip()
                    ven = open(f"{path}/device/device/vendor",
                               "r").read().strip()

                    if self.offline:
                        vendor = ""

                    else:
                        try:
                            vendor = self.pci.get_item(
                                dev[2:], ven[2:]).get("vendor", "")
                        except Exception as e:
                            vendor = ""

                            debugger.log_dbg(color_text(
                                "--> [Storage]: Failed to obtain vendor of current Storage device – ignoring! — (SYS_FS/BLOCK)" +
                                f"\n\t^^^^^^^{str(e)}",
                                "red"
                            ))

                            self.logger.warning(
                                f"Failed to obtain vendor for block device (SYS_FS/BLOCK) – Non-critical, ignoring"
                            )

                elif "sd" in folder:
                    # TODO: Choose correct connector type for block devices that use the SCSI subsystem
                    connector = "SCSI"
                    vendor = open(f"{path}/device/vendor", "r").read().strip()

                else:
                    debugger.log_dbg(color_text(
                        "--> [Storage]: Unknown connector type – ignoring! — (SYS_FS/BLOCK)",
                        "red"
                    ))

                    connector = "Unknown"

            except Exception as e:
                debugger.log_dbg(color_text(
                    "--> [Storage]: Failed to obtain block device info – critical! — (SYS_FS/BLOCK)" +
                    f"\n\t^^^^^^^{str(e)}",
                    "red"
                ))

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
