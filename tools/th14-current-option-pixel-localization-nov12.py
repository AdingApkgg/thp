"""Localize retained frame differences without changing a live application.

Quad reconstruction is a component diagnostic, never a pixel acceptance mask.
"""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import importlib
import json
import struct
import sys

R = Path(__file__).resolve().parents[1]
H = R / 'artifacts/th14/current-low-pause-pixels-nov12'
N = R / 'artifacts/th14/low-pause-present-capture-nov09/native-three-sites'
O = H / 'localization-v2'
load = lambda p: json.loads(p.read_bytes())
sha = lambda b: hashlib.sha256(b).hexdigest()
w = lambda b, offset: struct.unpack_from('<I', b, offset)[0]
f = lambda bits: struct.unpack('<f', struct.pack('<I', bits))[0]
q = load(H / 'qualified.json')
assert q['allOwnedResourcesRetired'] and q['beforePlayerStrict113AllExact']
assert q['nativeVms'] == q['cppVms'] == 321 and q['differentVmWords'] == 20
assert q['strictRegistryOrderEqual'] and q['postFrameCameraWordsExact']
differences = load(H / 'vm-private-differences.json')
assert len(differences) == 20
assert all(d['file'] == 9 and d['script'] == 10 and d['field'] in
    ['ageCurrent', 'nativeVmWord0x55c', 'nativeVmWord0x560', 'nativeVmWord0x564', 'nativeVmWord0x50'] for d in differences)
sys.path[:0] = [str(R / 'tools/tmp/th14-analysis-python'), str(R / 'tools')]
from unicorn import Uc, UC_ARCH_X86, UC_MODE_32
from unicorn.x86_const import (UC_X86_REG_ESP, UC_X86_REG_ECX, UC_X86_REG_EIP,
    UC_X86_REG_MXCSR, UC_X86_REG_FPCW, UC_X86_REG_FPSW, UC_X86_REG_FPTAG)
from PIL import Image
image = importlib.import_module('th12-pe').Image('H:/Games/th/14/th14.exe')
assert sha(image.data) == 'f08e885e28d2e0fc8c579e88034dd7de8f2a648d8f08ce781cf08eadc9ffe353'
m = Uc(UC_ARCH_X86, UC_MODE_32)
for _, va, size, offset, count in image.sections:
    first = va & ~4095
    m.mem_map(first, ((va + size + 4095) & ~4095) - first)
    m.mem_write(va, image.data[offset:offset + count])
BASE, VM, OUTPUT, STACK, STOP = 0x70000000, 0x70001000, 0x70003000, 0x700ff000, 0x700fe000
m.mem_map(BASE, 0x100000)
m.mem_write(0x4854a0, b'\xc3')
frame_header = (N / 'target-frame-header.bin').read_bytes()
assert len(frame_header) == 256
render_globals = frame_header[192:228]
assert len(render_globals) == 36
m.mem_write(0x4f7a6c, render_globals)


def quad(vm):
    m.mem_write(VM, vm)
    m.mem_write(OUTPUT, bytes(48))
    m.mem_write(STACK, struct.pack('<II', STOP, OUTPUT))
    for reg, value in [(UC_X86_REG_ESP, STACK), (UC_X86_REG_ECX, VM),
        (UC_X86_REG_MXCSR, 0x1f80), (UC_X86_REG_FPCW, 0x37f),
        (UC_X86_REG_FPSW, 0), (UC_X86_REG_FPTAG, 0xffff)]:
        m.reg_write(reg, value)
    m.emu_start(0x479560, STOP, count=100000)
    assert m.reg_read(UC_X86_REG_EIP) == STOP
    assert bytes(m.mem_read(VM, len(vm))) == vm
    words = list(struct.unpack('<12I', m.mem_read(OUTPUT, 48)))
    return words, [[f(words[i*3]), f(words[i*3+1])] for i in range(4)]


native = load(N / 'live-vms-before-readback.json')
quads, cases = [], []
for row in native['rows']:
    if row['file'] != 9 or row['script'] != 10:
        continue
    raw = bytes.fromhex(row['rawVmHex'])
    assert len(raw) == 0x5cc and not w(raw, 0x594) and (w(raw, 0x18) >> 25) & 31 == 1
    delta = [d for d in differences if d['handle'] == row['handle']]
    assert len(delta) == 5
    rotation = next(d for d in delta if d['field'] == 'nativeVmWord0x50')
    assert w(raw, 0x50) == rotation['native']
    changed = bytearray(raw)
    struct.pack_into('<I', changed, 0x50, rotation['cpp'])
    original, points = quad(raw)
    counterfactual, cpp_points = quad(bytes(changed))
    restored, _ = quad(raw)
    assert restored == original
    age = next(d for d in delta if d['field'] == 'ageCurrent')
    angle = f(rotation['cpp'])
    steps = age['native'] - age['cpp']
    assert steps == 3
    for _ in range(steps):
        angle = f(w(struct.pack('<f', float(angle + f(w(raw, 0x5c)))), 0))
        while angle > f(0x40490fdb):
            angle = f(w(struct.pack('<f', float(angle - f(0x40c90fdb))), 0))
        while angle < -f(0x40490fdb):
            angle = f(w(struct.pack('<f', float(angle + f(0x40c90fdb))), 0))
    angle_exact = w(struct.pack('<f', angle), 0) == rotation['native']
    assert angle_exact
    quads.extend([points, cpp_points])
    cases.append(dict(handle=row['handle'], nativeAge=age['native'], cppAge=age['cpp'],
        ageGap=steps, threeAngularUpdatesExplainRotationExactly=angle_exact,
        nativeQuadWords=original, cppAngleQuadWords=counterfactual,
        nativeAngleRestoreExact=True))
