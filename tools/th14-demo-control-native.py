"""Retail attract timeout/input decision at 436c08; callback boundaries recorded."""
import hashlib, importlib, itertools, json, struct
from pathlib import Path
from unicorn import Uc, UC_ARCH_X86, UC_MODE_32, UC_HOOK_CODE
from unicorn.x86_const import UC_X86_REG_EAX, UC_X86_REG_EDI, UC_X86_REG_ECX, UC_X86_REG_EDX, UC_X86_REG_ESP, UC_X86_REG_EIP

ROOT = Path(__file__).resolve().parents[1]

def main():
    img, _, _ = importlib.import_module('th-anm-handlers').handlers(14)
    m = Uc(UC_ARCH_X86, UC_MODE_32)
    for _, base, size, raw, n in img.sections:
        start = base & ~4095
        m.mem_map(start, ((base + size + 4095) & ~4095) - start)
        m.mem_write(base, img.data[raw:raw+n])
    base, stack = 0x70001000, 0x7000f000
    m.mem_map(0x70000000, 0x10000)
    def put(p, v): m.mem_write(p, struct.pack('<I', v & 0xffffffff))
    def get(p): return struct.unpack('<I', m.mem_read(p, 4))[0]
    fades = []
    def hook(uc, address, size, user):
        if address == 0x46d1c0:
            sp = uc.reg_read(UC_X86_REG_ESP)
            fades.append([uc.reg_read(UC_X86_REG_ECX), uc.reg_read(UC_X86_REG_EDX), *[get(sp+4+4*n) for n in range(4)]])
            uc.reg_write(UC_X86_REG_ESP, sp+20)
            uc.reg_write(UC_X86_REG_EIP, get(sp))
    m.hook_add(UC_HOOK_CODE, hook)
    rows = []
    frames = (0, 3540, 3600, 3839, 3840, 3841, 3899, 3900, 3901)
    inputs = (0, *[1 << n for n in range(20)], 0x80103, 0xffffffff)
    for frame, raw, system in itertools.product(frames, inputs, (0, 0x2000)):
        put(base+0x14, frame); put(0x4f58b8, 0x40)
        put(0x4d6878, raw); put(0x4d9684, system); put(0x4d964c, 0)
        m.reg_write(UC_X86_REG_ESP, stack); m.reg_write(UC_X86_REG_EDI, base); m.reg_write(UC_X86_REG_EAX, 0)
        fades.clear(); m.emu_start(0x436c08, 0x436c7b, count=1000)
        assert m.reg_read(UC_X86_REG_EIP) == 0x436c7b
        rows.append(dict(frame=frame, raw=raw, system=system, transition=get(0x4d964c), fades=fades.copy()))
    out = ROOT/'artifacts/th14/demo-control-native.json'
    out.write_text(json.dumps(dict(executableSha256=hashlib.sha256(img.data).hexdigest(), rows=rows)), encoding='utf-8')
    print(f'native demo decision: {len(rows)} cases')

if __name__ == '__main__': main()
