"""Run the original x64 ANM table loader in Unicorn, without game/Steam/GPU calls.

Compare JS resource fields to native UVs, sprite extents and script pointers.
This is not execution of the ANM animation VM or rendered-pixel acceptance.
"""
import hashlib
import importlib
import json
import struct
import subprocess
from pathlib import Path
from unicorn import Uc, UC_ARCH_X86, UC_MODE_64
from unicorn.x86_const import UC_X86_REG_RBX, UC_X86_REG_RDI, UC_X86_REG_RSI, UC_X86_REG_R14, UC_X86_REG_R15, UC_X86_REG_RSP, UC_X86_REG_RBP

ROOT = Path(__file__).resolve().parents[1]


def main():
    target = json.loads((ROOT/'runtimes/th06nc/target.json').read_bytes())
    blob = Path(target['executable']).read_bytes()
    assert hashlib.sha256(blob).hexdigest() == target['sha256']
    script = """
import {readFileSync} from 'node:fs';
import {readAnm} from './shared/th06nc/anm.mjs';
const files=JSON.parse(readFileSync('artifacts/th06nc/scripts.json')).filter(f=>f.name.endsWith('.anm'));
console.log(JSON.stringify(files.map(f=>({...f,parsed:readAnm(readFileSync(f.path))})),(k,v)=>k==='instructions'?undefined:v));
"""
    rows = json.loads(subprocess.check_output(['node', '--input-type=module', '-e', script], cwd=ROOT))
    machine = Uc(UC_ARCH_X86, UC_MODE_64)
    machine.mem_map(0x140000000, 0xd00000)
    for sec in importlib.import_module('th-disasm').sections(blob):
        machine.mem_write(0x140000000+sec['va'], blob[sec['raw']:sec['raw']+sec['rawsize']])
    asset, manager, stack = 0x70000000, 0x71000000, 0x72000000
    machine.mem_map(asset, 0x100000)
    machine.mem_map(manager, 0x40000)
    machine.mem_map(stack, 0x10000)
    f32 = lambda x: struct.unpack('<f', struct.pack('<f', x))[0]
    digest = hashlib.sha256()
    sprite_count = script_count = 0
    for row in rows:
        data = Path(row['path']).read_bytes()
        assert hashlib.sha256(data).hexdigest() == row['sha256']
        machine.mem_write(asset, data)
        machine.mem_write(manager, bytes(0x40000))
        machine.mem_write(stack, bytes(0x10000))
        machine.mem_write(manager+8, struct.pack('<Q', asset))
        machine.reg_write(UC_X86_REG_RBP, stack+0x8100)
        for reg, val in [(UC_X86_REG_RBX, manager), (UC_X86_REG_RDI, asset), (UC_X86_REG_RSI, 0), (UC_X86_REG_R14, 0), (UC_X86_REG_R15, 0), (UC_X86_REG_RSP, stack+0x8000)]:
            machine.reg_write(reg, val)
        # All code in this interval is the original loader; no API hooks/stubs.
        machine.emu_start(0x1400024ae, 0x14000270b, count=1000000)
        a = row['parsed']
        last_sprites = {s['id']: s for s in a['sprites']}
        for ident, s in last_sprites.items():
            ptr = manager+0x608+ident*64
            raw = bytes(machine.mem_read(ptr, 16))
            expected = struct.pack('<4f', f32(s['x']/a['width']), f32(s['y']/a['height']), f32(f32(s['x']+s['width'])/a['width']), f32(f32(s['y']+s['height'])/a['height']))
            assert raw == expected, (row['name'], ident, 'UV mismatch')
            extents = bytes(machine.mem_read(ptr+0x14, 8))
            expected_extents = struct.pack('<2f', f32(f32(s['y']+s['height'])-s['y']), f32(f32(s['x']+s['width'])-s['x']))
            assert extents == expected_extents, (row['name'], ident, 'extent mismatch')
            digest.update(raw+extents)
            sprite_count += 1
        for ident, s in {s['id']: s for s in a['scripts']}.items():
            pointer, = struct.unpack('<Q', machine.mem_read(manager+0x23090+ident*8, 8))
            assert pointer == asset+s['offset'], (row['name'], ident, 'script pointer mismatch')
            digest.update(struct.pack('<II', ident, pointer-asset))
            script_count += 1
    report = dict(scope=__doc__, executableSha256=target['sha256'], readerSha256=hashlib.sha256((ROOT/'shared/th06nc/anm.mjs').read_bytes()).hexdigest(), nativeRange=['0x1400024ae', '0x14000270b'], files=len(rows), finalSpriteBindings=sprite_count, finalScriptBindings=script_count, comparedBytesSha256=digest.hexdigest(), passed=True, completeGame=False, nativeEquivalent=False)
    (ROOT/'docs/porting/th06nc-anm-native-verified.json').write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8')
    print(json.dumps(report))


if __name__ == '__main__':
    main()
