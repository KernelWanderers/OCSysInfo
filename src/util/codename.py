from src.info import color_text
from src.util.debugger import Debugger as debugger

def gpu(dev, ven):
    """
    Extracts µarches matching the provided data,
    for GPUs; if possible.
    """

    if not dev or not ven:
        debugger.log_dbg(color_text(
            "--> [GpuCodenameManager]: No device or vendor ID provided! Cannot determine GPU codename – critical!",
            "red"
        ))

        return

    elif "1002" in ven:
        from src.uarch.gpu.amd_gpu import amd
        items = amd

        debugger.log_dbg(color_text(
            "--> [GpuCodenameManager]: AMD vendor detected!",
            "green"
        ))

    elif "10de" in ven:
        from src.uarch.gpu.nvidia_gpu import nvidia
        items = nvidia

        debugger.log_dbg(color_text(
            "--> [GpuCodenameManager]: NVIDIA vendor detected!",
            "green"
        ))
    else:
        debugger.log_dbg(color_text(
            "--> [GpuCodenameManager]: Couldn't determine vendor – critical!",
            "red"
        ))

        return

    debugger.log_dbg(color_text(
        "--> [GpuCodenameManager]: Preliminary checks passed; attempting to fetch codename...",
        "yellow"
    ))

    found = ""

    for uarch in items:
        if found:
            break

        for id in uarch.get("IDs", []):
            if (
                id.get("Vendor", "").lower() == ven.lower()
                and id.get("Device", "").lower() == dev.lower()
            ):
                found = uarch.get("Codename")
                break

    if found:
        debugger.log_dbg(color_text(
            f"--> [GpuCodenameManager]: Successfully obtained codename '{found}'!",
            "green"
        ))

    return found
