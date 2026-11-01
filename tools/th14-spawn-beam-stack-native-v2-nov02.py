"""Execute original vector sampling and beam fallback on a shared stack word.

The two call-frame offsets are declared component ABI inputs established by
live writer/read observations. Allocation, ECL dispatch and the full game are
not executed by this component experiment.
"""
import argparse, hashlib, importlib, itertools, json, struct
from pathlib import Path
from unicorn import Uc, UC_ARCH_X86, UC_MODE_32, UC_HOOK_CODE, UC_HOOK_MEM_WRITE
from unicorn.x86_const import *

R = Path(__file__).resolve().parents[1]
p = argparse.ArgumentParser(description=__doc__)
p.add_argument('--output', type=Path, required=True)
a = p.parse_args()
assert not a.output.exists()
im, _, _ = importlib.import_module('th-anm-handlers').handlers(14)
SHA = lambda b: hashlib.sha256(b).hexdigest()
assert SHA(im.data) == 'f08e885e28d2e0fc8c579e88034dd7de8f2a648d8f08ce781cf08eadc9ffe353'
m = Uc(UC_ARCH_X86, UC_MODE_32)
for _, address, size, offset, length in im.sections:
    first = address & ~4095
    m.mem_map(first, ((address + size + 4095) & ~4095) - first)
    m.mem_write(address, im.data[offset:offset + length])
end, interp, out, shot, area, target, player, stack = [0x70000000 + x for x in (0, 0x1000, 0x2000, 0x3000, 0x4000, 0x5000, 0x10000, 0xff010)]
m.mem_map(end, 0x100000)
scratch = stack - 44
put = lambda p, v: m.mem_write(p, struct.pack('<I', v & 0xffffffff))
get = lambda p: struct.unpack('<I', m.mem_read(p, 4))[0]
bits = lambda v: struct.unpack('<I', struct.pack('<f', v))[0]
floats = lambda p, *v: m.mem_write(p, struct.pack('<' + 'f' * len(v), *v))
writes, reads = [], []
phase = ''
def write_hook(_m, access, address, size, value, _user):
    if address <= scratch and scratch + 4 <= address + size:
        writes.append(dict(phase=phase, pc=m.reg_read(UC_X86_REG_EIP),
                           word=(value >> (8 * (scratch - address))) & 0xffffffff))
def read_hook(_m, pc, size, _user):
    actual = m.reg_read(UC_X86_REG_ESP) + 0x2c
    assert actual == scratch
    reads.append(dict(pc=pc, address=actual, word=get(actual)))
m.hook_add(UC_HOOK_MEM_WRITE, write_hook, begin=scratch, end=scratch + 3)
m.hook_add(UC_HOOK_CODE, read_hook, begin=0x45286f, end=0x45286f)
def call(pc, sp, ecx, edx=0):
    for reg, value in [(UC_X86_REG_ESP, sp), (UC_X86_REG_ECX, ecx), (UC_X86_REG_EDX, edx),
                       (UC_X86_REG_FPCW, 0x37f), (UC_X86_REG_FPSW, 0),
                       (UC_X86_REG_FPTAG, 0xffff), (UC_X86_REG_MXCSR, 0x1f80)]:
        m.reg_write(reg, value)
    m.emu_start(pc, end, count=200000)
    assert m.reg_read(UC_X86_REG_EIP) == end
rows = []
for mode, duration, z, rate in itertools.product(range(32), [-1, 1, 300], [-16., 0., 115.41128540039062, 240.], [0., .5, 1., 1.25]):
    phase = ''
    for address, size in [(interp, 0x100), (shot, 0x100), (area, 0x100), (player, 0x19000), (stack - 0x2000, 0x2100)]:
        m.mem_write(address, bytes(size))
    put(0x4db67c, player)
    floats(0x4d8f58, rate)
    floats(0x4f7afc, 0, 0, 0)
    floats(interp, 1, 2, z, 3, 4, 83.97372436523438)
    floats(interp + 0x18, 0, 0, .125, 0, 0, -.25)
    put(interp + 0x48, 0x4d8f58)
    put(interp + 0x4c, 1)
    put(interp + 0x50, duration)
    put(interp + 0x54, mode)
    put(stack, end)
    put(stack + 4, out)
    put(scratch, bits(31.25))  # Declared initial stack state, before both calls.
    writes.clear()
    reads.clear()
    phase = 'vector-sample'
    call(0x409bd0, stack, interp)
    sampled_z = get(out + 8)
    retained = get(scratch)
    vector_writes = list(writes)
    expected_hook=get(interp+0x2c)if mode==17 else sampled_z
    assert bool(vector_writes)==bool(get(interp+0x50))
    if vector_writes:assert vector_writes[-1]['word']==expected_hook
    put(shot + 0xc0, area)
    put(shot + 0xa8, 1)
    put(shot + 0x18, 226)
    put(shot + 0x1c, 227)
    floats(shot + 0x54, 40, 259.9700012207031, 0)
    floats(shot + 0x70, -1.5707963705062866)
    floats(area + 0x24, 320.96453857421875, 16)
    floats(target, 64, -48, 0)
    beam_stack = stack - 8
    for index, value in enumerate([end, 0, 0, bits(16)]): put(beam_stack + 4 * index, value)
    phase = 'beam-hit'
    call(0x452700, beam_stack, shot, target)
    assert len(reads) == 1 and reads[0]['word'] == retained
    assert get(area + 0x24) == get(shot + 0xb0)
    expected = max(0., struct.unpack('<f', struct.pack('<I', retained))[0] + 8.)
    assert get(shot + 0xb0) == bits(expected)
    rows.append(dict(mode=mode, duration=duration, startZ=bits(z), rate=bits(rate), sampledZ=sampled_z,
                     originalVectorWrites=vector_writes, wordRead=reads[0], beamLength=get(shot + 0xb0),
                     interpolatorTerminalDuration=get(interp+0x50),expectedHookWord=expected_hook,vectorTemporaryWritten=bool(vector_writes), lastVectorWriteEqualsSampledZ=bool(vector_writes) and vector_writes[-1]['word'] == sampled_z))
report = dict(executableSha256=SHA(im.data), toolSha256=SHA(Path(__file__).read_bytes()), cases=rows,
              actualVectorSamplerAndBeamCallbackExecuted=True, originalInstructionBytesPatched=0,
              scratchNotWrittenByObserverBetweenFunctions=True, syntheticCallFramesDeclared=True,
              vectorEntryMinusBeamEntry=8, scratchOffsetFromVectorEntry=-44,
              eclAndAllocationAndOriginalWholeGameNotExecuted=True, nativeValuesProvidedToPortableEngine=False,
              completeGame=False, nativeEquivalent=False)
a.output.write_text(json.dumps(report, indent=2) + '\n', encoding='utf8')
print(json.dumps(dict(cases=len(rows), temporaryWritten=sum(x['vectorTemporaryWritten'] for x in rows),
                      writerPcs=sorted({hex(w['pc']) for x in rows for w in x['originalVectorWrites']}))))
