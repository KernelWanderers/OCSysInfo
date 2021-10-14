import re


def tree(name, data, nest=1, parent="", looped={}, value=""):
    """
    Internal function to properly format nested objects / lists of objects,
    and display them to the terminal (thanks, @[Dids](https://github.com/Dids)!)
    """

    spacing = ""
    sp = ""

    i = looped.get('i', 1)
    l = looped.get('l', len(data))

    if nest == 1:
        spacing = "─ "

    if isinstance(data, dict):
        if nest == 1:
            value += f"{spacing}{name}\n"

        for key in data:

            if len(looped):
                sp = re.sub(r'├', '│', re.sub(r'─', ' ', re.sub(r'└',
                            ' ', parent))) + ("├── " if i < l else '└── ')
            else:
                sp = " " * len(parent if len(parent) else spacing) + \
                    ("├── " if i < l else '└── ')

            if len(key) and isinstance(data[key], dict):
                value += f"{sp}{key}\n"
                value = tree(key, data[key], nest=nest+1,
                              parent=sp, looped={'i': 1}, value=value)

            else:
                if i >= l:
                    value += f"{re.sub(r'├', '└', sp)}{key}: {data[key]}\n"
                else:
                    value += f"{sp}{key}: {data[key]}\n"

            i += 1

    elif isinstance(data, list):
        value += f"{spacing}{name}\n"

        i = 1
        for d in data:
            value = tree(name, d, nest=nest+1, parent=spacing,
                          looped={'i': i, 'l': len(data)}, value=value)
            i += 1

    return value
