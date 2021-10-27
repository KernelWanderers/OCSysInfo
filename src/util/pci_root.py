def pci_from_acpi(raw_path):
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
