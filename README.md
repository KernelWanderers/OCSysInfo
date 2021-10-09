# OCSysInfo

A basic, high-level and efficient CLI for discovering hardware information about the current system.
Sample of this:

[__TODO__]


# Issues

When opening up issues, please list all hardware information relevant, and the issue you're encountering. Show real outputs, and the expected output, etc.


# Credits

- @[Joshj23](https://github.com/Joshj23icy) – for extensive help in researching how to discover hardware information on Shit-nux platforms.

- @[Flagers](https://github.com/flagersgit) – for general guidance and ideas regarding on how to handle specific cases properly, how to dump system information across platforms, and much more.

- @[Acidanthera](https://github.com/Acidanthera) – for the OpenCore bootloader (its community is what drew inspiration for this project.)

- @[Rusty-bits](https://github.com/rusty-bits) – for inspiring the idea of parsing the PCI IDs from the pci.ids list and layout for implementing a search functionality. _Though sadly, this idea never reached production._

- @[Rvstry](https://github.com/rvstry) – for extensive help in research regarding identifying various devices on Linux platforms (screw Linux.)

- @[Dids](https://github.com/Dids) – for providing the URL to the raw content of the PCI IDs list repository. _Though sadly, this was never used, as we turned more towards scraping [`devicehunt.com`](https://devicehunt.com)_

- @[DhinakG](https://github.com/DhinakG) – for implementing the `ioreg` abstraction for [`OCLP`](https://github.com/dortania/OpenCore-Legacy-Patcher), and allowing us to copy it over for our own purposes.