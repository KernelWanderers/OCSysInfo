from ctypes import Structure, c_char, c_ulong, c_ushort


class GUID(Structure):
    """
    Source: https://github.com/tpn/winsdk-10/blob/master/Include/10.0.10240.0/shared/guiddef.h#L22-L26
    """
    _fields_ = [
        ("Data1", c_ulong),
        ("Data2", c_ushort),
        ("Data3", c_ushort),
        ("Data4", c_char * 8)
    ]
