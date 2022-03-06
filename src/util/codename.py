from src.info import root_dir as root


def gpu(dev, ven):
    """
    Extracts µarches matching the provided data,
    for GPUs; if possible.
    """

    if not dev or not ven:
        return

    elif "1002" in ven:
        from src.uarch.gpu.amd_gpu import amd
        items = amd
    elif "10de" in ven:
        from src.uarch.gpu.nvidia_gpu import nvidia
        items = nvidia
    else:
        return

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

    return found
