import re


def pci_from_acpi_osx(raw_path):
    if not raw_path:
        return

    f_path = ''

    for arg in raw_path.split(':')[1].split('/'):
        if '@' in arg.lower():
            pcip = arg.split('@')[1].split(',')
            pcif, pcis = pcip + ['#']

            if 'pci' in arg.lower():
                f_path += f'PciRoot(0x{pcif[0]})'
                continue

            n = '0x' + pcif[0]
            n += pcif[1] if len(pcif) > 1 and str(
                pcif[1]) != '0' else ''

            k = '0x0'

            if pcis != '#':
                k = f'0x{pcis}'

            f_path += f'/Pci({n},{k})'

    return f_path


def pci_from_acpi_win(wmi, name):

    try:
        # Thank you to DhinakG for this.
        # See: https://github.com/USBToolBox/tool/blob/ba3bb1238c0b552cb8066e29c5dc83b5e8faae32/Windows.py#L46
        raw_path = wmi.query(f'SELECT * FROM Win32_PnPEntity WHERE Name=\'{name}\'')[
            0].GetDeviceProperties(['DEVPKEY_Device_LocationPaths'])[0][0].Data
    except:
        return {}

    if not raw_path:
        return

    data = {
        'PCI Path': '',
        'ACPI Path': ''
    }

    pci, acpi = raw_path

    if pci != '#':
        path = ''

        for arg in pci.split('#'):
            digit = re.search(r'(?<=\()(\d*|\w*)+(?=\))', arg)

            if not digit:
                path = None
                break

            digit = digit.group()

            if 'pciroot' in arg.lower():
                path += f'PciRoot({hex(int(digit, 16))})'
                continue

            path += f'/Pci({hex(int(digit[0:2], 16))},{hex(int(digit[2:], 16))})'

        data['PCI Path'] = path

    if acpi != '#':
        path = ''

        for arg in acpi.split('#'):
            if '_SB' in arg:
                path += '\_SB'
                continue

            prop = re.search(r'(?<=\()(\w*|\d*)+(?=\))', arg)

            if not prop:
                path = None
                break

            path += f'.{prop.group()}'

        data['ACPI Path'] = path

    return data
