from ctypes import Structure, c_ulong
from .guid import GUID


class DEVPROPKEY(Structure):
    """
    Source: https://github.com/tpn/winsdk-10/blob/master/Include/10.0.10240.0/um/devpropdef.h#L118-L124
    """
    _fields_ = [
        ("fmtid", GUID),
        ("pid", c_ulong)
    ]
