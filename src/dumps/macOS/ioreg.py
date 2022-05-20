# Credits to @[DhinakG](https://github.com/DhinkaG) for allowing us to copy over their `ioreg.py` abstraction implementation from OpenCore-Legacy-Patcher:
# https://github.com/dortania/OpenCore-Legacy-Patcher/blob/f6ef7583eedc706e2bb70550fe847601ef258fcd/resources/ioreg.py

import objc
from typing import NewType, Union
from CoreFoundation import CFRelease, kCFAllocatorDefault
from Foundation import NSBundle
from PyObjCTools import Conversion


IOKit = NSBundle.bundleWithIdentifier_("com.apple.framework.IOKit")

io_name_t_ref_out = b"[128c]"  # io_name_t is char[128]
const_io_name_t_ref_in = b"r*"
CFStringRef = b"^{__CFString=}"
CFDictionaryRef = b"^{__CFDictionary=}"
CFAllocatorRef = b"^{__CFAllocator=}"

# https://developer.apple.com/library/archive/documentation/Cocoa/Conceptual/ObjCRuntimeGuide/Articles/ocrtTypeEncodings.html
functions = [
    ("IORegistryEntryCreateCFProperties", b"IIo^@" + CFAllocatorRef + b"I"),
    ("IORegistryEntryGetLocationInPlane", b"II" + const_io_name_t_ref_in + b"o" + io_name_t_ref_out),
    ("IORegistryEntryGetRegistryEntryID", b"IIo^Q"),
    ("IORegistryEntryCreateCFProperty", b"@I" + CFStringRef + CFAllocatorRef + b"I"),
    ("IORegistryEntryGetParentEntry", b"IIr*o^I"),
    ("IOServiceGetMatchingServices", b"II" + CFDictionaryRef + b"o^I"),
    ("IORegistryEntryIDMatching", CFDictionaryRef + b"Q"),
    ("IORegistryEntryFromPath", b"II*"),
    ("IORegistryEntryGetPath", b"II" + const_io_name_t_ref_in + b"o" + io_name_t_ref_out),
    ("IOServiceNameMatching", CFDictionaryRef + b"r*"),
    ("IOObjectConformsTo", b"II" + const_io_name_t_ref_in),
    ("IOServiceMatching", CFDictionaryRef + b"r*"),
    ("IOObjectRelease", b"II"),
    ("IOIteratorNext", b"II"),
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

kIOMasterPortDefault = NULL
kNilOptions = NULL

# IOKitLib.h
kIORegistryIterateRecursively = 1
kIORegistryIterateParents = 2


# kern_return_t IORegistryEntryCreateCFProperties(io_registry_entry_t entry, CFMutableDictionaryRef * properties, CFAllocatorRef allocator, IOOptionBits options);
def IORegistryEntryCreateCFProperties(entry, properties, allocator, options):
    raise NotImplementedError

# kern_return_t IORegistryEntryGetLocationInPlane(io_registry_entry_t entry, const io_name_t plane, io_name_t location);
def IORegistryEntryGetLocationInPlane(entry, plane, location):
    raise NotImplementedError


# CFTypeRef IORegistryEntryCreateCFProperty(io_registry_entry_t entry, CFStringRef key, CFAllocatorRef allocator, IOOptionBits options);
def IORegistryEntryCreateCFProperty(entry, key, allocator, options):
    raise NotImplementedError

# kern_return_t IORegistryEntryGetParentEntry(io_registry_entry_t entry, const char *plane, io_registry_entry_t parent);
def IORegistryEntryGetParentEntry(entry, plane, parent):
    raise NotImplementedError


# kern_return_t IORegistryEntryGetRegistryEntryID(io_registry_entry_t entry, uint64_t * entryID);
def IORegistryEntryGetRegistryEntryID(entry, entryID):
    raise NotImplementedError


# io_registry_entry_t IORegistryEntryFromPath(mach_port_t masterPort, io_name_t path);
def IORegistryEntryFromPath(masterPort, path):
    raise NotImplementedError


# kern_return_t IORegistryGetPath(io_registry_entry_t entry, const io_name_t plane, io_string_t path);
def IORegistryEntryGetPath(entry, plane, path):
    raise NotImplementedError


# kern_return_t IOServiceGetMatchingServices(mach_port_t masterPort, CFDictionaryRef matching CF_RELEASES_ARGUMENT, io_iterator_t * existing);
def IOServiceGetMatchingServices(masterPort, matching, existing):
    raise NotImplementedError


# CFMutableDictionaryRef IORegistryEntryIDMatching(uint64_t entryID);
def IORegistryEntryIDMatching(entryID):
    raise NotImplementedError


# CFMutableDictionaryRef IOServiceNameMatching(const char * name);
def IOServiceNameMatching(name):
    raise NotImplementedError


# CFMutableDictionaryRef IOServiceMatching(const char * name);
def IOServiceMatching(name):
    raise NotImplementedError

# boolean_t IOObjectConformsTo(io_object_t object, const char *className);
def IOObjectConformsTo(object, className):
    raise NotImplementedError


# kern_return_t IOObjectRelease(io_object_t object);
def IOObjectRelease(object):
    raise NotImplementedError


# io_object_t IOIteratorNext(io_iterator_t iterator);
def IOIteratorNext(iterator):
    raise NotImplementedError


objc.loadBundleFunctions(IOKit, globals(), functions)
objc.loadBundleVariables(IOKit, globals(), variables)


def ioiterator_to_list(iterator):
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


def ioname_t_to_str(name):
    return name.partition(b"\0")[0].decode()