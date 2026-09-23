import sys
sys.argv = ['generate_target.py',
            '--boot', 'boot_uncompressed.img',
            '--profile', 'profile_leedsa.json',
            '-o', '/tmp/dummy_target.h']

# import module by path
import importlib.util
spec = importlib.util.spec_from_file_location('gt', 'generate_target.py')
gt = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gt)

# Reimplement main() flow up to kallsyms recovery, then dump
from pathlib import Path

boot = gt.extract_boot_kernel(Path('boot_uncompressed.img'))
info = gt.recover_kallsyms(boot.kernel, boot.kernel_size, boot.image_size)

with open('../pixel-ksu-root/leedsa_kallsyms.txt', 'w') as f:
    for index, typ, name, off in info.symbols:
        addr = info.relative_base + off
        f.write(f"{addr:#018x} {typ} {name}\n")

print(f"wrote {len(info.symbols)} symbols, rel_base={info.relative_base:#x}")