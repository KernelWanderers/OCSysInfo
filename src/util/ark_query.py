import requests

import xmltodict


def get_full_ark_url(prod_url):
    # we get the product URL from the quick search results,
    # and then append it to the base URL
    full_url = "https://ark.intel.com{0}".format(prod_url)
    return full_url


def quick_search(search_term):
    # credits to https://github.com/xiongnemo/arksearch (a fork of major/arksearch) for this code
    url = "https://ark.intel.com/libs/apps/intel/arksearch/autocomplete?" + \
          "_charset_=UTF-8" + \
          "&locale=en_us" + \
          "&currentPageUrl=https%3A%2F%2Fark.intel.com%2Fcontent%2Fwww%2Fus%2Fen%2Fark.html" + \
          "&input_query={0}"

    r = requests.get(url.format(search_term))
    return r.json()


def get_codename(ark_url):
    # we get the Ark URL from the quick search results,
    # and get the HTML data from the URL.
    # Parsing it, and then getting the codename from the HTML
    text_thing = requests.get(ark_url).content.decode("utf8")
    lines = text_thing.split("\n")
    actual_line = {"a": {}}
    for line_index in range(len(lines)):
        if 'data-key="CodeNameText"' in lines[line_index]:
            actual_line = lines[line_index + 1].strip()

    line_json = xmltodict.parse(actual_line)  # we only need to parse the one line
    codename = line_json.get("a").get("#text")  # The codename is wrapped in an <a> tag
    return codename if codename else None


def iark_search(search_term):
    results = quick_search(search_term)
    return results[0] if results else None


def simplified_name(cpu_name):
    replace_dict = {
        "(R)": "®",
        "(TM)": "™",
        "(C)": "©",
        "(P)": "℗",
        "(G)": "℠",
        "CPU": ""
    }
    result_name = cpu_name.split("@")[0].strip()
    for key, value in replace_dict.items():
        if key in result_name:
            result_name = result_name.replace(key, value)
    return result_name
