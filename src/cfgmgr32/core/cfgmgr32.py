from ctypes import WinDLL, c_ulong, c_char_p, byref, c_buffer, sizeof

cfgmgr = WinDLL("cfgmgr32.dll")


class CM32:
    def __init__(self):
        pass

    def CM_Locate_DevNodeA(
        self,
        pdnDevInst=c_ulong(),
        pDeviceID=c_char_p(),
        ulFlags=c_ulong(0),
    ):
        status = cfgmgr.CM_Locate_DevNodeA(
            byref(pdnDevInst),
            pDeviceID,
            ulFlags,
        )

        return {
            "status": "success",
            "code": status
        } if status == 0x0 \
        else {
            # Something went wrong.
            "status": "failure",
            "code": status,
            "reason": "error"
        }

    def CM_Get_Parent(
        self,
        pdnDevInst=c_ulong(),
        dnDevInst=c_ulong(),
    ):
        status = cfgmgr.CM_Get_Parent(
            byref(pdnDevInst),
            dnDevInst,
            c_ulong(0),
        )

        return {
            "status": "success",
            "code": status
        } if status == 0x0 \
        else {
            # Something went wrong.
            "status": "failure",
            "code": status,
            "reason": "error"
        }

    def CM_Get_DevNode_PropertyW(
        self,
        dnDevInst=c_ulong(),
        propKey=None,
        propType=c_ulong(),
        propBuff=None,
        propBuffSize=c_ulong(0)
    ):
        if propKey is None:
            return {}

        status = cfgmgr.CM_Get_DevNode_PropertyW(
            dnDevInst,
            byref(propKey),
            byref(propType),
            propBuff,
            byref(propBuffSize),
            c_ulong(0),
        )

        # We ran out of memory
        if status == 0x02:
            return {
                "status": "failure",
                "code": status,
                "reason": "out of memory"
            }

        # The buffer isn't big enough...
        # we can just iterate again with a fixed-length buffer.
        #
        # More error codes here: https://github.com/tpn/winsdk-10/blob/master/Include/10.0.10240.0/um/cfgmgr32.h#L4508
        if status == 0x1A or propBuff is None:
            return self.CM_Get_DevNode_PropertyW(
                dnDevInst,
                propKey,
                propType,
                propBuff=c_buffer(b"", sizeof(c_ulong) * propBuffSize.value),
                propBuffSize=propBuffSize,
            )

        return {
            "status": "success",
            "data": {
                "type": propType,
                "buff": propBuff,
                "size": propBuffSize
            },
            "devInst": dnDevInst,
            "code": status
        }  if status == 0x0 \
        else {
            # Something went wrong.
            "status": "failure",
            "code": status,
            "reason": "error"
        }
