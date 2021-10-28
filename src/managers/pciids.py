import requests


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

        return data or None

    def get_item_dh(self, dev: str, ven: str = "any", types="pci") -> dict or None:
        content = requests.get(
            "https://devicehunt.com/search/type/{}/vendor/{}/device/{}".format(
                types, ven.upper(), dev.upper()
            )
        )

        if content.status_code != 200:
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

        return device or None

    def get_item_pi(self, dev: str, ven: str = "any") -> dict or None:
        content = requests.get("https://pci-ids.ucw.cz/read/PC/{}/{}".format(ven, dev))

        if content.status_code != 200:
            return None

        device = ""

        for line in content.text.split("\n"):
            if "itemname" in line.lower() and ">name" in line.lower():
                device = line.split("Name: ")[1]

        return {"device": device} if device else None
