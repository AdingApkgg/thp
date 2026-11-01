"""Execute the original animation interpolation driver and beam callback.

Synthetic VM and call frames are component inputs. No native values go into
the production engine. This does not execute an original whole game.
"""
import hashlib, importlib, json, struct, sys
from pathlib import Path
from unicorn import Uc, UC_ARCH_X86, UC_MODE_32, UC_HOOK_MEM_WRITE, UC_HOOK_CODE
from unicorn.x86_const import *

R = Path(__file__).resolve().parents[1]
import argparse, itertools, shutil
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--output',type=Path,required=True)
parser.add_argument('--mixed',action='store_true')
args=parser.parse_args()
H=args.output.resolve()
assert H.is_relative_to(R/'artifacts/th14') and not H.exists()
assert shutil.disk_usage(R).free>=100*1024**3
H.mkdir()
sys.path.insert(0, str(R / 'tools'))
im, *_ = importlib.import_module('th-anm-handlers').handlers(14)
sha = lambda b: hashlib.sha256(b).hexdigest()
assert sha(im.data) == 'f08e885e28d2e0fc8c579e88034dd7de8f2a648d8f08ce781cf08eadc9ffe353'
m = Uc(UC_ARCH_X86, UC_MODE_32)
for _, address, size, offset, length in im.sections:
    first = address & ~4095
    m.mem_map(first, ((address + size + 4095) & ~4095) - first)
    m.mem_write(address, im.data[offset:offset + length])
end, vm, shot, area, target, player, stack = [0x70000000 + x for x in (0, 0x1000, 0x3000, 0x4000, 0x5000, 0x10000, 0xff02c)]
m.mem_map(end, 0x100000)
scratch = stack - 72
put = lambda p, v: m.mem_write(p, struct.pack('<I', v & 0xffffffff))
get = lambda p: struct.unpack('<I', m.mem_read(p, 4))[0]
bits = lambda v: struct.unpack('<I', struct.pack('<f', v))[0]
floats = lambda p, *v: m.mem_write(p, struct.pack('<' + 'f' * len(v), *v))
writes, reads = [], []
phase = ''

def write_hook(_m, access, address, size, value, _user):
    low, high = max(address,scratch), min(address+size,scratch+4)
    if low < high:
        shift=8*(low-scratch);width=8*(high-low)
        mask=((1<<width)-1)<<shift
        fragment=((value>>(8*(low-address)))<<shift)&mask
        combined=(get(scratch)&~mask)|fragment
        writes.append(dict(phase=phase, pc=m.reg_read(UC_X86_REG_EIP), size=size,
                           address=address, mask=mask, word=combined))

def read_hook(_m, pc, size, _user):
    actual = m.reg_read(UC_X86_REG_ESP) + 0x2c
    assert actual == scratch, (hex(actual), hex(scratch))
    reads.append(dict(pc=pc, address=actual, word=get(actual)))

# Unicorn filters this hook by the write's starting address. Include writes
# beginning before the word: movq may update its upper four bytes.
m.hook_add(UC_HOOK_MEM_WRITE, write_hook, begin=scratch-16, end=scratch+15)
m.hook_add(UC_HOOK_CODE, read_hook, begin=0x45286f, end=0x45286f)

def call(pc, sp, ecx, edx=0):
    for reg, value in [(UC_X86_REG_ESP, sp), (UC_X86_REG_ECX, ecx), (UC_X86_REG_EDX, edx),
                       (UC_X86_REG_FPCW, control_word), (UC_X86_REG_FPSW, 0),
                       (UC_X86_REG_FPTAG, 0xffff), (UC_X86_REG_MXCSR, 0x1f80)]:
        m.reg_write(reg, value)
    m.emu_start(pc, end, count=200000)
    assert m.reg_read(UC_X86_REG_EIP) == end

fields = [('position', 0x9c, 3, False), ('color', 0xf4, 3, True),
          ('alpha', 0x14c, 1, True), ('scale', 0x204, 2, False),
          ('extraScale', 0x248, 2, False), ('textureScale', 0x28c, 2, False),
          ('rotation', 0x17c, 3, False), ('color2', 0x2d0, 3, True),
          ('alpha2', 0x328, 1, True), ('scrollX', 0x358, 1, False),
          ('scrollY', 0x388, 1, False)]
