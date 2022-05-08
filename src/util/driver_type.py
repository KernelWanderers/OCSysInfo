import wmi
import subprocess
from ctypes import c_ulong
from src.cfgmgr32.core.cfgmgr32 import CM32
from src.cfgmgr32.util.get_info import get_info

cm32 = CM32()

PS2_compatible = [
    "PNP0F03",
    "PNP0F12",
    "PNP0F13",
]


def protocol(pnp_id, logger, _wmi=wmi.WMI()):
    pdnDevInst = c_ulong()

    status = cm32.CM_Locate_DevNodeA(
        pdnDevInst,
        pnp_id.encode("UTF8")
    ).get("code")

    if status != 0x0:
        logger.warning(
            f"Failed to determine connection protocol of ambiguous device at status code {status} (WMI) - Non-critical, ignoring",
            __file__,
        )
        return status

    parent = c_ulong()

    stat = cm32.CM_Get_Parent(
        parent,
        pdnDevInst,
    ).get("code")

    if stat != 0x0:
        logger.warning(
            f"Failed to determine connection protocol of ambiguous device (at parent) at status code {stat} (WMI) - Non-critical, ignoring",
            __file__,
        )
        return stat

    device_data = get_info(pdnDevInst, cm32)
    parent_data = get_info(parent, cm32)

    con_type = "UNKNOWN"

    if "i2c" in device_data.get("name", "").lower() \
            or "i2c" in parent_data.get("name").lower():
        con_type = "I2C"

    elif "usb" in device_data.get("driver_desc", "").lower() \
            or "usb" in parent_data.get("driver_desc", "").lower():
        con_type = "USB"

    else:
        compatible_ids = device_data.get("compatible_ids", "").lower()

        for id in PS2_compatible:
            if id.lower() in compatible_ids:
                compatible_ids = compatible_ids.replace(id.lower(), "")

        smbus_driver = None

        for entity in _wmi.instances("Win32_PnPEntity"):
            compat_id = entity.wmi_property("CompatibleID").value

            if compat_id and \
                    type(compat_id) != str and \
                    "PCI\\CC_0C0500" in compat_id:

                smbus_driver = entity
                break

        if smbus_driver:
            name = smbus_driver.wmi_property("Name").value

            if "synaptics" in name.lower() \
                    or "elans" in name.lower():
                return "SMBus"

        con_type = "PS/2"

    return con_type
