import os


def _get_valid(slot):
    parts = [n.split(".")[0] for n in slot.split(":")]

    try:
        bus, slot = hex(int(parts[1].split(".")[0], 16)), hex(
            int(parts[2].split(".")[0], 16)
        )
    except Exception as e:
        return [None, None]

    return [bus, slot]


def pci_from_acpi_osx(raw_path, logger):
    if not raw_path:
        logger.warning(
            "Failed to obtain constructable path from anonymous device (IOKit)"
        )
        return {}

    p_path = ""
    a_path = ""

    for arg in raw_path.split(":")[1].split("/")[1:]:
        if not "@" in arg.lower():
            a_path += f"\{arg}"
        else:
            acpi = arg.split("@")[0]
            a_path += f".{acpi}"

            # The below logic is
            # implemented by CorpNewt.
            #
            # Thanks, bb!
            pcip = int(arg.split("@")[1], 16)

            a = hex(pcip >> 16 & 0xFFFF)
            b = hex(pcip & 0xFFFF)

            if "pci" in arg.lower():
                p_path += f"PciRoot({a})"
                continue

            p_path += f"/Pci({a},{b})"

    return {"PCI Path": p_path, "ACPI Path": a_path}


def pci_from_acpi_win(wmi, instance_id, logger):

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
        logger.error(
            f"Failed to retrieve ACPI/PCI path of anonymous device (WMI)\n\t^^^^^^^^^{str(e)}"
        )
        return {}

    if not raw_path:
        return

    data = {"PCI Path": "", "ACPI Path": ""}

    devices = raw_path

    for device in devices:
        if not "acpi" in device.lower() and "pci" in device.lower():
            path = ""

            for arg in device.split("#"):
                # A valid PCI path shouldn't have
                # a `USB(...)` as any argument.
                if "usb" in arg.lower():
                    logger.warning(
                        "[USB WARNING]: Non-constructable ACPI/PCI path - ignoring.. (WMI)"
                    )
                    break

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

        elif "acpi" in device.lower():
            path = ""

            for arg in device.split("#"):
                if "_SB" in arg:
                    path += "\_SB"
                    continue

                try:
                    # Thank you to DhinakG for this.
                    _acpi, val = arg[:-1].split("(")
                except Exception as e:
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

    return data


def pci_from_acpi_linux(device_path, logger):
    data = {}

    try:
        acpi = open(f"{device_path}/firmware_node/path", "r").read().strip()
        pci = open(f"{device_path}/uevent", "r").read().strip()

        data["ACPI Path"] = acpi
    except Exception as e:
        logger.error(
            f"Failed to construct ACPI/PATH of anonymous device (SYS_FS)\n\t^^^^^^^^^{str(e)}"
        )

    # Path to be yielded in the end.
    # E.g: PciRoot(0x0)/Pci(0x2,0x0)
    pcip = ""

    # Parent PCI description
    #
    # <domain>:<bus>:<slot>.<function>
    slot = ""

    # Whether or not there's 1 or 2 components
    # of the entire PCI path.
    #
    # E.g:
    # 1 - PciRoot(0x0)/Pci(0x2,0x0)
    # 2 - PciRoot(0x0)/Pci(0x1,0x0)/Pci(0x0,0x0)
    amount = 1 if len(acpi.split(".")) < 4 else 2

    # Whether or not we found what we were looking for.
    found = False

    for line in pci.split("\n"):
        if "pci_slot_name" in line.lower():
            slot = line.split("=")[1]
            break

    if slot:
        paths = os.listdir(f"/sys/bus/pci/devices/")

        for path in paths:
            nested = os.listdir(f"/sys/bus/pci/devices/{path}")

            if found:
                break

            if slot in nested:

                for nest in nested:
                    if found:
                        break

                    if (
                        "pcie" in nest
                        and not slot in nest
                        and slot.split(":")[0] == nest.split(":")[0]
                    ):
                        # Add PCIROOT (domain)
                        pcip += "PciRoot({})".format(hex(int(nest.split(":")[0], 16)))

                        """
                        busc  - Child bus ID
                        slotc - Child slot ID
                        busp  - Parent bus ID
                        slotp - Parent slot ID
                        """
                        busc, slotc = _get_valid(path)
                        busp, slotp = _get_valid(slot)

                        if busp == slotc:
                            busp = "0x0"

                        # As far as we can tell,
                        # The bus ID should never be equal
                        # to the slot ID.
                        if busc and busc != "0x0" and slotc != "0x0" and busc == slotp:
                            busc = "0x0"

                        pcip += f"/Pci({slotc},{busp})"

                        if amount == 2:
                            pcip += f"/Pci({slotp},{busc})"

                        found = True

        # In some cases, there won't
        # be an accommodating directory in
        # /sys/bus/pci/devices/* which will have
        # the current slot name.
        #
        # So, we format the current one, and use that.
        # This should, by default,
        # only have a single PCI path component.
        if not pcip:
            domain = hex(int(slot.split(":")[0], 16))
            bus, slot = _get_valid(slot)

            pcip += f"PciRoot({domain})/Pci({slot},{bus})"

        if pcip:
            data["PCI Path"] = pcip

    return data