work=[]
if args.mixed:
    for choices,modes,duration,rate,control_word in itertools.product(range(32),[(0,7,18),(17,17,21),(8,17,19)],[1,300],[0,1.25],[0x007f,0x037f]):
        mask=sum(1<<field for n,field in enumerate([0,1,3,6,7])if choices&(1<<n))
        if mask&(1<<3):mask|=(1<<4)|(1<<5)
        work.append(dict(field='mixed',mask=mask,vectorMode=modes[0],rgbMode=modes[1],vec2Mode=modes[2],duration=duration,rate=rate,x87ControlWord=control_word))
else:
    for field,(name,*_)in enumerate(fields):
        for mode,duration,rate,control_word in itertools.product(range(32),[-1,1,300],[0,.5,1,1.25],[0x007f,0x037f]):
            work.append(dict(field=name,mode=mode,mask=1<<field,vectorMode=mode,rgbMode=mode,vec2Mode=mode,duration=duration,rate=rate,x87ControlWord=control_word))
rows=[]
for case in work:
    duration,rate,control_word=case['duration'],case['rate'],case['x87ControlWord']
    phase = ''
    for address, size in [(vm, 0x700), (shot, 0x100), (area, 0x100),
                          (player, 0x19000), (stack - 0x2000, 0x2100)]:
        m.mem_write(address, bytes(size))
    put(0x4db67c, player)
    floats(0x4d8f58, rate)
    floats(0x4f7afc, 0, 0, 0)
    for field,(name,offset,n,integer)in enumerate(fields):
        if not(case['mask']&(1<<field)):continue
        mode=case['rgbMode']if field in(1,7)else case['vec2Mode']if field in(3,4,5)else case['vectorMode']
        interp=vm+offset
        for block,values in enumerate([[11,17,23],[31,47,59],[2,3,5],[7,11,13]]):
            for axis in range(n):
                (put if integer else lambda p,v:floats(p,v))(interp+block*n*4+axis*4,values[axis])
        timer=interp+20*n
        put(timer+12,0x4d8f58);put(timer+16,1);put(timer+20,duration);put(timer+24,mode)
    put(stack, end)
    put(scratch, bits(31.25))
    writes.clear(); reads.clear()
    phase = 'actual-animation-driver'
    call(0x473af0, stack, vm)
    retained, driver_writes = get(scratch), list(writes)
    assert (driver_writes[-1]['word'] if driver_writes else bits(31.25))==retained
    put(shot + 0xc0, area); put(shot + 0xa8, 1)
    put(shot + 0x18, 226); put(shot + 0x1c, 227)
    floats(shot + 0x54, 40, 259.9700012207031, 0)
    floats(shot + 0x70, -1.5707963705062866)
    floats(area + 0x24, 320.96453857421875, 16)
    floats(target, 64, -48, 0)
    beam_stack = stack - 36
    for index, value in enumerate([end, 0, 0, bits(16)]): put(beam_stack + 4 * index, value)
    phase = 'actual-beam-callback'
    call(0x452700, beam_stack, shot, target)
    assert len(reads) == 1 and reads[0]['word'] == retained
    mask=0
    for w in driver_writes:mask|=w['mask']
    rows.append(dict(field=case['field'],mode=case.get('mode'),mask=case['mask'],vectorMode=case['vectorMode'],rgbMode=case['rgbMode'],vec2Mode=case['vec2Mode'], duration=duration, rate=rate,x87ControlWord=control_word,writes=driver_writes,writeMask=mask,
                     retainedWord=retained, beamLengthWord=get(shot + 0xb0),
                     originalBeamRead=reads[0]))
report = dict(rows=rows,mixedInterpolationCases=args.mixed, originalExecutableSha256=sha(im.data),
              toolSha256=sha(Path(__file__).read_bytes()), syntheticCallFramesDeclared=True,
              actualOriginalDriverAndBeamExecuted=True, animationEntryMinusBeamEntry=36,
              scratchOffsetFromAnimationEntry=-72, originalInstructionsPatched=0,
              productionChanged=False, nativeValuesProvidedToEngine=False,
              completeGame=False, nativeEquivalent=False)
(H / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
(H / 'observer-source.py').write_bytes(Path(__file__).read_bytes())
assert sum(p.stat().st_size for p in H.rglob('*')if p.is_file())<=128*1024**2
assert shutil.disk_usage(R).free>=100*1024**3
print(json.dumps(dict(cases=len(rows),mixedInterpolationCases=args.mixed,originalInstructionsPatched=0)))
