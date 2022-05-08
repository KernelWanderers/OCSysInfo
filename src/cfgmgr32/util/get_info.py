from ctypes import c_ulong, c_ushort
from src.cfgmgr32.core.cfgmgr32 import CM32
from src.cfgmgr32.data.props import props
from src.cfgmgr32.structs.devpropkey import DEVPROPKEY
from src.cfgmgr32.structs.guid import GUID


def get_info(pdnDevInst=c_ulong(), cm32=CM32()):
    re_data = {}

    for prop in props:
        try:
            name = prop[0]
            mGUID = GUID(
                Data1=c_ulong(prop[1]),
                Data2=c_ushort(prop[2]),
                Data3=c_ushort(prop[3]),
                Data4=bytes(prop[4]),
            )

            dpkey = DEVPROPKEY(
                fmtid=mGUID,
                pid=c_ulong(prop[5]),
            )

            data = cm32.CM_Get_DevNode_PropertyW(
                pdnDevInst,
                dpkey,
            )

            buff = data.get("data", {}).get("buff")

            if not buff:
                continue

            re_data[name] = buff.raw.decode().replace(
                " ", "").replace("\x00", "")
        except Exception as e:
            raise e

    return re_data
