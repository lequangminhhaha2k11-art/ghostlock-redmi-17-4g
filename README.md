# KernelSU Root — Xiaomi Redmi 17 4G (leedsa)

Temporary root for the **Xiaomi Redmi 17 4G** with a **locked bootloader**, achieved by
adapting the CVE-2026-43499 (GhostLock) kernel exploit to this device's MediaTek
MT6768 (Helio G85) SoC and porting the
[pixel-ksu-root](https://github.com/JingMatrix/pixel-ksu-root) runner framework
to work with Xiaomi's GKI kernel build.

No bootloader unlock. No flashing. No partition writes. A reboot is the uninstall.

---

## Supported Device

| Spec | Value |
|------|-------|
| Model | Redmi 17 4G (2606FRN72Y) |
| Codename | leedsa / leedsa_n_global |
| SoC | MediaTek MT6768 (Helio G85) |
| Kernel | 6.6.118-android15-8-ge56cf6b09cca-ab15511674-4k |
| KMI | android15-6.6 |
| Build | OS3.0.310.0.WDTMIXM (HyperOS 3.0, Android 16) |
| Bootloader | Locked |

## How It Works

CVE-2026-43499 is a use-after-free in the Linux kernel's futex PI subsystem.
remove_waiter() leaves a dangling rt_mutex_waiter that pselect(2) re-occupies
on the stack. The exploitation chain:

1. KASLR leak — pselect stack overlap corrupts nfulnl_logger, read back via
   /proc/sys/kernel/random/boot_id
2. Arbitrary R/W — pipe-buffer page reclaim gives a physical read/write primitive
3. Credential swap — overwrite task->cred with init_cred gives uid=0
4. KernelSU late-load — finit_module() loads kernelsu.ko from the manager APK

After the module loads, the installed KernelSU manager app takes over
completely. Root survives until the next reboot.

## Prerequisites

- Windows with [MSYS2 UCRT64](https://www.msys2.org/) (NOT Git Bash — path
  conversion will break the runner)
- [Android NDK r30 or newer](https://developer.android.com/ndk/downloads)
- A full OTA ZIP matching your exact firmware build
- [pixel-ksu-root](https://github.com/JingMatrix/pixel-ksu-root) cloned
- KernelSU manager installed on the phone (any variant works)

## Quick Start

### 1. Set up the environment (UCRT64 shell)

    pacman -S --noconfirm make coreutils python

    export MSYS2_ARG_CONV_EXCL="*"
    export MSYS_NO_PATHCONV=1
    export SHELL=/bin/bash
    export PATH="/usr/bin:/ucrt64/bin:/c/Downloads/platform-tools:$PATH"

### 2. Copy this repo's files into pixel-ksu-root

    cp target/android15-6.6-ab15511674.h pixel-ksu-root/cves/targets/kernel/
    cp patches/targets-with-leedsa.json pixel-ksu-root/data/targets.json
    cp patches/vulns-with-leedsa.json pixel-ksu-root/data/vulns.json
    cp patches/install-msys-fix.sh pixel-ksu-root/runner/lib/install.sh

### 3. Fix the WORKDIR path issue

In the file pixel-ksu-root/pixel-ksu-root find the line:

    WORKDIR="$(mktemp -d)"

Replace with:

    WORKDIR="$(cygpath -m "$REPO")/.workdir"
    rm -rf "$WORKDIR"
    mkdir -p "$WORKDIR"

### 4. Build the payload

    cd pixel-ksu-root

    python3 tools/pixel-image/derive_offsets.py \
      --image leedsa_Image \
      --kallsyms target/leedsa-kallsyms.txt \
      --target leedsa-OS3.0.310.0.WDTMIXM \
      > cves/targets/kernel/android15-6.6-ab15511674.h

    make -C cves TARGET=leedsa-OS3.0.310.0.WDTMIXM RECIPE=ghostlock all \
      SHELL=/bin/bash \
      ANDROID_NDK_HOME=/c/Downloads/android-ndk-r30 \
      TARGET_CC="/c/Downloads/android-ndk-r30/toolchains/llvm/prebuilt/windows-x86_64/bin/aarch64-linux-android35-clang -include stddef.h"

    mkdir -p artifacts/exploits
    cp cves/build/leedsa-OS3.0.310.0.WDTMIXM/cve-2026-43499-ghostlock.so \
       artifacts/exploits/cve-2026-43499-ghostlock-android15-6.6-ab15511674.so
    cp cves/build/leedsa-OS3.0.310.0.WDTMIXM/cve-2026-43499-root \
       artifacts/cve-helper

Note: the derive step overwrites the kernel header — re-add the include
guards and runtime facts (MM_STRUCT_SZ, P0_PHYS_OFFSET, P0_KERNEL_PHYS_LOAD)
by appending them manually, or skip derive if you use the committed header
from this repo's target/ directory directly.

### 5. Root the device

    ./pixel-ksu-root --manager me.weishu.kernelsu

The runner will reboot the device for a clean shot, run the exploit (up to
4 attempts), late-load the KernelSU module, and verify. Expected output:

    KernelSU driver live: version=32601
    SUCCESS — KernelSU is loaded and answering (version=32601)

### 6. Grant root to apps

Open the KernelSU manager app on the phone, go to the Superuser tab, and
toggle root for any app you want.

## Physical Memory Map

    p0_phys_offset:        0x40000000    (DRAM base, MT6768)
    p0_kernel_phys_load:   0x40080000    (arm64 Image text_offset standard)
    KIMAGE_TEXT_BASE:      0xffffffc080000000  (VA_BITS=39)

## Known Issues

| Issue | Status | Notes |
|-------|--------|-------|
| Apps crash during exploit | Expected | The heap spray causes memory pressure on 4GB devices. Apps recover after reboot. |
| Su daemon dies after late-load | By design | The temp su is replaced by KernelSU's own su. |
| Exec format error on prebuilt .ko | Resolved | Kernel has CFI_CLANG — prebuilt modules are rejected. Build from source with matching config. |
| Reboot loses root | By design | LKM mode is temporary. Re-run after each reboot. |

## Credits

- [JingMatrix/pixel-ksu-root](https://github.com/JingMatrix/pixel-ksu-root) — the runner framework, exploit architecture, and build system
- [Linuxoid-cn/CVE-2026-43499-Poc-Analysis](https://github.com/Linuxoid-cn/CVE-2026-43499-Poc-Analysis) — the original exploit source and target generator
- NebuSec (Kernix) — CVE-2026-43499 research and disclosure
- [tiann/KernelSU](https://github.com/tiann/KernelSU) and [rsuntk/ReSukiSU](https://github.com/rsuntk/KernelSU) — the kernel modules and manager apps
- KernelSnitch (TU Graz, NDSS 2025) — the heap pointer side channel technique

## Disclaimer

This project is for educational and research purposes only. Use it only on
devices you own or have explicit authorization to test. The authors are not
responsible for any damage, data loss, or legal consequences arising from
the use of this software.

## License

MIT — same as pixel-ksu-root.
