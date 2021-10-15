import sys

required = {
    'dicttoxml',
    'requests',
    'distro',
    'pyobjc' if sys.platform.lower() == "darwin" else None
}
