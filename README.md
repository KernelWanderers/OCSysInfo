
<div align="center">
<img src="./resources/icons/OCSI_logo_readme.png" width="300"/>

# OCSysInfo

</div>


A basic, high-level and efficient CLI for discovering hardware information about the current system.

<a href="https://github.com/KernelWanderers/OCSysInfo/blob/main/LICENSE"><img src="https://img.shields.io/github/license/KernelWanderers/OCSysInfo?color=%232885D7&style=for-the-badge"></a>
<a href="https://github.com/KernelWanderers/OCSysInfo/releases/"><img src="https://img.shields.io/github/downloads/KernelWanderers/OCSysInfo/total?color=%231DE2D0&style=for-the-badge" /></a>
<img src="https://img.shields.io/github/workflow/status/KernelWanderers/OCSysInfo/Compile%20and%20publish%20binaries?style=for-the-badge" />

<br />



<details>
<summary>Example</summary>
<br>

```
─ CPU
  └── Intel(R) Core(TM) i5-8400 CPU @ 2.80GHz
      ├── Cores: 6
      ├── Threads: 6
      ├── SSE: SSE4.2
      ├── SSSE3: Supported
      └── Codename: Coffee Lake

─ Motherboard
  ├── Model: B365M DS3H
  └── Manufacturer: Gigabyte Technology Co., Ltd.

─ GPU
  ├── Intel(R) UHD Graphics 630
  │   ├── Device ID: 0x3E92
  │   ├── Vendor: 0x8086
  │   ├── PCI Path: PciRoot(0x0)/Pci(0x2,0x0)
  │   └── ACPI Path: \_SB.PCI0.GFX0
  └── AMD Radeon (TM) R9 390 Series
      ├── Device ID: 0x67B1
      ├── Vendor: 0x1002
      ├── PCI Path: PciRoot(0x0)/Pci(0x1,0x0)/Pci(0x0,0x0)
      ├── ACPI Path: \_SB.PCI0.PEG0.PEGP
      └── Codename: Hawaii

─ Memory
  ├── F4-2400C15-4GRR (Part-Number)
  │   ├── Type: DDR4
  │   ├── Slot
  │   │   ├── Bank: BANK 0
  │   │   └── Channel: ChannelA-DIMM0
  │   ├── Frequency (MHz): 2400 MHz
  │   ├── Manufacturer: 04CD
  │   └── Capacity: 4096MB
  ├── F4-2400C15-4GRR (Part-Number)
  │   ├── Type: DDR4
  │   ├── Slot
  │   │   ├── Bank: BANK 1
  │   │   └── Channel: ChannelA-DIMM1
  │   ├── Frequency (MHz): 2400 MHz
  │   ├── Manufacturer: 04CD
  │   └── Capacity: 4096MB
  ├── F4-2400C15-4GRR (Part-Number)
  │   ├── Type: DDR4
  │   ├── Slot
  │   │   ├── Bank: BANK 2
  │   │   └── Channel: ChannelB-DIMM0
  │   ├── Frequency (MHz): 2400 MHz
  │   ├── Manufacturer: 04CD
  │   └── Capacity: 4096MB
  └── F4-2400C15-4GRR (Part-Number)
      ├── Type: DDR4
      ├── Slot
      │   ├── Bank: BANK 3
      │   └── Channel: ChannelB-DIMM1
      ├── Frequency (MHz): 2400 MHz
      ├── Manufacturer: 04CD
      └── Capacity: 4096MB

─ Network
  └── RTL8111/8168/8411 PCI Express Gigabit Ethernet Controller
      ├── Device ID: 0x8168
      ├── Vendor: 0x10EC
      ├── PCI Path: PciRoot(0x0)/Pci(0x1c,0x4)/Pci(0x0,0x0)
      └── ACPI Path: \_SB.PCI0.RP05.PXSX

─ Audio
  ├── Unknown Sound Device
  │   ├── Device ID: 0x4938
  │   └── Vendor: 0x0BDA
  ├── RV635 HDMI Audio [Radeon HD 3650/3730/3750]
  │   ├── Device ID: 0xAA01
  │   └── Vendor: 0x1002
  ├── Intel(R) Display Audio
  │   ├── Device ID: 0x280B
  │   └── Vendor: 0x8086
  └── Realtek ALC887
      ├── Device ID: 0x0887
      └── Vendor: 0x10EC

─ Input
  └── HID Keyboard Device

─ Storage
  ├── WDC WD2500AAJS-00L7A0
  │   ├── Type: Unspecified
  │   ├── Connector: Serial ATA (SATA)
  │   └── Location: Internal
  ├── Kingston DataTraveler 2.0
  │   ├── Type: Unspecified
  │   ├── Connector: USB
  │   └── Location: External
  ├── KINGSTON SA400S37240G
  │   ├── Type: Solid State Drive (SSD)
  │   ├── Connector: Serial ATA (SATA)
  │   └── Location: Internal
  └── LITEON CV3-8D128-HP
      ├── Type: Solid State Drive (SSD)
      ├── Connector: Serial ATA (SATA)
      └── Location: Internal
```
</details>

