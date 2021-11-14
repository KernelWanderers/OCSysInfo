# Special thanks to [Quist](https://github.com/nadiaholmquist)
# for this!
#
# They, alongside
#   - [Joshj23](https://github.com/joshj23),
#   - [Flagers](https://github.com/flagersgit)
#   - [Rusty-bits](https://github.com/rusty-bits)
#
# have helped the development team around figuring out
# how to decode specific data from DMI tables.
#
# This is all thanks to them.
def get_string_entry(string, n):
    if n == 0:
        return "Unknown"
    else:
        return string[n - 1].decode("ascii")

MEMORY_TYPE = {
    0x01: "Other",
    0x02: "UNKNOWN",
    0x03: "DRAM",
    0x04: "EDRAM",
    0x05: "VRAM",
    0x06: "SRAM",
    0x07: "RAM",
    0x08: "ROM",
    0x09: "FLASH",
    0x0A: "EEPROM",
    0x0B: "FEPROM",
    0x0C: "EPROM",
    0x0D: "CDRAM",
    0x0E: "3DRAM",
    0x0F: "SDRAM",
    0x10: "SGRAM",
    0x11: "RDRAM",
    0x12: "DDR",
    0x13: "DDR2",
    0x14: "DDR2-FB-DIMM",
    0x15: "Reserved",
    0x16: "Reserved",
    0x17: "Reserved",
    0x18: "DDR3",
    0x19: "FBD2",
    0x1A: "DDR4",
    0x1B: "LPDDR",
    0x1C: "LPDDR2",
    0x1D: "LPDDR3"
}