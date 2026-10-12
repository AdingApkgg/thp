"""Read pinned original32 D3DX triangle weights under D3D9 device FPU control."""
import hashlib
import json
import struct
import subprocess
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'artifacts/th14/physical-texture32-post-reset'
sha = lambda b: hashlib.sha256(b).hexdigest()
dll = Path('C:/Windows/SysWOW64/d3dx9_43.dll')
assert sha(dll.read_bytes()) == '0b28546be22c71834501f7d7185ede5d79742457331c7ee09efc14490dd64f5f'
native = json.loads((OUT/'64/native.json').read_text(encoding='utf-8'))
request = (OUT/'requests.bin').read_bytes()
assert sha(request) == native['requestInputSha256']
helper = OUT/'weights32.exe'
subprocess.run([str(helper), str(OUT/'requests.bin'), str(OUT/'weights32.bin')], check=True, creationflags=subprocess.CREATE_NO_WINDOW)
data = (OUT/'weights32.bin').read_bytes()
control, count = struct.unpack_from('<II', data); at = 8; tables = []
assert control & 0x30000 == 0
for _ in range(count):
    source, destination, size = struct.unpack_from('<III', data, at); at += 12
    raw = data[at:at+size]; at += size; pos = 4; weights = []
    assert struct.unpack_from('<I', raw)[0] == size
    for sample in range(source):
        length = struct.unpack_from('<I', raw, pos)[0]
        assert length >= 4 and (length-4)%8 == 0
        weights.append([list(struct.unpack_from('<II', raw, x)) for x in range(pos+4,pos+length,8)])
        pos += length
    assert pos == size
    tables.append(dict(source=source,destination=destination,weights=weights))
assert at == len(data)
report = dict(passed=True,completeGame=False,nativeEquivalent=False,control=control,precision=64,tables=tables,privateRoutineRva=0xdc63b,d3dxSha256=sha(dll.read_bytes()),d3d9Sha256=sha(Path('C:/Windows/SysWOW64/d3d9.dll').read_bytes()),requestInputSha256=sha(request),nativeTextureProofSha256=sha((OUT/'64/native.json').read_bytes()),binarySha256=sha(data),toolSha256=sha(Path(__file__).read_bytes()),helperSourceSha256=sha((ROOT/'tools/th14-triangle-weights32-post-reset-helper.cpp').read_bytes()),helperSha256=sha(helper.read_bytes()),scope='All distinct triangle axis dimensions used by actual57 TH14 resources. Pinned original32 D3DX9_43 private triangle table RVA dc63b, mirror border mode, exact destination indices and float bits; actual hidden HAL D3D9 device followed by actual x87 FNINIT64 precision (independent reset hypothesis). No whole-frame or natural clear claim.')
(OUT/'weights32-native.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
print('PASS original32 triangle tables',count,sum(len(t['weights']) for t in tables))
