<div align="center">

<img src="../../../resources/icons/OCSI_logo_linux.png" width="500">

# Linux

</div>

This platform has probably caused the most inconvenience amongst us compared to any other. <br />

With Windows and macOS, it was practically a breeze. However, on Linux, we were left with doing a lot of data extraction manually, and it was not a treat.

I believe the worst part about it was figuring out how to construct a PCI path properly. <br />

Before we further progress with the explanation, we must thank @[Dids](https://github.com/Dids) and @[Flagers](https://github.com/flagersgit) for helping immensely with this logic. If it weren't for them, we probably might've ditched this altogether.

Take a look at the example below:

<br />

<details>

<br />

<summary>The logic behind our extraction, for parent slots with a child slot</summary>

<br />

```
Determine whether or not the full PCI path needs 1 or 2 components.

\_SB.PCI0.RP05.PXSX
        ^^^^^^^^ In our case, it's 2: since there's 2 arguments after PCI0

0000:00:1c.4
        | ||_ _ _  '4'  (function) is the second argument of the first PCI part of the path
        | |                 ^^^^^^^^^^PciRoot(0x0)/Pci(__,0x4)/Pci(__,__)
        | |
        |_|_ _ _ _ '1c' (device UID) is the first argument of the first PCI part of the path
                            ^^^^^^^^^^PciRoot(0x0)/Pci(0x1c,__)/Pci(__,__)


0000:07:00.0
        | || _ _ _  '0'  (function) is the second argument of the second PCI part of the path
        | |                 ^^^^^^^^^^PciRoot(0x0)/Pci(__,__)/Pci(__,0x0)
        | |
        |_| _ _ _ _ '00' (device UID) is the first argument of the second PCI part of the path
                            ^^^^^^^^^^PciRoot(0x0)/Pci(__,__)/Pci(0x0,__)

Yielding — PciRoot(0x0)/Pci(0x1c,0x4)/Pci(0x0,0x0)
```

</details>

<br />

Now take a look at another example below:

<br />

<details>

<br />

<summary>Example where we can't find a child slot</code>?</summary>

```
Determine whether or not the full PCI path needs 1 or 2 components.

\_SB.PCI0.GFX0
        ^^^^^^^^ In our case, it's 1: since there's a single argument after PCI0

// 
// In this case, we didn't find a child slot,
// so it already tells us it'll only consist of a single component.
//

0000:00:02.0
        | ||_ _ _  '0'  (function) is the second argument of the first PCI part of the path
        | |                  ^^^^^^^^^^PciRoot(0x0)/Pci(__,0x0)
        | |
        |_| _ _ _  '02' (device UID) is the first argument of the first PCI part of the path
                            ^^^^^^^^^^PciRoot(0x0)/Pci(0x2,__)

Yielding — PciRoot(0x0)/Pci(0x2,0x0)
```

</details>

<br />

Basically, What we're doing is, from the `*/device` path of the current device we're looking at, we read the `uevent` file, which, if contains `PCI_SLOT_NAME`, enables us to traverse through `/sys/bus/pci/devices`, and we look for any directories which may have that value inside of them, and then we grab the first entry's "value" and use the device & function as the first component of the PCI path, so let's say we have a network controller, and its slot name is `0000:07:00.0`, we look through `/sys/bus/pci/devices` trying to find any directory which may have it. Then we find these two directories:
```
-> 0000:00:1c.4:pcie002
-> 0000:00:1c.4:pcie010
```

We simply use the first one, and look at its device & function values, which we convert into proper hex values, which yields:
```
device = 0x1c
function = 0x4
```

We also convert the parent value (`0000:07:00.0`), which yields `0x0,0x0`; then we look at the ACPI path, and split on `.`; in this case, the ACPI path is `\_SB.PCI0.RP05.PXSX`, the list will have 4 elements, which means the amount of PCI path components (`Pci(...)`) that should make up this path are 2, so we basically set `PciRoot(0x0)`, and then use the first obtained child value (`0x1c`,`0x4`) and convert it into `Pci(0x1c,0x4)`—we also add the parent's value, since the ACPI path seems to point to it having 2 PCI path components, so to say. Which means, the parent value will be `Pci(0x0,0x0)` -- finally yielding `PciRoot(0x0)/Pci(0x1c,0x4)/Pci(0x0,0x0)`