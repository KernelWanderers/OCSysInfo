# OCSysInfo

A basic, high-level and efficient CLI for discovering hardware information about the current system.

Basic example of this:

[<img src="https://i.imgur.com/taFKTV0.png" width="600"/>](https://i.imgur.com/taFKTV0.png=0)

## Implementations

OCSysInfo takes advantage of each platform's native interaction protocol, except for Linux, which uses a pseudo file system & its distros expose no consistent way of obtaining this information via command/API, in order to extract information about the system's hardware manually.

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

### Linux

- `sysfs`

  - Devices enumerated as `drm` (`/sys/class/drm`) devices are taken into account with the identity of a GPU; which are looked at if `cardX` directories are found. The directories of these enumerations will generally contain a `cardX/device/device` and `cardX/device/vendor` file.

  - Devices enumerated inside of `/sys/class/net` are classified only if they contain a `*/device/device` and `*/device/vendor` file (so that we can at least have a strong assumption that it'd be a valid network controller.)

  - Devices enumerated inside of `/sys/class/sound` are looked at for the audio controllers — generally, they'll have a relatively similar enumerations as `drm` devices — as a `cardX` format.

- `proc`
  - General CPU information is extracted via `/proc/cpuinfo`
    - Generally, just running the `cat` command on this file won't expose some vital information such as thread count. <br />
      The way we obtain threads from it is by doing some black magic: `grep -c processor /proc/cpuinfo`

## Issues

When opening up issues, please list all hardware information relevant, and the issue you're encountering. Show real outputs, and the expected output, etc.

## Credits

<<<<<<< HEAD
- @[Joshj23](https://github.com/Joshj23icy) — for extensive help in researching how to discover hardware information on Linux platforms, and providing a big portion of machines used for unit testing.
=======
- @[ObscureNightingale](https://github.com/ObscureNightingale) for writing basically the whole thing.

- @[Joshj23](https://github.com/Joshj23icy) – for extensive help in researching how to discover hardware information on Linux platforms.
>>>>>>> d159c3e9801b7d01057a04c9802f0c3ea4da6f76

- @[Flagers](https://github.com/flagersgit) — for general guidance, documentation reference, implemnetion ideas, general support, documentation, and much, much more.

- @[Acidanthera](https://github.com/Acidanthera) — for the OpenCore bootloader (its community is what drew inspiration for this project.)

- @[Rusty-bits](https://github.com/rusty-bits) — for inspiring the idea of parsing the PCI IDs from the pci.ids list and layout for implementing a search functionality. _Though sadly, this idea never reached production._

- @[Rvstry](https://github.com/rvstry) — for extensive help in research regarding identifying various devices on Linux platforms.

- @[Dids](https://github.com/Dids) — for providing the URL to the raw content of the PCI IDs list repository. _Though sadly, this was never used, as we turned more towards scraping [the site](https://pci-ids.ucw.cz)_

- @[DhinakG](https://github.com/DhinakG) — for implementing the `ioreg` abstraction for [`OCLP`](https://github.com/dortania/OpenCore-Legacy-Patcher), and allowing us to copy it over for our own purposes.

- @[CorpNewt](https://github.com/CorpNewt) — for implementing the logic of scraping the [`pci-ids`](https://pci-ids.ucw.cz) repository site.

- @[ScoobyChan](https://github.com/ScoobyChan) — for guidance and helping with the implementation of Linux's flags detection.

- @[Quist](https://github.com/nadiaholmquist) - for extensive amounts of unit testing on various hardware, they helped immensely with fool-proofing OCSysInfo as best as possible, alongside [Joshj23](https://github.com/Joshj23icy)'s immense help with unit testing.
