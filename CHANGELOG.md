<div align="center">

# OCSysInfo Changelog

</div>

## v1.0.8 (ALPHA)

* Fixed `driver_type.py` logic for PS/2 / SMBus detection
    - Previously, it wouldn't have preliminary checks for PS/2 devices, which is required to ensure that it's a PS/2 altogether.
      At that point, if it's not a PS/2 keyboard, but is a PS/2 device, we can check for the SMBus driver; if it's present, the device
      is SMBus, otherwise, it's PS/2. If it's not a PS/2 keyboard, nor a PS/2 pointing device, then it's unknown.
* Added `product` and `vendor` id extraction for Input devices on Windows (macOS is still TODO)
* Fixed logic for extracting PCI paths on Linux.
* Fixed logic for storage devices on Linux.
    - Explicitly specify drive type for NVMe devices as `NVMe`, instead of just `SSD`
* Fixed Intel's ARK page not sending data back due to broken User-Agent 


## v1.0.7

* Added self-updater module (not for binaries yet)
    - Only updates scripts that are on the `main` branch. Targets only:
        - `src/`
        - `update/`
        - `main.py`
* Fix M1 iGPU detection
    - Previous iteration wasn't able to properly identify Apple's M1 integrated graphics. This is the following information it now specifies:
        - Model name
        - Physical cores
        - Neural Engine (NE) Cores
        - Generation tag
* Pack macOS app bundle into DMG image via `create-dmg`
* Fix Intel ARK functionality
    - Sometimes, the iARK US page won't have information about a particular model (i.e. `i3 4130T`) whilst the same page in a different region might.
* Properly handle logs/dump data
    - Create dedicated directories on each platform
        - Windows: 
            - `%LOCALAPPDATA%\OCSysInfo\Logs`
            - `%LOCALAPPDATA%\OCSysInfo\Data`
        - Linux:
            - `~/.ocsysinfo/logs`
            - `~/.ocsysinfo/data`
        - macOS:
            - `~/Library/Logs/OCSysInfo`
            - `~/Library/Application Support/OCSysInfo`
* Fix PCI Path issues
    - Sometimes ACPI and/or PCI values aren't available (affected Linux)
* Fix ACPI and PCI paths being overwritten
    - Happened on macOS, for Network controllers
* Better handle offline detection
* Fix `tree.py` module visual bug
    - Use `2` as default value if `parent` isn't available
* Refactor hardware manager
    - Assign dictionary keys in each method, if everything goes according to logic
* Fix XML dump functionality
    - Use custom fork of `dicttoxml`, where the `collections` issue was fixed.
* Added OS version constant for Ventura