# Credits to @[DhinakG](https://github.com/DhinkaG) for allowing us to copy over their `ioreg.py` abstraction implementation from OpenCore-Legacy-Patcher:
# https://github.com/dortania/OpenCore-Legacy-Patcher/blob/f6ef7583eedc706e2bb70550fe847601ef258fcd/resources/ioreg.py

import objc
from typing import NewType, Union
from CoreFoundation import CFRelease, kCFAllocatorDefault
from Foundation import NSBundle
from PyObjCTools import Conversion


IOKit = NSBundle.bundleWithIdentifier_("com.apple.framework.IOKit")

CFStringRef = b"^{__CFString=}"
CFDictionaryRef = b"^{__CFDictionary=}"
CFAllocatorRef = b"^{__CFAllocator=}"

# https://developer.apple.com/library/archive/documentation/Cocoa/Conceptual/ObjCRuntimeGuide/Articles/ocrtTypeEncodings.html
functions = [
    ("IORegistryEntryCreateCFProperties", b"IIo^@" + CFAllocatorRef + b"I"),
    ("IORegistryEntryCreateCFProperty", b"@I" + CFStringRef + CFAllocatorRef + b"I"),
    ("IORegistryEntryGetRegistryEntryID", b"IIo^Q"),
    ("IOServiceGetMatchingServices", b"II" + CFDictionaryRef + b"o^I"),
    ("IORegistryEntryIDMatching", CFDictionaryRef + b"Q"),
    ("IOServiceNameMatching", CFDictionaryRef + b"r*"),
    ("IOServiceMatching", CFDictionaryRef + b"r*"),
    ("IOObjectRelease", b"II"),
    ("IOIteratorNext", b"II")
]

variables = [("kIOMasterPortDefault", b"I")]

pointer = type(None)

kern_return_t = NewType("kern_return_t", int)
boolean_t = int

io_object_t = NewType("io_object_t", object)
io_name_t = bytes
io_string_t = bytes

io_registry_entry_t = io_object_t
io_iterator_t = NewType("io_iterator_t", io_object_t)

CFTypeRef = Union[int, float, bytes, dict, list]

IOOptionBits = int
mach_port_t = int
CFAllocatorType = type(kCFAllocatorDefault)

NULL = 0

kIOMasterPortDefault: mach_port_t
kNilOptions: IOOptionBits = NULL

# IOKitLib.h
kIORegistryIterateRecursively = 1
kIORegistryIterateParents = 2


# kern_return_t IORegistryEntryCreateCFProperties(io_registry_entry_t entry, CFMutableDictionaryRef * properties, CFAllocatorRef allocator, IOOptionBits options);
def IORegistryEntryCreateCFProperties(entry: io_registry_entry_t, properties: pointer, allocator: CFAllocatorType, options: IOOptionBits) -> tuple[kern_return_t, dict]:
    raise NotImplementedError

# CFTypeRef IORegistryEntryCreateCFProperty(io_registry_entry_t entry, CFStringRef key, CFAllocatorRef allocator, IOOptionBits options);
def IORegistryEntryCreateCFProperty(entry: io_registry_entry_t, key: str, allocator: CFAllocatorType, options: IOOptionBits) -> CFTypeRef:
    raise NotImplementedError

# kern_return_t IORegistryEntryGetRegistryEntryID(io_registry_entry_t entry, uint64_t * entryID)
def IORegistryEntryGetRegistryEntryID(entrY: io_registry_entry_t, entryID: pointer) -> tuple[kern_return_t, int]:
    raise NotImplementedError

# kern_return_t IOServiceGetMatchingServices(mach_port_t masterPort, CFDictionaryRef matching CF_RELEASES_ARGUMENT, io_iterator_t * existing);
def IOServiceGetMatchingServices(masterPort: mach_port_t, matching: dict, existing: pointer) -> tuple[kern_return_t, io_iterator_t]:
    raise NotImplementedError

# CFMutableDictionaryRef IORegistryEntryIDMatching(uint64_t entryID);
def IORegistryEntryIDMatching(entryID: int) -> dict:
    raise NotImplementedError

# CFMutableDictionaryRef IOServiceNameMatching(const char * name);
def IOServiceNameMatching(name: bytes) -> dict:
    raise NotImplementedError

# CFMutableDictionaryRef IOServiceMatching(const char * name);
def IOServiceMatching(name: bytes) -> dict:
    raise NotImplementedError

# kern_return_t IOObjectRelease(io_object_t object);
def IOObjectRelease(object: io_object_t) -> kern_return_t:
    raise NotImplementedError

# io_object_t IOIteratorNext(io_iterator_t iterator);
def IOIteratorNext(iterator: io_iterator_t) -> io_object_t:
    raise NotImplementedError

objc.loadBundleFunctions(IOKit, globals(), functions)
objc.loadBundleVariables(IOKit, globals(), variables)

def ioiterator_to_list(iterator: io_iterator_t) -> dict:
    item = IOIteratorNext(iterator)
    
    while item:
        yield item
        item = IOIteratorNext(iterator)
    
    IOObjectRelease(item)


def corefoundation_to_native(collection):
    if collection is None:  # nullptr
        return None
    native = Conversion.pythonCollectionFromPropertyList(collection)
    CFRelease(collection)
    return native


def ioname_t_to_str(name) -> str:
    return name.partition(b"\0")[0].decode()