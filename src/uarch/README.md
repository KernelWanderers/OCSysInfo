# What's this?

This, fellow user, is the bare minimum necessary in order for OCSysInfo to make a _relatively close_ assumption on the codename of the current CPU (Intel & AMD only for now.)

The JSON files you see here were both manually written according to the following:
- [Intel CPUID wiki](https://en.wikichip.org/wiki/intel/cpuid)
- [AMD CPUID wiki](https://en.wikichip.org/wiki/amd/cpuid)

It is not precise, lacks some codenames, and most certainly not explicitly distinguishable from other codenames. <br />
As can be seen with the following example for Intel's codenames:
```
Kaby Lake
    ├─ [DT, H, S, X ] <-- Microarchitecture revisions.
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

To “resolve” this issue, we've simplified how we identify different microarchitectures. AKA, we ditch some values. Which generally does work.

Lines [386-399](https://github.com/iabtw/OCSysInfo/blob/main/src/uarch/intel.json#L386-L399) in `intel.json`:
```json
    {
        "Codename": "Kaby Lake",
        "ExtFamily": "0X0",
        "BaseFamily": "0X6",
        "ExtModels": ["0X8"],
        "BaseModels": ["0XE"]
    },

    {
        "Codename": "Coffee Lake",
        "ExtFamily": "0X0",
        "BaseFamily": "0X6",
        "ExtModels": ["0X9"],
        "BaseModels": ["0XE"]
    },
```

We have completely ditched distinguishing these 3 microarchitectures from one another, and as you can see, completely removed `Comet Lake` too. Which will, of course, be rewritten to attempt to resolve this issue. 

`Kaby Lake` is defined by:
- Extended Model `0x8`
- Base Model `0xE`

`Coffee Lake` is defined by:
- Extended Model: `0x9`
- Base Model `0xE`

`Comet Lake` is `N/A` for the time being.

_I suppose this means goodbye Comet Lake for now..._