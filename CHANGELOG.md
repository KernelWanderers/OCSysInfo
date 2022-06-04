<div align="center">

# OCSysInfo Changelog

</div>

## v1.0.7 (ALPHA)

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