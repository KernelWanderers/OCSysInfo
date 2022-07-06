import requests

from src import info
from src.info import color_text
from src.util.debugger import Debugger as debugger

class PCIIDs:
    """
    Abstraction for scraping the https://devicehunt.com website.
    If data is unavailable from the aforementioned website, it will attempt to scrape https://pci-ids.ucw.cz.

    Thank you to @[CorpNewt](https://github.com/CorpNewt) for allowing us to copy over their own
    implementation of scraping a website's response.
    """

    def get_item(self, dev: str, ven: str = "any", types="pci") -> dict or None:
        data = self.get_item_dh(dev, ven, types)

        if not data and ven != "any":
            data = self.get_item_pi(dev, ven)

        return data or {}

    def get_item_dh(self, dev: str, ven: str = "any", types="pci") -> dict or None:
        debugger.log_dbg(color_text(
            f"--> [DH/PID]: Attempting to find a match for:" +
            f"\n\t* Device ID: {dev}" +
            f"\n\t* Vendor ID: {ven}", 
            "yellow"
        ))

        content = requests.get(
            "https://devicehunt.com/search/type/{}/vendor/{}/device/{}".format(
                types, ven.upper(), dev.upper()
            ), timeout=info.requests_timeout, headers=info.useragent_header
        )

        if content.status_code != 200:
            debugger.log_dbg(color_text(
                "--> [DH/PID]: Failed to fetch device with provided data – ignoring!\n",
                "red"
            ))

            return None

        lines = content.text.split("\n")
        device = {}
        caught = None

        for line in lines:
            cond = "--type-device" in line.lower()
            if cond or ("--type-vendor" in line.lower() and caught):
                device["device" if cond else "vendor"] = lines[
                    lines.index(line.lower()) + 1
                ].split("<")[0]
                caught = device

        if device:
            debugger.log_dbg(color_text(
                f"--> [DH/PID]: Obtained device '{device.get('device')}' using the following data:" +
                f"\n\t* Device ID: {dev}" +
                f"\n\t* Vendor ID: {ven}" +
                f"\n\t* Type: {types}\n",
                "green"
            ))

            return device

    def get_item_pi(self, dev: str, ven: str = "any") -> dict or None:
        debugger.log_dbg(color_text(
            f"--> [DH/PID]: Attempting to find a match for:" +
            f"\n\t* Device ID: {dev}" +
            f"\n\t* Vendor ID: {ven}", 
            "yellow"
        ))

        content = requests.get(
            "https://pci-ids.ucw.cz/read/PC/{}/{}".format(ven, dev),
            timeout=info.requests_timeout,
            headers=info.useragent_header
        )

        if content.status_code != 200:
            debugger.log_dbg(color_text(
                "--> [DH/PID]: Failed to fetch device with provided data – ignoring!\n",
                "red"
            ))

            return None

        device = ""

        for line in content.text.split("\n"):
            if "itemname" in line.lower() and ">name" in line.lower():
                device = line.split("Name: ")[1]

        if device:
            debugger.log_dbg(color_text(
                f"--> [DH/PID]: Obtained device '{device}' using the following data:" +
                f"\n\t* Device ID: {dev}" +
                f"\n\t* Vendor ID: {ven}" +
                f"\n\t* Type: PCI\n",
                "green"
            ))

            return { "device": device }
