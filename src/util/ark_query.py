# Copyright 2016 Major Hayden
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
#

import requests
import xmltodict

from src import info
from src.info import color_text
from src.util.debugger import Debugger as debugger


def get_full_ark_url(prod_url):
    """
    Method to obtain the product URL from the quick search results,
    and append it to the base URL.
    """

    full_url = "https://ark.intel.com{0}".format(prod_url)

    return full_url


def quick_search(search_term):
    # Credits to https://github.com/xiongnemo/arksearch (a fork of major/arksearch) for this.
    url = (
        "https://ark.intel.com/libs/apps/intel/arksearch/autocomplete?"
        + "_charset_=UTF-8"
        + "&locale=en_us"
        + "&currentPageUrl=https%3A%2F%2Fark.intel.com%2Fcontent%2Fwww%2Fus%2Fen%2Fark.html"
        + "&input_query={0}"
    )

    try:
        r = requests.get(
            url.format(search_term), 
            headers=info.useragent_header, 
            timeout=info.requests_timeout
        ).json()

        return r
    except Exception as e:
        if isinstance(e, requests.ConnectionError):
            return
        else:
            raise e


def get_codename(ark_url, tried=False):
    """
    We get the ARK URL from the quick search results,
    and obtain the HTML data.
    Parsing it, we can get the codename.
    """

    try:
        text_thing = requests.get(
            ark_url, 
            headers=info.useragent_header, 
            timeout=info.requests_timeout
        ).content.decode("utf8")
    except Exception as e:
        if isinstance(e, requests.ConnectionError):
            return
        elif isinstance(e, requests.ReadTimeout):
            debugger.log_dbg(color_text(
                "--> [iARK]: Intel's ARK page returned no data – aborting!\n",
                "red"
            ))

            return
        else:
            raise e
            
    lines = text_thing.split("\n")
    actual_line = {"a":{}}

    for line_index in range(len(lines)):
        if 'data-key="CodeNameText"' in lines[line_index]:
            actual_line = lines[line_index + 1].strip()

    if type(actual_line) != str and not tried:
        return get_codename(ark_url.replace('/us', '/fr').replace('/en', '/fr'), True)
    elif type(actual_line) != str and tried:
        return ""

    # We only need to parse the one line.
    line_json = xmltodict.parse(actual_line)

    # The codename is wrapped in an <a> tag.
    codename = line_json.get("a").get("#text")

    return codename if codename else ""


def iark_search(search_term):
    debugger.log_dbg(color_text(
        f"--> [CodenameManager]: Attempting to fetch codename for '{search_term}'...",
        "yellow"
    ))

    results = quick_search(search_term)

    return results[0] if results else None


def simplified_name(cpu_name):
    replace_dict = {
        "(R)": "®",
        "(TM)": "™",
        "(C)": "©",
        "(P)": "℗",
        "(G)": "℠",
        "CPU": "",
    }

    debugger.log_dbg(color_text(
        "--> [CodenameManager]: Adjusting CPU name for query...",
        "yellow"
    ))

    result_name = cpu_name.split("@")[0].strip()

    for key, value in replace_dict.items():
        if key in result_name:
            result_name = result_name.replace(key, value).strip()

    debugger.log_dbg(color_text(
        f"--> [CodenameManager]: Modified '{cpu_name}' to '{result_name}' for query...",
        "yellow"
    ))

    return result_name