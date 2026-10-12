"""Run original 32-bit D3DX API on original TH14 captured texture requests."""
import hashlib
import importlib
import json
import struct
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'artifacts/th14/physical-texture32-pixels'
sha = lambda b: hashlib.sha256(b).hexdigest()


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    proof_bytes = (ROOT / 'artifacts/th14/anm-physical-resource-loader/native.json').read_bytes()
    proof = json.loads(proof_bytes)
    archive = json.loads((ROOT / 'artifacts/archive-differential/th14.json').read_text(encoding='utf-8'))
    parser = importlib.import_module('th-anm-script-dump')
    rows = [r for r in proof['rows'] if r['rate'] == 1]
    assert len(rows) == 57
    cases = []
    request = bytearray(b'TH14TEX\0' + struct.pack('<I', 437))
    for row in rows:
        raw = (Path(archive['extraction']) / row['name']).read_bytes()
        assert sha(raw) == row['sha256']
        chunks = list(parser.chunks(raw))
        assert len(chunks) == row['chunks'] == len(row['uploads'])
        for record, (_, chunk) in zip(row['uploads'], chunks):
            if record['kind'] == 'renderTarget':
                continue
            embedded = record['kind'] == 'embedded'
            pixels = b''
            if embedded:
                tex_offset = struct.unpack_from('<I', chunk, 28)[0]
                pixels = chunk[tex_offset + 16:tex_offset + 16 + record['sourceBytes']]
                assert len(pixels) == record['sourceBytes'] and sha(pixels) == record['sourceSha256']
            args = record['creationArguments'] + [int(embedded), record.get('sourceFormat', 0), record.get('pitch', 0), record.get('filter', 0)] + record.get('sourceRect', [0]*4) + record.get('destinationRect', [0]*4) + [len(pixels)]
            assert len(args) == 19
            request.extend(struct.pack('<19I', *args)); request.extend(pixels)
            cases.append(dict(name=row['name'], chunk=record['chunk'], kind=record['kind'], requestedFormat=args[4]))
    assert len(cases) == 437
    request_path = OUT / 'requests.bin'; request_path.write_bytes(request)
    helper = ROOT / 'artifacts/th14/physical-texture-pixels/texture32.exe'
    for precision in (53, 64):
        destination = OUT / str(precision); destination.mkdir(exist_ok=True)
        output_path = destination / 'readback.bin'
        subprocess.run([str(helper), str(request_path), str(output_path), str(precision)], check=True, creationflags=subprocess.CREATE_NO_WINDOW)
        data = output_path.read_bytes(); control, post_device_control, count = struct.unpack_from('<3I', data)
        assert post_device_control & 0x30000 == 0x20000, hex(post_device_control)
        assert count == len(cases)
        cursor = 12; offset = 0; stream = hashlib.sha256(); results = []
        with (destination / 'textures.bin').open('wb') as binary:
            for case in cases:
                fmt, width, height, pitch, size = struct.unpack_from('<5I', data, cursor); cursor += 20
                pixels = data[cursor:cursor+size]; cursor += size
                assert len(pixels) == size == pitch*height
                results.append(dict(case, format=fmt, width=width, height=height, pitch=pitch, offset=offset, bytes=size, sha256=sha(pixels)))
                binary.write(pixels); stream.update(pixels); offset += size
        assert cursor == len(data)
        report = dict(passed=True, completeGame=False, nativeEquivalent=False, cases=results, bytes=offset, binarySha256=stream.hexdigest(), precision=precision, requestedPreDevicePrecision=precision, control=control, postDeviceControl=post_device_control, postDevicePrecision=24, requestInputSha256=sha(request), requestProofSha256=sha(proof_bytes), toolSha256=sha(Path(__file__).read_bytes()), helperSourceSha256=sha((ROOT/'tools/th14-physical-texture32-helper.cpp').read_bytes()), helperSha256=sha(helper.read_bytes()), parserSha256=sha((ROOT/'tools/th-anm-script-dump.py').read_bytes()), d3d9Sha256=sha(Path('C:/Windows/SysWOW64/d3d9.dll').read_bytes()), d3dxSha256=sha(Path('C:/Windows/SysWOW64/d3dx9_43.dll').read_bytes()), scope='Actual original32 D3DX9_43 CreateTexture/LoadSurfaceFromMemory on hidden D3D9 HAL managed textures, original TH14 captured requests at logical scale1, all57 resources, embedded and blank textures, exact packed readback. D3D9 default post-device24-bit FPU precision (requested pre-device53/64 recorded separately) and controlled zero unwritten borders/blank textures; render targets excluded. Helper executes original DLL API, not full-game COM or whole-frame/audio/natural clear proof.')
        (destination/'native.json').write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8')
        print('PASS texture32 readback', precision, count, offset, stream.hexdigest(), flush=True)


if __name__ == '__main__':
    main()
