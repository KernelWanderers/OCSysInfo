import json
import os
from src.info import root_dir as root


def gpu(dev, ven):
    """
    Extracts µarches matching the provided data,
    for GPUs; if possible.
    """

    if not dev or not ven:
        return

    elif "1002" in ven:
        vendor = "amd_gpu"
    elif "10de" in ven:
        vendor = "nvidia_gpu"
    else:
        return

    found = ""

    with open(os.path.join(root, "src", "uarch", "gpu", f"{vendor}.json"), "r") as file:
        data = json.loads(file.read())

        for uarch in data:
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
