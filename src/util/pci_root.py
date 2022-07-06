import os
import platform
from src.info import color_text
from src.util.debugger import Debugger as debugger

if platform.system().lower() == "darwin":
    from src.dumps.macOS.ioreg import *


def _get_valid(slot):
    try:
        return tuple([
            hex(
                int(n, 16)) for n 
                in slot.split(":")[-1].split(".")
        ])
    except Exception:
        return (None, None)

# Original source:
# https://github.com/dortania/OpenCore-Legacy-Patcher/blob/ca859c7ad7ac2225af3b50626d88f3bfe014eaa8/resources/device_probe.py#L67-L93
def construct_pcip_osx(parent_entry, acpi, logger):

    data = {
        "PCI Path": "",
        "ACPI Path": ""
    }
    paths = []
    entry = parent_entry

    while entry:
        if IOObjectConformsTo(entry, b'IOPCIDevice'):
            try:
                bus, func = ([
                    hex(int(i, 16)) for i in
                    ioname_t_to_str(
                        IORegistryEntryGetLocationInPlane(
                            entry, b'IOService', None
                        )[1]
                    ).split(',')
                ] + ['0x0'])[:2]

                paths.append(
                    f'Pci({bus},{func})'
                )
            except ValueError:
                debugger.log_dbg(color_text(
                    "--> [PCI/ACPI]: Failed! Ignoring! — (IOKit)", 
                    "red"
                ))
                logger.warning(
                    "Failed to construct PCI path for ambiguous PCI device (IOKit) – Non-critical, ignoring.",
                    __file__,
                )
                break

        elif IOObjectConformsTo(entry, b'IOACPIPlatformDevice'):
            paths.append(
                f'PciRoot({hex(int(corefoundation_to_native(IORegistryEntryCreateCFProperty(entry, "_UID", kCFAllocatorDefault, kNilOptions)) or 0))})')
            break

        elif IOObjectConformsTo(entry, b'IOPCIBridge'):
            pass

        else:
            paths = []
            debugger.log_dbg(color_text(
                "--> [PCI/ACPI]: Invalid! Unable to construct path! — (IOKit)", 
                "red"
            ))
            logger.warning(
                "Invalid PCI device – unable to construct PCI path (IOKit)",
                __file__,
            )
            break

        parent = IORegistryEntryGetParentEntry(entry, b'IOService', None)[1]

        if entry != parent_entry:
            IOObjectRelease(entry)

        entry = parent

    if paths:
        data['PCI Path'] = '/'.join(reversed(paths))

    if acpi:
        data['ACPI Path'] = ''.join([("\\" if "sb" in a.lower(
        ) else ".") + a.split("@")[0] for a in acpi.split(':')[1].split('/')[1:]])

    debugger.log_dbg(color_text(
        "--> [PCI/ACPI]: Successfully constructed PCI/ACPI path(s)! — (IOKit)", 
        "green"
    ))
    return data


