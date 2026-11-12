"""Execute retail display-mode selection and dimensions without starting the game."""
from pathlib import Path
import hashlib, importlib, itertools, json, struct, sys
from unicorn import Uc, UC_ARCH_X86, UC_MODE_32
from unicorn.x86_const import UC_X86_REG_ECX, UC_X86_REG_ESP, UC_X86_REG_EIP, UC_X86_REG_ESI

R = Path(__file__).resolve().parents[1]
H = R / 'artifacts/th14/display-mode-entry-nov12'
assert H.exists() and not (H / 'native.json').exists()
sys.path.insert(0, str(R / 'tools'))
im = importlib.import_module('th12-pe').Image('H:/Games/th/14/th14.exe')
sha = lambda data: hashlib.sha256(data).hexdigest()
assert sha(im.data) == 'f08e885e28d2e0fc8c579e88034dd7de8f2a648d8f08ce781cf08eadc9ffe353'
m = Uc(UC_ARCH_X86, UC_MODE_32)
for _, va, size, off, count in im.sections:
    page = va & ~4095
    m.mem_map(page, ((va + size + 4095) & ~4095) - page)
    m.mem_write(va, im.data[off:off + count])
B = 0x78000000
m.mem_map(B, 0x10000)
stack, stop = B + 0xf000, B + 0xe000
put = lambda p, value: m.mem_write(p, struct.pack('<I', value))
get = lambda p: struct.unpack('<I', m.mem_read(p, 4))[0]
rows = []
for mode, initial, skip, vsync in itertools.product(range(6), (0, 1, 0x180, 0xf3c0), range(3), range(3)):
    cfg = bytearray(92)
    cfg[0x1f], cfg[0x20], cfg[0x25] = mode, skip, vsync
    m.mem_write(0x4d9134, bytes(cfg))
    put(0x4f7a54, initial)
    m.emu_start(0x46af64, 0x46afab, count=100)
    assert m.reg_read(UC_X86_REG_EIP) == 0x46afab
    flags, windowed = get(0x4f7a54), get(0x4d9074)
    expected = (initial & ~0x3c) | (mode << 2)
    expected = expected | 0x40 if skip == 0 and vsync == 2 else expected & ~0x40
    assert flags == expected and windowed == int(mode >= 3)
    put(stack, stop)
    m.reg_write(UC_X86_REG_ESP, stack)
    m.reg_write(UC_X86_REG_ECX, 0x4f5a18)
    m.emu_start(0x46ae40, stop, count=100)
    assert m.reg_read(UC_X86_REG_EIP) == stop
    width, height, scale = get(0x4f7a64), get(0x4f7a68), get(0x4f7a6c)
    assert (width, height) == [(640, 480), (960, 720), (1280, 960)][mode % 3]
    assert scale == struct.unpack('<I', struct.pack('<f', width / 640))[0]
    rows.append(dict(mode=mode, initialFlags=initial, frameSkip=skip, vsync=vsync,
                     selectedFlags=flags, windowed=windowed, width=width, height=height,
                     scaleBits=scale, playOrigin=[get(0x4f7a70), get(0x4f7a74)]))
assert len(rows) == 216
report = dict(schema='thp/th14-display-mode-selection/1', rows=rows, cases=len(rows),
              originalCodeUnmodified=True, nativeGameStarted=False, gpuStarted=False,
              configInputsSynthetic=True, completeGame=False,
              executableSha256=sha(im.data), toolSha256=sha(Path(__file__).read_bytes()),
              instructionBindings={hex(a): sha(im.read(a, b-a)) for a, b in
                                   [(0x46af64, 0x46afab), (0x46ae40, 0x46aeee)]})
(H / 'native.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps({k: v for k, v in report.items() if k != 'rows'}))
