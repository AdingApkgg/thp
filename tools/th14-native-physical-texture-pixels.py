"""Read actual host64 D3DX textures using requests captured from original TH14.

Original32 upload request generation is separate. Hidden HAL device; no Present.
Unwritten texture borders and blank textures begin at controlled zero.
"""
import ctypes as C
import hashlib
import importlib
import json
import re
import struct
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'artifacts/th14/physical-texture-pixels'
OUT.mkdir(parents=True, exist_ok=True)
SDK = Path('C:/Program Files (x86)/Windows Kits/10/Include/10.0.26100.0/shared/d3d9.h')
P, U, I = C.c_void_p, C.c_uint32, C.c_int32
sha = lambda b: hashlib.sha256(b).hexdigest()


class Present(C.Structure):
    _fields_ = [(n, U) for n in ('width', 'height', 'format', 'count', 'multisample', 'quality', 'swap')] + [('window', P), ('windowed', I), ('depth', I)] + [(n, U) for n in ('depth_format', 'flags', 'refresh', 'interval')]


class Lock(C.Structure):
    _fields_ = [('pitch', I), ('bits', P)]


class Rect(C.Structure):
    _fields_ = [(n, I) for n in ('left', 'top', 'right', 'bottom')]


def main():
    tables = {}; header = SDK.read_text(encoding='utf-8')
    for name in ('IDirect3D9', 'IDirect3DDevice9', 'IDirect3DTexture9', 'IDirect3DSurface9'):
        body = header.split('DECLARE_INTERFACE_(' + name + ',', 1)[1].split('};', 1)[0]
        methods = [a.strip() or b.strip() for a, b in re.findall(r'STDMETHOD_\([^,]+,([^\)]+)\)|STDMETHOD\(([^\)]+)\)', body)]
        tables[name] = {n: i for i, n in enumerate(methods)}

    def method(obj, interface, name, types):
        return C.WINFUNCTYPE(I, P, *types)(C.cast(obj, C.POINTER(C.POINTER(P))).contents[tables[interface][name]])

    def call(obj, interface, name, types, values):
        hr = method(obj, interface, name, types)(obj, *values)
        assert hr >= 0, (name, hex(hr & 0xffffffff))
        return hr

    user = C.WinDLL('user32'); user.CreateWindowExW.restype = P
    user.CreateWindowExW.argtypes = [U, C.c_wchar_p, C.c_wchar_p, U, I, I, I, I, P, P, P, P]
    user.DestroyWindow.argtypes = [P]
    dll = C.WinDLL('d3d9'); dll.Direct3DCreate9.restype = P; dll.Direct3DCreate9.argtypes = [U]
    d3dx = C.WinDLL('d3dx9_43')
    create = d3dx.D3DXCreateTexture; create.restype = I; create.argtypes = [P, U, U, U, U, U, U, C.POINTER(P)]
    upload = d3dx.D3DXLoadSurfaceFromMemory; upload.restype = I; upload.argtypes = [P, P, P, P, U, U, P, P, U, U]
    proof_bytes = (ROOT / 'artifacts/th14/anm-physical-resource-loader/native.json').read_bytes()
    proof = json.loads(proof_bytes)
    archive = json.loads((ROOT / 'artifacts/archive-differential/th14.json').read_text(encoding='utf-8'))
    parser = importlib.import_module('th-anm-script-dump')
    rows = [r for r in proof['rows'] if r['rate'] == 1]; assert len(rows) == 57
    bpps = {20: 3, 21: 4, 22: 4, 23: 2, 25: 2, 26: 2, 28: 1, 29: 2}
    device, d3d, texture, surface = P(), P(), P(), P()
    window = None; cases = []; byte_count = 0; stream = hashlib.sha256()
    try:
        window = user.CreateWindowExW(0, 'STATIC', 'TH14 physical texture readback', 0, 0, 0, 64, 64, None, None, None, None); assert window
        d3d = P(dll.Direct3DCreate9(32)); assert d3d
        pp = Present(32, 32, 21, 1, 0, 0, 1, window, 1, 0, 0, 0, 0, 0x80000000)
        call(d3d, 'IDirect3D9', 'CreateDevice', [U, U, P, U, P, C.POINTER(P)], [0, 1, window, 64, C.byref(pp), C.byref(device)])
        with (OUT / 'textures.bin').open('wb') as destination_file:
            for row in rows:
                raw = (Path(archive['extraction']) / row['name']).read_bytes(); assert sha(raw) == row['sha256']
                chunks = list(parser.chunks(raw)); assert len(chunks) == row['chunks']
                for record, (offset, chunk) in zip(row['uploads'], chunks):
                    if record['kind'] == 'renderTarget': continue
                    width, height, levels, usage, fmt, pool = record['creationArguments']
                    hr = create(device, width, height, levels, usage, fmt, pool, C.byref(texture)); assert hr >= 0, (row['name'], record['chunk'], hex(hr & 0xffffffff))
                    desc = (U * 8)(); call(texture, 'IDirect3DTexture9', 'GetLevelDesc', [U, P], [0, C.byref(desc)])
                    actual_format, actual_width, actual_height = desc[0], desc[6], desc[7]
                    assert (actual_width, actual_height) == (width, height)
                    bpp = bpps[actual_format]
                    lock = Lock(); call(texture, 'IDirect3DTexture9', 'LockRect', [U, P, P, U], [0, C.byref(lock), None, 0])
                    for y in range(height): C.memset(lock.bits + y * lock.pitch, 0, width * bpp)
                    call(texture, 'IDirect3DTexture9', 'UnlockRect', [U], [0])
                    if record['kind'] == 'embedded':
                        tex_offset = struct.unpack_from('<I', chunk, 28)[0]
                        pixels = chunk[tex_offset + 16:tex_offset + 16 + record['sourceBytes']]
                        assert len(pixels) == record['sourceBytes'] and sha(pixels) == record['sourceSha256']
                        source = C.create_string_buffer(pixels)
                        call(texture, 'IDirect3DTexture9', 'GetSurfaceLevel', [U, C.POINTER(P)], [0, C.byref(surface)])
                        d, s = Rect(*record['destinationRect']), Rect(*record['sourceRect'])
                        hr = upload(surface, None, C.byref(d), source, record['sourceFormat'], record['pitch'], None, C.byref(s), record['filter'], 0); assert hr >= 0
                        method(surface, 'IDirect3DSurface9', 'Release', [])(surface); surface = P()
                    call(texture, 'IDirect3DTexture9', 'LockRect', [U, P, P, U], [0, C.byref(lock), None, 16])
                    result = b''.join(C.string_at(lock.bits + y * lock.pitch, width * bpp) for y in range(height))
                    call(texture, 'IDirect3DTexture9', 'UnlockRect', [U], [0])
                    cases.append(dict(name=row['name'], chunk=record['chunk'], kind=record['kind'], requestedFormat=fmt, format=actual_format, width=width, height=height, pitch=width*bpp, offset=byte_count, bytes=len(result), sha256=sha(result)))
                    destination_file.write(result); stream.update(result); byte_count += len(result)
                    method(texture, 'IDirect3DTexture9', 'Release', [])(texture); texture = P()
                print('physical texture readback', row['name'], len(cases), flush=True)
        report = dict(passed=True, completeGame=False, nativeEquivalent=False, cases=cases, bytes=byte_count, binarySha256=stream.hexdigest(), requestProofSha256=sha(proof_bytes), toolSha256=sha(Path(__file__).read_bytes()), parserSha256=sha((ROOT/'tools/th-anm-script-dump.py').read_bytes()), sdkHeaderSha256=sha(SDK.read_bytes()), d3d9Sha256=sha(Path('C:/Windows/System32/d3d9.dll').read_bytes()), d3dxSha256=sha(Path('C:/Windows/System32/d3dx9_43.dll').read_bytes()), scope='Actual hidden D3D9 HAL managed textures and host64 D3DX9_43 CreateTexture/LoadSurfaceFromMemory using original32 TH14 captured creation/upload requests at logical scale1, all57 resources, embedded and blank textures, exact raw packed readback bytes. Destination padding/blank textures initialized to controlled zero, render targets excluded. Device format adjustment observed; host64 API counterpart, not original32 COM upload execution. No whole-frame, audio or natural clear claim.')
        (OUT / 'native.json').write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8')
        print('PASS physical textures', len(cases), byte_count)
    finally:
        for obj, interface in ((surface, 'IDirect3DSurface9'), (texture, 'IDirect3DTexture9'), (device, 'IDirect3DDevice9'), (d3d, 'IDirect3D9')):
            if obj.value: method(obj, interface, 'Release', [])(obj)
        if window: user.DestroyWindow(window)


if __name__ == '__main__': main()