def pci_from_acpi_win(wmi, instance_id, logger):

    debugger.log_dbg(color_text(
        "--> [PCI/ACPI]: Attempting to construct PCI/ACPI paths...",
        "yellow"
    ))

    try:
        # Thank you to DhinakG for this.
        # See: https://github.com/USBToolBox/tool/blob/ba3bb1238c0b552cb8066e29c5dc83b5e8faae32/Windows.py#L46
        raw_path = (
            wmi.query(
                f"SELECT * FROM Win32_PnPEntity WHERE PNPDeviceID = '{instance_id}'"
            )[0]
            .GetDeviceProperties(["DEVPKEY_Device_LocationPaths"])[0][0]
            .Data
        )
    except Exception as e:
        debugger.log_dbg(color_text(
            "--> [PCI/ACPI]: Failed to retrieve path of anonymous device! — (WMI)\n",
            "red"
        ))

        logger.error(
            f"Failed to retrieve ACPI/PCI path of anonymous device (WMI)\n\t^^^^^^^^^{str(e)}"
        )

        return {}

    if not raw_path:
        return

    data = {"PCI Path": "", "ACPI Path": ""}

    devices = raw_path

    for device in devices:
        # A valid ACPI/PCI path shouldn't have
        # `USB(...)` as any argument.
        if "usb" in device.lower():
            debugger.log_dbg(color_text(
                "--> [PCI/ACPI]: 'USB' component present in path - non-constructable! — (WMI)\n", 
                "red"
            ))
            logger.warning(
                "[USB WARNING]: Non-constructable ACPI/PCI path - ignoring.. (WMI)"
            )
            break

        path = ""

        for arg in device.split("#"):
            if "acpi" in device.lower():
                if "_SB" in arg:
                    path += "\_SB"
                    continue

                try:
                    # Thank you to DhinakG for this.
                    _acpi, val = arg[:-1].split("(")
                except Exception as e:
                    debugger.log_dbg(color_text(
                        "--> [PCI/ACPI]: Failed to parse path of anonymous device! — (WMI)\n",
                        "red"
                    ))

                    logger.error(
                        f"Failed to parse ACPI/PCI path of anonymous device (WMI)\n\t^^^^^^^^^{str(e)}"
                    )

                    path = None
                    break

                if _acpi.lower() == "pci":
                    path = None
                    break

                path += f".{val}"

                data["ACPI Path"] = path
                continue

            # Thank you to DhinakG for this.
            #
            # E.g: PCI(0301) -> ['PCI', '0301']
            digit = arg[:-1].split("(")[1]

            if not digit:
                path = None
                return

            # Add PCIROOT (domain)
            if "pciroot" in arg.lower():
                path += f"PciRoot({hex(int(digit, 16))})"
                continue

            path += f"/Pci({hex(int(digit[0:2], 16))},{hex(int(digit[2:], 16))})"

            data["PCI Path"] = path

    debugger.log_dbg(color_text(
        "--> [PCI/ACPI]: Successfully constructed PCI/ACPI path(s)! — (WMI)\n", 
        "green"
    ))

    return data

def pci_from_acpi_linux(device_path, logger):
    data = {}
    acpi = ""
    pci = ""

    try:
        acpi = open(f"{device_path}/firmware_node/path", "r").read().strip()
        pci = open(f"{device_path}/uevent", "r").read().strip()

        data["ACPI Path"] = acpi
    except Exception as e:
        debugger.log_dbg(color_text(
            "--> [PCI/ACPI]: Failed to construct paths of anonymous device! — (SYS_FS)",
            "red"
        ))

        logger.error(
            f"Failed to construct ACPI/PATH of anonymous device (SYS_FS)\n\t^^^^^^^^^{str(e)}"
        )

        return ""

    if not acpi or not pci:
        return ""

    # Path to be yielded in the end.
    # E.g: PciRoot(0x0)/Pci(0x2,0x0)
    pcip = ""

    # Parent PCI description
    #
    # <domain>:<bus>:<slot>.<function>
    slot = ""

    for line in pci.split("\n"):
        if "pci_slot_name" in line.lower():
            slot = line.split("=")[1]
            break

    if slot:
        # Domain
        pcip += f"PciRoot({hex(int(slot.split(':')[0], 16))})"
        children = []
        paths = [",".join(_get_valid(slot))]

        for path in os.listdir("/sys/bus/pci/devices"):
            if slot in os.listdir(f"/sys/bus/pci/devices/{path}"):
                children.append(path)

        for child in children:
            paths.append(",".join(_get_valid(child)))

        for comp in sorted(paths, reverse=True):
            pcip += f"/Pci({comp})"

    if pcip:
        data["PCI Path"] = pcip

    debugger.log_dbg(color_text(
        "--> [PCI/ACPI]: Successfully constructed PCI/ACPI path(s)! — (SYS_FS)",
        "green"
    ))
    
    return data