<br />

## Installation

Firstly, we do not support `Python 2` – the only support provided is for `Python 3.8` and greater. <br />
So please ensure you have `Python 3.8` or greater installed.

In order to install `OCSysInfo`, you can either download the repository manually via GitHub, or via Git.
<br />
Then, run the `main.py` script located in the project's root. (Do also make sure to install the dependencies as shown below.)

```sh
# Clone the repository using Git
git clone https://github.com/KernelWanderers/OCSysInfo.git

# Switch to the repository folder
cd OCSysInfo

# Install dependencies
python3 -m pip install -r requirements.txt
```

```sh
# Run the script
python3 main.py
```

## Implementations

OCSysInfo takes advantage of each platform's native interaction protocol, except for Linux, which uses a pseudo file system & its distros expose no consistent way of obtaining this information via command/API, in order to extract information about the system's hardware manually.

### Windows

- `WMI`

  - Windows's WMI (`Windows Management Instrumentation`) is a protocol allowing us to obtain the current system's data—which is practically anything that we could ever ask for. (Some PCI devices even construct the `PCIROOT` path where available! Though, generally this data isn't reliable). Data that we look for are as follows (per class):

    - `Win32_Processor` — information about the current system's CPU in use. Though, we only seek out the following properties:
      - `Manufacturer`
      - `Name`
      - `NumberOfCores`
      - `NumberOfLogicalProcessors`
    <br />

    - `Win32_VideoController` — information about the current system's **GPU devices** in use. The only properties we seek out are `Name` (the GPU's friendly name) and `PNPDeviceID`, which is basically its PCI path; it includes the device id and vendor id, which we extract.

    - `Win32_NetworkAdapter` — information about [...] system's **Network controllers** available. We only want the `PNPDeviceID` property, from which we can extract the device/vendor id, which we use to query `devicehunt.com` and `pci-ids.ucw.cz` if nothing was found in `devicehunt.com`; the application does _not_ push the device if it cannot be found on either site.

    - `Win32_SoundDevice` — information about [...] system's **audio I/O controllers** available. As with the network adapter, we only care about `PNPDeviceID`.

    - `Win32_BaseBoard` — information about [...] system's **motherboard**, we only care about the `Product` (motherboard model) and `Manufacturer` (vendor name) properties.

    - `Win32_Keyboard` — information about [...] system's **keyboard(s)**, their connection types, and possibly their display names. We only look for the `Description` (type of connector + display name), and the `DeviceID` property.

    - `Win32_PointingDevice` — same as the one item before, but instead for **mice**/**trackpads**/**touchpads**/etc.

### macOS

- `sysctl`

  - macOS's `sysctl` command exposes a way for us to obtain information about the CPU with ease. The key features of this, which we need, are:

    - CPU model
    - CPU instruction flags
    - Core count
    - Thread count
    - Maximum supported SSE version
    - SSSE3 support

- `IOKit`

  - Apple's `IOKit` framework allows us to interact with the system's devices (we only seek out `IOPCIDevice` and `IOHDACodecDevice`, as more information would be overtly useless to us.)

  - We filter by using `IOPCIClassMatch`, which can serve as a bit mask match, where the goal is to match the type of device exposed through `class-code` (i.e. display controllers will generally have a bit that's equal to `0x03`, multimedia controllers have a bit that's equal to `0x04`, etc.)

  - With `IOPCIDevice`, we're looking for PCI devices which have a specific bit mask, and we obtain the model (if exposed), device ID and vendor ID through there.

  - With `IOHDACodecDevice`, we simply seek out built-in audio controllers that have an HDA codec present. If nothing, that suffices our criteria, is returned, we simply look into `0x04` (bit for PCI multimedia controllers.)

  - With `IODeviceTree`, we're looking for Memory (RAM) modules, which is surprisingly easily obtainable. More-so, we extract the data in the following manner:
    - Instantiate a list which will hold an `N` amount of dictionaries.
    - Afterwards, loop over each property of the data returned, and convert the values into types we can handle internally (i.e. bytes -> str), and look for the following:
      - `dimm-part-number` — holds a list of each module's part number (yes, each part number is enumerated uniquely for each memory module)

      - `dimm-types` — holds a list of each module's DIMM type (DDR3, DDR4, etc.)

      - `slot-names` — holds a list of each module's `BANK` and `Channel` location, as well as the index of that specific channel.

      - `dimm-speeds` — holds a list of each module's current frequency (as far as we can tell, there's no way of determining the base clock frequency.)

      - `reg` — holds a byte sequence, from which we determine the capacity of each memory module.
        - Example: ``01 00 00 00 00 00 00 00 01 00 00 00 00 00 00 00 01 00 00 00 00 00 00 00 01 00 00 00 00 00 00 00`` -> `[1, 1, 1, 1]`

        - We then multiply each value from the list with `0x010000` (`65536` in decimal), and divide the result by `0x10` (`16` in decimal) to calculate the capacity. Here, in our aforementioned example, `1 * 0x010000 / 0x10` would be equal to `4096` (`0x1000` in hexadecimal), which is, of course 4096MB.

