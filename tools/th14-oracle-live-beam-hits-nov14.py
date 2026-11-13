"""Original 452700 on captured real beam owner inputs and declared stack scratch.

ANM allocation, lookup, family interrupt and CRT cookie service are intercepted
external boundaries. No native instruction bytes are changed. Visual output and
the original caller's full stack history remain outside this component test.
"""
from pathlib import Path
import hashlib, importlib, json, struct
from unicorn import Uc, UC_ARCH_X86, UC_MODE_32, UC_HOOK_CODE
from unicorn.x86_const import *

R = Path(__file__).resolve().parents[1]
H = R / 'artifacts/th14/ordinary-difficulties-nov14'
A = H / 'marisaa-hard-damage-owner-v2'
report = json.loads((A / 'report.json').read_bytes())
assert report['retired'] and not report['exception']
raw = (A / 'damage-probe.u32').read_bytes()
words = struct.unpack('<%dI' % (len(raw) // 4), raw)
events, at = [], 0
while at < len(words):
    h = words[at:at + 23]
    assert h[0] == 0x44505242 and h[21] == 256
    at += 23
    pool = [words[at + i * 19:at + (i + 1) * 19] for i in range(256)]
    at += 256 * 19
    owner = words[at:at + 64]
    at += 64
    events.append((h, pool, owner))
assert at == len(words)
image, _, _ = importlib.import_module('th-anm-handlers').handlers(14)
assert hashlib.sha256(image.data).hexdigest() == 'f08e885e28d2e0fc8c579e88034dd7de8f2a648d8f08ce781cf08eadc9ffe353'
m = Uc(UC_ARCH_X86, UC_MODE_32)
for _, base, size, source, count in image.sections:
    start = base & ~4095
    m.mem_map(start, ((base + size + 4095) & ~4095) - start)
    m.mem_write(base, image.data[source:source + count])
end, obj, area, target, rect, vm, player, stack = (0x70000000, 0x70001000, 0x70002000,
    0x70003000, 0x70004000, 0x70005000, 0x70010000, 0x700ff000)
m.mem_map(end, 0x100000)
put = lambda p, v: m.mem_write(p, struct.pack('<I', v & 0xffffffff))
get = lambda p: struct.unpack('<I', m.mem_read(p, 4))[0]
side_effects = []

def boundary(machine, address, length, user):
    sp = m.reg_read(UC_X86_REG_ESP)
    pops = {0x47f140: 8, 0x47f0a0: 4, 0x47ed10: 28, 0x4854a0: 0}
    if address == 0x47f140:
        side_effects.append(['interrupt', get(sp + 8)])
    elif address == 0x47f0a0:
        m.reg_write(UC_X86_REG_EAX, vm)
    elif address == 0x47ed10:
        side_effects.append(['effect', get(sp + 8)])
        put(get(sp + 4), 73)
    m.reg_write(UC_X86_REG_EIP, get(sp))
    m.reg_write(UC_X86_REG_ESP, sp + 4 + pops[address])

for address in (0x47f140, 0x47f0a0, 0x47ed10, 0x4854a0):
    m.hook_add(UC_HOOK_CODE, boundary, begin=address, end=address)
results, types = [], {}
for i, (h, pool, owner) in enumerate(events):
    if h[1] != 2:
        continue
    assert owner[0] == 1
    types[owner[1]] = types.get(owner[1], 0) + 1
    if owner[1] != 3:
        continue
    after = events[i + 1]
    assert after[0][1] == 3 and after[0][22] == h[22]
    ah, ap, ao = after
    before_area, after_area = pool[h[22]], ap[h[22]]
    for pointer, size in ((obj, 0x100), (area, 0x100), (vm, 0x600), (player, 0x19000)):
        m.mem_write(pointer, bytes(size))
    m.mem_write(stack - 0x3000, bytes(0x3100))
    side_effects.clear()
    for address, value in [(0x4db67c, player), (0x4d8f58, 0x3f800000),
                           (obj + 0x14, 71), (obj + 0xc0, area),
                           (obj + 0x70, owner[6]), (obj + 0xb0, owner[12]),
                           (obj + 0xa4, owner[10]), (obj + 0xa8, owner[11]),
                           (obj + 0x18, owner[7]), (obj + 0x1c, owner[8]), (obj + 0x20, owner[9]),
                           (area + 0x24, before_area[4]), (area + 0x28, before_area[5]),
                           (area + 0x84, before_area[12]), (player + 0x184b4, owner[16])]:
        put(address, value)
    for j, value in enumerate(owner[3:6]):
        put(obj + 0x54 + j * 4, value)
    for j, value in enumerate(h[14:17]):
        put(target + j * 4, value)
    for j, value in enumerate(h[17:19]):
        put(rect + j * 4, value)
    put(stack, end)
    put(stack + 4, rect if h[5] else 0)
    put(stack + 8, h[20])
    put(stack + 12, h[19])
    put(stack - 36, owner[19])
    m.reg_write(UC_X86_REG_ESP, stack)
    m.reg_write(UC_X86_REG_ECX, obj)
    m.reg_write(UC_X86_REG_EDX, target)
    m.reg_write(UC_X86_REG_MXCSR, 0x1f80)
    m.reg_write(UC_X86_REG_FPCW, 0x37f)
    m.reg_write(UC_X86_REG_FPSW, 0)
    m.reg_write(UC_X86_REG_FPTAG, 0xffff)
    m.emu_start(0x452700, end, count=1000000)
    assert m.reg_read(UC_X86_REG_EIP) == end
    actual = [get(obj + 0xb0), get(area + 0x24), get(obj + 0xa4), get(obj + 0xa8),
              get(player + 0x184b4), m.reg_read(UC_X86_REG_EAX)]
    expected = [ao[12], after_area[4], ao[10], ao[11], ao[16], ah[12]]
    results.append(dict(stage=h[3], controlFrame=h[4], areaSlot=h[22], shotSlot=owner[32],
        passed=actual == expected, native=actual, port=expected,
        hasRectangle=bool(h[5]), declaredScratch=owner[19], events=side_effects[:]))
assert results
proof = dict(passed=all(x['passed'] for x in results), cases=len(results),
    capturedCallbackTypes=types, actualOriginalBeamBody=True, instructionBytesPatched=0,
    anmAndCookieServicesDeclaredExternal=True, originalCallerScratchHistoryValidated=False,
    actualVisualEffectsValidated=False, nativeValuesFedBackToPort=False,
    captureSha256=hashlib.sha256(raw).hexdigest(), results=results, completeGame=False)
(H / 'live-beam-hit-oracle.json').write_text(json.dumps(proof, indent=2) + '\n')
print(json.dumps(proof))
