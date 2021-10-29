import re


def pci_from_acpi_osx(raw_path):
    if not raw_path:
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


def pci_from_acpi_win(wmi, instance_id):

    try:
        # Thank you to DhinakG for this.
        # See: https://github.com/USBToolBox/tool/blob/ba3bb1238c0b552cb8066e29c5dc83b5e8faae32/Windows.py#L46
        raw_path = (
            wmi.query(
                f"SELECT * FROM Win32_PnPEntity WHERE PNPDeviceID = '{instance_id}'")[0]
            .GetDeviceProperties(["DEVPKEY_Device_LocationPaths"])[0][0]
            .Data
        )
    except Exception:
        return {}

    if not raw_path:
        return

    data = {"PCI Path": "", "ACPI Path": ""}

    devices = raw_path


    for device in devices:
        if not 'acpi' in device.lower() and 'pci' in device.lower():
            path = ""

            for arg in device.split("#"):
                if "usb" in arg.lower():
                    break

                # Thank you to DhinakG for this.
                digit = arg[:-1].split("(")[1]

                if not digit:
                    path = None
                    return

                if "pciroot" in arg.lower():
                    path += f"PciRoot({hex(int(digit, 16))})"
                    continue

                path += f"/Pci({hex(int(digit[0:2], 16))},{hex(int(digit[2:], 16))})"

            data["PCI Path"] = path

        elif 'acpi' in device.lower():
            path = ""

            for arg in device.split("#"):
                if "_SB" in arg:
                    path += "\_SB"
                    continue

                try:
                    # Thank you to DhinakG for this.
                    _acpi, val = arg[:-1].split("(")
                except Exception:
                    path = None
                    break

                if _acpi.lower() == 'pci':
                    path = None
                    break

                path += f".{val}"

            data["ACPI Path"] = path
    
    return data
