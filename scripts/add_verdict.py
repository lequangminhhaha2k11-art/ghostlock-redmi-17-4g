import json
import datetime

path = 'data/vulns.json'
data = json.load(open(path))

krel = "6.6.118-android15-8-ge56cf6b09cca-ab15511674-4k"

# CVE-2026-43499 record: nếu chưa có, tạo khung tối tiểu để gate hoạt động
if 'CVE-2026-43499' not in data.get('cves', {}):
    data.setdefault('cves', {})['CVE-2026-43499'] = {
        'fix': {},
        'kernels': {}
    }

entry = data['cves']['CVE-2026-43499'].setdefault('kernels', {})
entry[krel] = {
    'verdict': 'vulnerable',
    'checked': datetime.date.today().isoformat(),
    'method': 'hardware',
    'note': 'remove_waiter UAF live-verified: CVE-2026-43499 exploit achieved uid=0 '
            'repeatedly on this device 2026-09-22 (pselect race + cred swap + KASLR '
            'leak all working, logs archived). Kernel image from device OTA '
            'OS3.0.310.0.WDTMIXM, sha256 81181e8321e655acbce601faff94ab1610f9b825869a56a1c0e5bfcf9db1126c'
}

with open(path, 'w') as f:
    json.dump(data, f, indent=2)
    f.write('\n')

print('verdict recorded:', entry[krel]['verdict'], 'for', krel)