### Linux

- `sysfs`

  - Devices enumerated as `drm` (`/sys/class/drm`) devices are taken into account with the identity of a GPU; which are looked at if `cardX` directories are found. The directories of these enumerations will generally contain a `cardX/device/device` and `cardX/device/vendor` file.

  - Devices enumerated inside of `/sys/class/net` are classified only if they contain a `*/device/device` and `*/device/vendor` file (so that we can at least have a strong assumption that it'd be a valid network controller.)

  - Devices enumerated inside of `/sys/class/sound` are looked at for the audio controllers — generally, they'll have a relatively similar enumerations as `drm` devices — as a `cardX` format.

- `proc`

  - We are able to take advantage of what is enumerated and the type of data available in Linux's `procfs` pseudo filesystem. For example, we may look into `/proc/bus/input/devices` to list all the names and paths of each input device, and of course, its location in `sysfs` — which is of use for us.

  - We may also find `/proc/cpuinfo`, which holds data about the current system's CPU. Though, generally, thread count isn't explicitly stated as is, but rather, each thread has its own set of data enumerated in `cpuinfo`'s dump, so we may simply get the thread count by doing: `<cpuinfo>.count('processor')`

## Issues

When opening up issues, please list all hardware information relevant, and the issue you're encountering. Show real outputs, and the expected output, etc.

## Credits

The following contains credits to all the people who helped assist in the making, testing, and polishing of this project. This project would be nothing without them.

- @[Joshj23](https://github.com/Joshj23icy) — for extensive help in researching how to discover hardware information on Linux platforms, and providing a big portion of machines used for unit testing.

- @[Flagers](https://github.com/flagersgit) — for general guidance, documentation reference, implementation ideas, general support, documentation, help in fixing the source code's faulty logic, and much, much more.

- @[Acidanthera](https://github.com/Acidanthera) — for the OpenCore bootloader (its community is what drew inspiration for this project.)

- @[Rusty-bits](https://github.com/rusty-bits) — for inspiring the idea of parsing the PCI IDs from the pci.ids list and layout for implementing a search functionality. _Though sadly, this idea never reached production._

- @[Rvstry](https://github.com/rvstry) — for extensive help in research regarding identifying various devices on Linux platforms, & testing the application in its various stages.

- @[Dids](https://github.com/Dids) — for providing the URL to the raw content of the PCI IDs list repository. _Though sadly, this was never used, as we turned more towards scraping [the site](https://pci-ids.ucw.cz)_

- @[DhinakG](https://github.com/DhinakG) — for implementing the `ioreg` abstraction for [`OCLP`](https://github.com/dortania/OpenCore-Legacy-Patcher), and allowing us to copy it over for our own purposes.

- @[CorpNewt](https://github.com/CorpNewt) — for implementing the logic of scraping the [`pci-ids`](https://pci-ids.ucw.cz) repository site, and allowing us to use their CLI format.

- @[Midi1996](https://github.com/midi1996) — for extensive amounts of assistance in regards to testing the application on different hardware, in the application's various stages.

- @[ScoobyChan](https://github.com/ScoobyChan) — for guidance and helping with the implementation of Linux's flags detection.

- @[Quist](https://github.com/nadiaholmquist) — for extensive amounts of unit testing on various hardware, they helped immensely with fool-proofing OCSysInfo as best as possible, alongside [Joshj23](https://github.com/Joshj23icy)'s immense help with unit testing.

- @[1Revenger1](https://github.com/1Revenger1) — for implementing input device detection for Linux platforms, as well as immense assistance for identifying input devices properly on Windows & unit testing.

- @[Yuichiro](https://github.com/YuiiiPTChan) — for assistance in testing the application in its various stages.

- @[Emiyl](https://github.com/emiyl) — for providing extensive assistance with testing the application, and debugging it.

- @[ThatsNiceGuy](https://github.com/ThatsNiceGuy) — for extensive amounts of help in regards to testing the application, and debugging it.

- @[flababah](https://github.com/flababah/) — for https://github.com/flababah/cpuid.py

- @[Nemo Xiong](https://github.com/xiongnemo) — for their implementation of [scraping Intel's ARK page](https://github.com/xiongnemo/arksearch)

- @[renegadevi](https://gitlab.com/renegadevi) — for extensive amounts of help with fixing the source code's faulty logic.

- @[mendelsshop](https://github.com/mendelsshop) — for assistance in testing the application in its various stages, and continuous feedback on new updates/features.

- @[khronokernel](https://github.com/khronokernel) — for extensive amounts of help with fixing the source code's faulty logic, as well as providing extensive amounts of assistance in regards to unit-testing & debugging.

- @[Fewtarius](https://github.com/fewtarius) — for assistance in testing the application in its various stages.

- @[Apethesis](https://github.com/Apethesis) — for assistance in testing the application in its various stages.

- @[ThatCopy](https://github.com/ThatCopy) — for assistance in locating and fixing bugs and issues with the terminal on OSX, as well as completely defining and taking care of the logic for detecting ARM (ARM64 and ARMv7) CPUs on Linux.