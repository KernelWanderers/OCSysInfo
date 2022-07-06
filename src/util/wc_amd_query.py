import requests
import re

from src import info
from src.info import color_text

BASE_URL = "https://en.wikichip.org/wiki/amd"


def parse_codename(cpu_name):
    """
    Queries the AMD section from wikichip,
    parses the contents, and looks for the codename/µarch.
    """

    formatted = re.sub(
        r"(\d{1,2}?(-Core\s?)?(Processor))", "", cpu_name.replace("AMD", "")
    ).strip()

    family = ""
    model = ""

    # Format data for request properly
    if "ryzen" in formatted.lower():
        family = "_".join(formatted.split(" ")[:2]).lower()
        model = formatted.split(" ")[2].lower()
    else:
        model = formatted.lower()

    URL = ""

    if family:
        URL = f"{BASE_URL}/{family}/{model}"
    else:
        URL = f"{BASE_URL}/{model}"

    URL = URL.replace(" ", "_")

    try:
        contents = requests.get(URL, timeout=info.requests_timeout, headers=info.useragent_header).content.decode("utf-8")
    except Exception as e:
        if isinstance(e, requests.ConnectionError):
            return
        else:
            raise e
            
    data = {"Microarchitecture": "", "Codename": ""}

    try:
        data["Codename"] = re.search(
            r"(?<=\>).+(?=\<)",
            re.search(
                r"\<a\s?href=\"\/wiki\/amd\/cores\/(\w|\d)+\s?(\w|\d)+?\"[^>]+\>[^<]+?\<\/a\>",
                contents,
            ).group(),
        ).group()
    except Exception:
        pass

    try:
        data["Microarchitecture"] = re.search(
            r"(?<=\>).+(?=\<)",
            re.search(
                r"\<a\s?href=\"\/wiki\/amd\/microarchitectures\/(\w|\d)+\s?(\w|\d)+?\"[^>]+\>[^<]+?\<\/a\>",
                contents,
            ).group(),
        ).group()
    except Exception:
        pass

    try:
        if not data["Microarchitecture"]:
            data["Microarchitecture"] = re.search(
                r"(?<=\>).+(?=\<)",
                re.search(
                    r"\<a\s?href=\"\/wiki\/amd\/(\w|\d)+\s?(\w|\d)+?\s?\(microarch\)\"[^>]+\>[^<]+?\<\/a\>",
                    contents,
                ).group(),
            ).group()
    except Exception:
        pass

    if not data["Microarchitecture"] and not data["Codename"]:
        return None

    return data
