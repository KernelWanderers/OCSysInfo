# Linux

This platform has probably caused the most inconvenience amongst us compared to any other. <br />

With Windows and macOS, it was practically a breeze. However, on Linux, we were left with doing a lot of data extraction manually, and it was not a treat. 

I believe the worst part about it was figuring out how to construct a PCI path properly. <br />

Before we further progress with the explanation, we must thank @[Dids](https://github.com/Dids) for helping immensely with this logic. If it weren't for them, we probably might've ditched this altogether.

Take a look at the example below:

<br />

<details>

<br />

<summary>The logic behind our extraction</summary>

<br />

```
Determine whether or not there should be 1 or 2 pci parts of the full path:

\_SB_.PCI0.RP05.PXSX
    ^^^^^In this case, it's 2: since after PCI0, there's 2 arguments

0000:00:1c.4
     | || |
     | ||_|_ _ _ _ '1c' is the first argument of the first PCI part of the path?
     | |                 ^^^^^^^^^^PciRoot(0x0)/Pci(0x1c,__)/Pci(__,__)
     | |
     |_|_ _ _ _ _  '00' is the first argument of the second PCI part of the path
                         ^^^^^^^^^^PciRoot(0x0)/Pci(__,__)/Pci(0x0,__)

0000:07:00.0
     | || |
     | ||_| _ _ _  '00' is the second argument of the second PCI part of the path
     | |                 ^^^^^^^^^^PciRoot(0x0)/Pci(__,__)/Pci(__,0x0)
     | |
     |_|_ _ _ _ _  '07' is the second argument of the first PCI part of the path
                         ^^^^^^^^^^PciRoot(0x0)/Pci(__,0x7)/Pci(__,__)

Yielding — PciRoot(0x0)/Pci(0x1c,0x7)/Pci(0x0,0x0)
```
</details>

<br />

Now take a look at another example below:

<br />

<details>

<br />

<summary>What happens when we only have a single argument after <code>PCI0</code>?</summary>

```
Determine whether or not there should be 1 or 2 pci parts of the full path:

\_SB_.PCI0.GFX0
    ^^^^^In this case, it's 1: since after PCI0, there's only a single argument

< BLANK >
     | || |
     | ||_|_ _ _ _ There's nothing here.
     | |
     | |
     |_|_ _ _ _ _  There's nothing here.


0000:00:02.0
     | || |
     | ||_| _ _ _  '02' is the first argument of the first PCI part of the path
     | |                 ^^^^^^^^^^PciRoot(0x0)/Pci(0x2,__)
     | |
     |_|_ _ _ _ _  '00' is the second argument of the first PCI part of the path
                         ^^^^^^^^^^PciRoot(0x0)/Pci(__,0x0)

Yielding — PciRoot(0x0)/Pci(0x2,0x0)
```

Bit of a doosey one, eh?

</details>

