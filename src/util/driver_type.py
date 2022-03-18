import subprocess

smbus_driver = subprocess.check_output(["powershell", "Get-WmiObject", "-Class", "Win32_PnPEntity", "|", "Where",
                                        "-Property", "CompatibleID", "-Contains", "-Value", '"PCI\CC_0C0500"', "|", "Select", "Name"]).decode().lower()

smbus_elan = len(smbus_driver) > 0 and "elans" in smbus_driver
smbus_syna = len(smbus_driver) > 0 and "synaptics" in smbus_driver

def is_usb(inf, service):
    return inf.split(".")[0] in ("msmouse", "keyboard", "input") and service in ("mouhid", "kbdhid", "hidusb")


def is_i2c(inf, service):
    return "hidi2c" in inf and service == "hidi2c"


def is_smbus(desc):
    return ("synaptics" in desc and smbus_syna) or ("elans" in desc and smbus_elan)


def is_ps2(service):
    return "i8042" in service.lower()


def driver_type(pnp_id, desc, w):
    pnp_entity = w.query(f"SELECT * FROM Win32_PnPEntity WHERE PNPDeviceID = '{pnp_id}'")[
        0].GetDeviceProperties(["DEVPKEY_Device_DriverInfPath", "DEVPKEY_Device_Service", "DEVPKEY_Device_Stack"])

    protocol = None

    for instances in pnp_entity:
        if type(instances) == int:
            continue

        inf = instances[0].Data.lower()
        service = instances[1].Data.lower()

        if is_usb(inf, service):
            protocol = "USB"
        elif is_i2c(inf, service):
            protocol = "I2C"
        elif is_ps2(service):
            if is_smbus(desc.lower()):
                protocol = "SMBus"
            else:
                protocol = "PS/2"

    return protocol