import src.util.ark_query as ark_query
from src.util.wc_amd_query import parse_codename


class CodenameManager:
    """
    A WIP manager to obtain the codename value of the current CPU.

    Currently, this is only for Intel CPUs.
    """

    def __init__(self, name, vendor):
        self.name = name
        self.vendor = vendor or ""
        self.codename = None
        self.codename_init()

    def codename_init(self):
        # 'Unified' function, determing which codename function to call.

        if "intel" in self.vendor.lower():
            self.codename_intel()
        elif "amd" in self.vendor.lower():
            self.codename_amd()
        elif "apple" in self.vendor.lower():
            self.codename_apple_arm()
        else:
            return

    def codename_intel(self):
        search_term = ark_query.simplified_name(self.name)
        found_term = ark_query.iark_search(search_term)

        if not found_term:
            return None

        ark_url = ark_query.get_full_ark_url(
            found_term.get("prodUrl")
        )
        value = ark_query.get_codename(ark_url).replace("Products formerly ", "")

        self.codename = value
        return value

    def codename_amd(self):
        data = parse_codename(self.name)

        if data:
            self.codename = data.get("Codename", None) or data.get(
                "Microarchitecture", None
            )
            return data

    def codename_apple_arm(self):
        raise NotImplementedError
