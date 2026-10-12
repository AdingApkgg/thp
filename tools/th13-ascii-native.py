"""Observe TH13's original ASCII layout, replacing only sprite/GPU submission.

The native 4042a0 string routine runs unchanged, including glyph selection,
spacing, line breaks, filtering and shadows. The synthetic atlas is never read
for pixels; its sprite pointers identify which original glyph was requested.
"""
import importlib
import hashlib
import json
import struct
from pathlib import Path
from unicorn import Uc, UC_ARCH_X86, UC_MODE_32, UC_HOOK_CODE
from unicorn.x86_const import *

ROOT = Path(__file__).resolve().parents[1]
SUP, REQUEST, RESOURCE, ATLAS, STACK, RETURN = (
    0x70000000, 0x70020000, 0x70021000, 0x70022000, 0x7003f000, 0x70040000)


def main():
    img, _, _ = importlib.import_module('th-anm-handlers').handlers(13)
    m = Uc(UC_ARCH_X86, UC_MODE_32)
    for _, base, size, raw, n in img.sections:
        begin = base & ~4095
        m.mem_map(begin, ((base + size + 4095) & ~4095) - begin)
        m.mem_write(base, img.data[raw:raw+n])
    m.mem_map(SUP, 0x41000)
    def put(p, value): m.mem_write(p, struct.pack('<I', value & 0xffffffff))
    def get(p): return struct.unpack('<I', m.mem_read(p, 4))[0]
    def flt(p): return struct.unpack('<f', m.mem_read(p, 4))[0]
    # Binding exposes the selected atlas entry without introducing graphics.
    m.mem_write(0x404ea0, b'\xc3')
    m.mem_write(0x467b50, b'\xc2\x08\x00')
    m.mem_write(0x467350, b'\xc2\x04\x00')
    glyphs = []
    def observe(machine, address, size, user):
        if address == 0x404ea0:
            put(SUP + 0x40, machine.reg_read(UC_X86_REG_ECX))
        else:
            glyphs.append(dict(sprite=(get(SUP+0x40)-ATLAS)//72,
                x=flt(SUP+0x50), y=flt(SUP+0x54), color=get(SUP+0x53c),
                filtered=bool(get(SUP+0x30)&0x400)))
    for address in (0x404ea0, 0x467350):
        m.hook_add(UC_HOOK_CODE, observe, begin=address, end=address)
    cases = []
    texts = [''.join(chr(c) for c in range(33, 127)),
             '0123456789 /:.-*%$+s,', 'Abcz Z\n1. 2,3 s.4', '. .\n, ,\nss']
    for font in range(8):
        for sx, sy in ((1., 1.), (1.5, .75), (.5, 2.)):
            for shadow in (False, True):
                for text in texts:
                    m.mem_write(SUP, bytes(0x191a4));m.mem_write(REQUEST, bytes(0x138))
                    m.mem_write(REQUEST, text.encode('ascii') + b'\0')
                    m.mem_write(REQUEST+0x100, struct.pack('<3fI2f', 16.25, 28.5, 0., 0xa5345678, sx, sy))
                    for off, value in ((0x120,font),(0x124,int(shadow)),(0x130,1),(0x134,1)):
                        put(REQUEST+off,value)
                    put(SUP+0x19194, RESOURCE);put(RESOURCE+0x11c, ATLAS);put(SUP+0x1918c, 9)
                    m.mem_write(STACK, struct.pack('<3I', RETURN, SUP, REQUEST))
                    m.reg_write(UC_X86_REG_ESP, STACK)
                    m.reg_write(UC_X86_REG_FPCW, 0x37f);m.reg_write(UC_X86_REG_FPSW,0)
                    m.reg_write(UC_X86_REG_FPTAG,0xffff)
                    glyphs.clear()
                    m.emu_start(0x4042a0, RETURN, count=100000)
                    assert m.reg_read(UC_X86_REG_EIP)==RETURN
                    cases.append(dict(font=font,scale=[sx,sy],shadow=shadow,text=text,glyphs=list(glyphs)))
    out = ROOT/'artifacts/th13/ascii-native.json';out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(dict(executableSha256=hashlib.sha256(img.data).hexdigest(),
        scope='Original string layout; sprite binding and GPU calls substituted.',cases=cases),indent=2)+'\n',encoding='utf-8')
    print(f'{len(cases)} original TH13 string layouts; {sum(len(c["glyphs"]) for c in cases)} glyph submissions.')


if __name__ == '__main__': main()
