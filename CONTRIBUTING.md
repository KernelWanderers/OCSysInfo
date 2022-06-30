> **Warning**
> If you do not have a great understanding of OOP concepts, 
> or aren't familiar with Python - please ground yourself in the aforementioned before contributing to this project.


Before you attempt to contribute, please ensure that you're familiar with the following:

**Universal prerequisites:**

* Basic knowledge of each OS's respective core commands (such as `dir`, `ls`, `mv`, etc.)
* Familiarity with OpenCore (not a necessary prerequisite. 
Definitely desirable however, so that new contributors are able to comply with their standards immediately.)
* Basic knowledge of hardware (and how each OS interacts with it.)

**macOS prerequisites**:

* User-space `I/O Kit`
* `Python<->Obj-C` bridge (`pyobjc`)
* Some basic kernel-space concepts and paradigms for the XNU kernel

**Windows prerequisites**:

* `WMI` API
* `CFGMGR32` API
* Basic knowledge of Powershell

**Linux prerequisites**:

* Please avoid this platform at any cost
* Knowledge on the Linux kernel's API standards
* Familiarity with various distros (and their own implementations for `sysfs`/`procfs`, because fuck standardisation.)

**Other platforms?**

We don't support any other platform than the ones listed above.
We also don't plan on supporting anything but the aforementioned until further notice. PRs for this are welcome, though!

**CPU arch support?**

We really don't have many machines to test ARM (or even RISC-V) support on; but, as far as we know, Apple's `ARM64` on macOS is supported
(Linux is yet to be tested), `ARMv7`/`*v8` Linux is supported. Windows remains untested for ARM.

The `x86_64` arch is really the only CPU with certain support across all three platforms.
We don't have many CPUs that are x86 only—anyone is free to send us over a dump if they can, though!
32-bit support is questionable, because we aren't certain if Python 3.9.x+ can run on 32-bit OSes.
