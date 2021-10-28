import re


def pci_from_acpi_osx(raw_path):
    if not raw_path:
        return {}

    p_path = ''
    a_path = ''

    for arg in raw_path.split(':')[1].split('/')[1:]:
        if not '@' in arg.lower():
            a_path += f'\{arg}'
        else:
            acpi = arg.split('@')[0]
            a_path += f'.{acpi}'

            _pcip = arg.split('@')[1].split(',')
            _pcip = re.findall(r'..', _pcip[0])
            pcip = []

            for i in _pcip:
                pcip.append(re.sub(r'0', '', i))

            if 'pci' in arg.lower():
                p_path += 'PciRoot(0x{})'.format(pcip[0] if pcip else '0')
                continue

            temp = '/Pci('

            if not pcip:
                temp += '0x0,0x0)'

            for n in range(len(pcip)):
                if n == (len(pcip) - 1) and pcip[n] == '':
                    temp += f'0x0)'
                elif n == (len(pcip) - 1):
                    temp += f'0x{pcip[n]})'
                elif pcip[n] != '':
                    temp += f'0x{pcip[n]},'

            p_path += temp

    return {
        'PCI Path': p_path,
        'ACPI Path': a_path
    }


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
        'p_path Path': '',
        'ACPI Path': ''
    }

    pci, acpi = raw_path

    if p_path != '#':
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

        data['p_path Path'] = path

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
