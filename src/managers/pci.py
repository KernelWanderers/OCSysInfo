import json
import sys
import re
from requests import get


"""
Instance which manages the parsing, and look-up, of PCI IDs from the pciids repository.
"""
class PCI:
    def __init__(self):
        sys.setrecursionlimit(10000)
        content = get(
            'https://raw.githubusercontent.com/pciutils/pciids/master/pci.ids').text
        data = re.sub(r'(?<=[^\t])\n(?=[a-zA-Z0-9]+)', '\n\n', content)
        parent = {"parent": "root", "children": []}

        for line in data.split('\n\n'):
            parent = self.parse(line.split('\n'), parent=parent)

        print(self.search("67b1", parent))

    def parse(self, data, tc=0, parent={'parent': 'root', 'children': []}, i=0):
        """
        If we're done with traversing the list, return the result.
        """
        if len(data) <= i:
            return parent

        if "#" in data[i]:
            return self.parse(data, tc=tc, parent=parent, i=(i + 1))

        # Current amount of tabs (to indicate the indentation level)
        count = data[i].count('\t')

        # A look-ahead to see if we need to traverse over the current parent to find its children.
        ahead = data[i + 1].count('\t') if len(data) > i + 1 else count

        """
        Lenghty conditional checking if:
            - Current indentation level is greater than the previous (to indicate it's a child of the previous value)
            - If the value exists either in the current parent;
            - Or in one of its children (so that we get no duplicates.)
        """
        if count > tc or data[i].lower() in parent.get('parent').lower() or any(data[i].lower() in x for x in parent.get('children')):
            return self.parse(data, tc=tc, parent=parent, i=(i + 1))

        """
        If the current indentation's level is equal to the previous,
        this would indicate a child of the parent node, 
        so add it to its children nodes.
        """
        if count == tc:
            obj = {"parent": data[i][count:], "children": []}

            if ahead > count:
                self.parse(data, tc=ahead, i=(i + 1), parent=obj)

            parent.get('children').append(obj)
            return self.parse(data, tc=tc, parent=parent, i=(i+1))

        return parent

    def search(self, id, ids={}, i=0, ven=''):
        """
        If we've looped through the first node, and found nothing,
        continue over to the second set of children of each node.
        """
        if len(ids.get('children')) and len(ids.get('children')) <= i:
            res = []
            for index in range(len(ids.get('children'))):
                _res = self.search(id, ids.get('children')
                                   [index], i=0, ven=ven)
                if len(_res):
                    _res.insert(0, ids.get('children')[index].get('parent'))
                    res.append(_res)

            return res

        elif not len(ids.get('children')):
            return []

        items = ids.get('children')[i]

        """
        If we're looping over the root's children (vendors),
        and vendor id specified, check if it's a match - if it is:
        loop over that node's children only.
        """
        if ids.get('parent') == 'root' and len(ven):
            if ven.lower() in items.get('parent').lower():
                res = self.search(id, items, i=0, ven=ven)
                return [items.get('parent'), *res] if len(res) else []
            else:
                return self.search(id, ids, i=(i + 1), ven=ven)

        """
        In case it doesn't find the node we're looking for, yet,
        keep looking.
        """
        if not id.lower() in items.get('parent').lower():
            return self.search(id, ids, i=(i + 1), ven=ven)

        """
        If it finds a node matching the supplied argument,
        return a list with the item inside of it.
        """
        if id.lower() in items.get('parent').lower():
            return [items.get('parent'), *self.search(id, ids, i=(i + 1), ven=ven)]

        """
        If no condition is met, return an empty list.
        """
        return []

p = PCI()