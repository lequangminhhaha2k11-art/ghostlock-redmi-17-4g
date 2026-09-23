# KernelSU Root — Xiaomi Redmi 17 4G (leedsa)

Temporary root for the **Xiaomi Redmi 17 4G** with a **locked bootloader**, achieved by
adapting the CVE-2026-43499 (GhostLock) kernel exploit to this device's MediaTek
MT6768 (Helio G85) SoC and porting the [pixel-ksu-root](https://github.com/JingMatrix/pixel-ksu-root)
runner framework to work with Xiaomi's GKI kernel build.

No bootloader unlock. No flashing. No partition writes. A reboot is the uninstall.

---

## Supported Device

| Spec | Value |
|------|-------|
| Model | Redmi 17 4G (2606FRN72Y) |
| Codename | `leedsa` / `leedsa_n_global` |
| SoC | MediaTek MT6768 (Helio G85) |
| Kernel | `6.6.118-android15-8-ge56cf6b09cca-ab15511674-4k` |
| KMI | `android15-6.6` |
| Build | `OS3.0.310.0.WDTMIXM` (HyperOS 3.0, Android 16) |
| Bootloader | **Locked** (required — do not unlock) |

## How It Works

The CVE-2026-43499 vulnerability is a use-after-free in the Linux kernel's
futex PI subsystem (`remove_waiter()` leaves a dangling `rt_mutex_waiter`
that `pselect(2)` re-occupies on the stack). The exploitation chain:
