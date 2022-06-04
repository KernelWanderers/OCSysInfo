import re
from src.info import color_text


def tree(name, data, nest=1, parent="", looped={}, value="", color=True):
    """
    Internal function to properly format nested objects / lists of objects,
    and display them to the terminal (thanks, @[Dids](https://github.com/Dids)!)
    """

    spacing = ""
    sp = ""

    i = looped.get("i", 1)
    l = looped.get("l", len(data))

    if nest == 1:
        spacing = color_text("─ ", "cyan") if color else "─ "

    if isinstance(data, dict):
        if nest == 1:
            value += f"{spacing}{name}\n"

        for key in data:
            if not key:
                continue

            f = color_text("├── ", "cyan") if color else "├── "
            s = color_text("└── ", "cyan") if color else "└── "

            if len(looped):
                sp = (
                    re.sub(
                        r"├",
                        color_text("│", "cyan") if color else "│",
                        re.sub(r"─", " ", re.sub(r"└", " ", parent)),
                    )
                    + (f if i < l else s)
                )
            else:
                sp = " " * (len(parent) if parent else 2) + (f if i < l else s)

            if len(key) and isinstance(data[key], dict):
                value += f"{sp}{key}\n"
                value = tree(
                    key,
                    data[key],
                    nest=nest + 1,
                    parent=sp,
                    looped={"i": 1},
                    value=value,
                    color=color,
                )

            else:
                if i >= l:
                    value += f"{re.sub(r'├', color_text('└', 'cyan') if color else '└', sp)}{key}: {data[key]}\n"
                else:
                    value += f"{sp}{key}: {data[key]}\n"

            i += 1

    elif isinstance(data, list):
        value += f"{spacing}{name}\n"

        i = 1
        for d in data:
            if not d:
                continue

            value = tree(
                name,
                d,
                nest=nest + 1,
                parent=spacing,
                looped={"i": i, "l": len(data)},
                value=value,
                color=color,
            )
            i += 1

    return value
