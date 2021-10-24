# What's this?

This, fellow user, is the bare minimum necessary in order for OCSysInfo to make a _relatively close_ assumption on the codename of the current CPU (Intel & AMD only for now.)

The JSON files you see here were both manually written according to the following:

- [Intel CPUID wiki](https://en.wikichip.org/wiki/intel/cpuid)
- [AMD CPUID wiki](https://en.wikichip.org/wiki/amd/cpuid)

It is not pin-point precise, but it tries to make sense of it using the iGPU model, in order to match with the possible match of teh CPU codename, and/or the stepping value.

```
Kaby Lake
    ├─ [DT, H, S, X ] <-- CPU “core” variants
    │   ├─ Extended Family: 0x0
    │   ├─ Base Family: 0x6
    │   ├─ Extended Model: 0x9
    │   └─ Base Model: 0xE
    │
    └─ [Y, U]
        ├─ Extended Family: 0x0
        ├─ Base Family: 0x6
        ├─ Extended Model: 0x8
        └─ Base Model: 0xE

Coffee Lake
    ├─ [S, H, E]
    │   ├─ Extended Family: 0x0
    │   ├─ Base Family: 0x6
    │   ├─ Extended Model: 0x9
    │   └─ Base Model: 0xE
    │
    └─ [U]
        ├─ Extended Family: 0x0
        ├─ Base Family: 0x6
        ├─ Extended Model: 0x8
        └─ Base Model: 0xE

Comet Lake
    ├─ [S, H]
    │   ├─ Extended Family: 0x0
    │   ├─ Base Family: 0x6
    │   ├─ Extended Model: 0x9
    │   └─ Base Model: 0xE
    │
    └─ [U]
        ├─ Extended Family: 0x0
        ├─ Base Family: 0x6
        ├─ Extended Model: 0x8
        └─ Base Model: 0xE
```

This is where the issue arises. Some CPU generations/microarchitectures simply aren't distinguished uniquely enough for us to strongly “assume” the codename/microarchitecture for the system's CPU.

<br />

To “resolve” this issue, we've introduced two methods of verifying:

- Matching against the iGPU model, which is attached to its µarch.
- Using the `stepping` value to more specifically distinguish codenames from one another.
  
  - This isn't as accurate as we'd like it to be. For example, we can have a case where `Whiskey Lake` CPUs may have a stepping of `0xC`, which is the general stepping value for `Comet Lake` CPUs.

  - Another example of this would be the `i3-9100F` model from intel, where its stepping is identified as `0xB`, and not `0xA`, as it usually should be for `Coffee Lake` CPUs. Even though, on their website, it's identified as a CFL gen.

Because Intel has absolutely borked their own CPUID information, we are left to deal with some edge-cases, like the one previously mentioned.