assert len(cases) == 4 and len(quads) == 8
# Declared final 640px composition mapping, not fitted from differing pixels.
# Current reset producer uses intermediate viewport x128 and window viewport x32.
compositor_source = R / 'runtimes/th12/th12_web/cpp/game/SceneCompositor.cpp'
compositor = compositor_source.read_text()
assert 'play_camera.viewport={u32(32*scale)' in compositor
assert 'scaled_play_camera.viewport.x=u32(128*scale)' in compositor
assert load(N / 'report.json')['readback']['surfaceDescription'][6:8] == [640,480]
assert struct.unpack_from('<i', render_globals, 4)[0] == 128
quads = [[[x + (32-128), y] for x,y in vertices] for vertices in quads]



def inside_triangle(p, a, b, c):
    cross = lambda u, v, x: (v[0]-u[0])*(x[1]-u[1]) - (v[1]-u[1])*(x[0]-u[0])
    signs = [cross(a, b, p), cross(b, c, p), cross(c, a, p)]
    return all(x >= 0 for x in signs) or all(x <= 0 for x in signs)


def inside(p, vertices):
    return inside_triangle(p, *[vertices[i] for i in [0, 1, 2]]) or inside_triangle(p, *[vertices[i] for i in [1, 3, 2]])


nb = (N / 'native-before-present-1200.bgra').read_bytes()
cb = (H / 'current/application-stage3-frame1200.bgra').read_bytes()
assert len(nb) == len(cb) == 640*480*4 and sha(nb) == load(N / 'report.json')['readback']['pixelSha256']
different = [(i % 640, i // 640) for i in range(640*480) if nb[i*4:i*4+4] != cb[i*4:i*4+4]]
assert len(different) == q['differentPixels'] == 854
counts = []
for center in [0, .5]:
    outside = [[x, y] for x, y in different if not any(inside((x+center, y+center), vertices) for vertices in quads)]
    counts.append(dict(pixelSampleOffset=center, insideUnion=len(different)-len(outside),
        outsideUnion=len(outside), outsidePixelCoordinates=outside))
assert not O.exists()
O.mkdir()
for name, b in [('native', nb), ('current', cb)]:
    Image.frombytes('RGBA', (640, 480), b, 'raw', 'BGRA').convert('RGB').save(O / (name+'.png'))
mask = bytearray(640*480*3)
for x, y in different:
    at = (y*640+x)*3
    mask[at:at+3] = bytes([255, 80, 180])
Image.frombytes('RGB', (640, 480), bytes(mask)).save(O / 'all-different-pixels.png')
report = dict(recordedAt=datetime.now(timezone.utc).isoformat(), diagnosticOnly=True,
    actualFramePixelsCompared=640*480, differentPixels=len(different), cases=cases,
    reconstructedQuadFootprintCounts=counts,
    finalCompositionTranslationDeclared=[-96,0],
    actualDetachedCopyStateNotCapturedInRetainedNativeReference=True,
    exactDirectCausalityOrGpuRasterCoverageNotProvenByFootprint=True,
    noMaskOrPixelToleranceUsedForAcceptance=True, strictWholeFrameStillFails=True,
    noLiveEngineStateChanged=True, noAgeOrRngOrWaitPadding=True,
    geometryEntry='0x479560', declaredCookieReturnService='0x4854a0',
    x87ControlWord='0x037f', mxcsr='0x1f80', originalVmRawInputsClonedOnly=True,
    newOriginalOsGameOrGpuOrAudio=False, productionChanged=False,
    completeGame=False, nativeEquivalent=False,
    bindings={p.relative_to(R).as_posix(): dict(bytes=p.stat().st_size, sha256=sha(p.read_bytes())) for p in
        [Path(__file__), compositor_source, H / 'qualified.json', H / 'vm-private-differences.json',
         N / 'live-vms-before-readback.json', N / 'target-frame-header.bin',
         N / 'native-before-present-1200.bgra', H / 'current/application-stage3-frame1200.bgra']})
(O / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps(dict(differentPixels=len(different), allFourAngleGapsExplainedByThreeUpdates=True,
    footprints=[{k: v for k, v in c.items() if k != 'outsidePixelCoordinates'} for c in counts],
    strictWholeFrameStillFails=True)))
