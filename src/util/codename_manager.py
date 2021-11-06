import ark_query


# WIP
class CodenameManager:
    def __init__(self, name, vendor):
        self.name = name
        self.vendor = vendor
        self.codename = None
        self.codename_init()

    def codename_init(self):
        if 'intel' in self.vendor.lower():
            self.codename_intel()
        elif 'amd' in self.vendor.lower():
            self.codename_amd()
        elif 'apple' in self.vendor.lower():
            self.codename_apple_arm()
        else:
            return

    def codename_intel(self):
        search_term = ark_query.simplified_name(self.name)
        ark_url = ark_query.get_full_ark_url(ark_query.iark_search(search_term).get("prodUrl"))
        self.codename = ark_query.get_codename(ark_url)
        return ark_query.get_codename(ark_url)

    def codename_amd(self):
        raise NotImplementedError

    def codename_apple_arm(self):
        raise NotImplementedError
