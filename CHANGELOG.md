<div align="center">

# OCSysInfo Changelog

</div>

## v1.0.7 (BETA)

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