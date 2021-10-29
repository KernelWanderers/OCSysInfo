import json
import os
from root import root


def codename(data, extf, family, extm, model, stepping=None, laptop=False):
    """
    Extracts µarches matching the provided data,
    and takes care of validating which codename is
    the most accurate guess.
    """

    vals = []
    for arch in data:

        if (
            extf.lower() == arch.get("ExtFamily", "").lower()
            and family.lower() == arch.get("BaseFamily", "").lower()
            and extm.lower() == arch.get("ExtModel", "").lower()
            and model.lower() == arch.get("BaseModel", "").lower()
        ):

            valid_stepping = (
                stepping and stepping.lower() in arch.get("Stepping", "").lower()
            )

            if (
                laptop
                and arch.get("Laptop", None)
                and valid_stepping
                or stepping
                and arch.get("Stepping", None)
                and valid_stepping
            ):
                vals = [arch.get("Codename")]
                if laptop and arch.get("Laptop", None):
                    break

                continue

            vals.append(arch.get("Codename"))

    return vals if vals else ["Unknown"]


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
