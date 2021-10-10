import re


def tree(name: str, data: list[dict] or dict, nest=1, parent="", looped: dict = {}):
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
            print(f"{spacing}{name}")

        for key in data:

            if len(looped):
                sp = re.sub(r'├', '│', re.sub(r'─', ' ', re.sub(r'└',
                            ' ', parent))) + ("├── " if i < l else '└── ')
            else:
                sp = " " * len(parent if len(parent) else spacing) + \
                    ("├── " if i < l else '└── ')

            if len(key) and isinstance(data[key], dict):
                print(f"{sp}{key}")
                tree(key, data[key], nest=nest+1,
                     parent=sp, looped={'i': 1})

            else:
                if i >= l:
                    print(f"{re.sub(r'├', '└', sp)}{key}: {data[key]}")
                else:
                    print(f"{sp}{key}: {data[key]}")

            i += 1

    elif isinstance(data, list):
        print(f"{spacing}{name}")
        i = 1
        for d in data:
            tree(name, d, nest=nest+1, parent=spacing,
                 looped={'i': i, 'l': len(data)})
            i += 1