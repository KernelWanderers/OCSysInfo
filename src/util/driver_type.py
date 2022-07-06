import wmi
import subprocess
from src.info import color_text
from ctypes import c_ulong
from src.cfgmgr32.core.cfgmgr32 import CM32
from src.cfgmgr32.util.get_info import get_info
from src.util.debugger import Debugger as debugger

cm32 = CM32()

PS2_KEYBOARD_IDS = [
    "PNP0303",
    "PNP030B",
    "PNP0320",
]

PS2_MOUSE_IDS = [
    "PNP0F03",
    "PNP0F0B",
    "PNP0F0E",
    "PNP0F12",
    "PNP0F13",
]

def __is_ps2_keyboard(ids):
    for id in PS2_KEYBOARD_IDS:
        if id in ids:
            return True

    return False

def __is_ps2_mouse(ids):
    for id in PS2_MOUSE_IDS:
        if id in ids:
            return True

    return False


def protocol(pnp_id, logger, _wmi=wmi.WMI()):
    debugger.log_dbg(color_text(
        "--> [WINDOWS]: Attempting to determine connection protocol...",
        "yellow"
    ))

    pdnDevInst = c_ulong()

    status = cm32.CM_Locate_DevNodeA(
        pdnDevInst,
        pnp_id.encode("UTF8")
    ).get("code")

    if status != 0x0:
        debugger.log_dbg(color_text(
            f"--> [WINDOWS]: Failed to determine connection protocol! Status code: {status}. — (WMI)\n",
            "red"
        ))

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
        debugger.log_dbg(color_text(
            f"--> [WINDOWS]: Failed to determine connection protocol! Status code: {status}. — (WMI)\n",
            "red"
        ))

        logger.warning(
            f"Failed to determine connection protocol of ambiguous device (at parent) at status code {stat} (WMI) - Non-critical, ignoring",
            __file__,
        )

        return stat

    device_data = get_info(pdnDevInst, cm32)
    parent_data = get_info(parent, cm32)

    dev_name = device_data.get("name", "")
    prt_name = parent_data.get("name", "")

    dev_driver = device_data.get("driver_desc", "")
    prt_driver = parent_data.get("dirver_desc", "")

    if (
        "i2c" in dev_name.lower() or 
        "i2c" in prt_name.lower()
    ):
        debugger.log_dbg(color_text(
            f"--> [WINDOWS]: Returned I2C for {dev_name}!\n",
            "green"
        ))

        return "I2C"

    elif (
        "usb" in dev_driver.lower() or 
        "usb" in prt_driver.lower()
    ):
        debugger.log_dbg(color_text(
            f"--> [WINDOWS]: Returned USB for {dev_name}!\n",
            "green"
        ))

        return "USB"

    compatible_ids = device_data.get("compatible_ids", "").lower()

    if __is_ps2_keyboard(compatible_ids):
        debugger.log_dbg(color_text(
            f"--> [WINDOWS]: Returned PS/2 for {dev_name}!\n",
            "green"
        ))

        return "PS/2"

    if not __is_ps2_mouse(compatible_ids):
        return

    smbus_driver = None

    for entity in _wmi.instances("Win32_PnPEntity"):
        compat_id = entity.wmi_property("CompatibleID").value

        if (
            compat_id and
            type(compat_id) != str and
            "PCI\\CC_0C0500" in compat_id
        ):

            smbus_driver = entity
            break

    if smbus_driver:
        name = smbus_driver.wmi_property("Name").value

        if (
            (
                "synaptics" in name.lower() and
                "synaptics" in dev_name.lower()
            ) or
            (
                "elans" in name.lower() and
                "elans" in dev_name.lower()
            )
        ):
            debugger.log_dbg(color_text(
                f"--> [WINDOWS]: Returned SMBus for {dev_name}!\n",
                "green"
            ))

            return "SMBus"

    debugger.log_dbg(color_text(
        f"--> [WINDOWS]: Returned PS/2 for {dev_name}!\n",
        "green"
    ))

    return "PS/2"
