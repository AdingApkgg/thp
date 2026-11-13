"""Run original 451430 on actual port call inputs.

Area-hit callbacks are declared external boundaries: their observed return and
field mutations are supplied. The original collector/geometry/score instructions
execute without patches. This does not validate the callback implementations.
"""
from pathlib import Path
import hashlib, importlib, json, struct
from unicorn import Uc, UC_ARCH_X86, UC_MODE_32, UC_HOOK_CODE
from unicorn.x86_const import *

R = Path(__file__).resolve().parents[1]
H = R / 'artifacts/th14/ordinary-difficulties-nov14'
A = H / 'marisaa-hard-damage-window-v1'
report = json.loads((A / 'report.json').read_bytes())
assert report['retired'] and not report['exception'] and report['outcome'] == 'natural-game-over'
raw = (A / 'damage-probe.u32').read_bytes()
words = struct.unpack('<%dI' % (len(raw) // 4), raw)
events, at = [], 0
while at < len(words):
    header = words[at:at + 23]
    assert header[0] == 0x44505242 and header[21] == 256
    at += 23
    pool = [words[at + i * 19:at + (i + 1) * 19] for i in range(256)]
    at += 256 * 19
    events.append((header, pool))
assert at == len(words)
groups, current = [], None
for event in events:
    phase = event[0][1]
    if phase == 0:
        assert current is None
        current = [event]
    else:
        assert current is not None
        current.append(event)
        if phase == 1:
            groups.append(current)
            current = None
assert current is None
image, _, _ = importlib.import_module('th-anm-handlers').handlers(14)
assert hashlib.sha256(image.data).hexdigest() == 'f08e885e28d2e0fc8c579e88034dd7de8f2a648d8f08ce781cf08eadc9ffe353'
m = Uc(UC_ARCH_X86, UC_MODE_32)
for _, base, size, source, count in image.sections:
    start = base & ~4095
    m.mem_map(start, ((base + size + 4095) & ~4095) - start)
    m.mem_write(base, image.data[source:source + count])
end, player, manager, resource = 0x70000000, 0x70001000, 0x70030000, 0x70031000
p, sizeptr, bomb, last, cb, stack = 0x70032000, 0x70032020, 0x70032040, 0x70032060, 0x70033000, 0x700ff000
m.mem_map(end, 0x200000)
put = lambda address, value: m.mem_write(address, struct.pack('<I', value & 0xffffffff))
get = lambda address: struct.unpack('<I', m.mem_read(address, 4))[0]
offsets = (0x10, 0x14, 0x1c, 0x24, 0x28, 0x2c, 0x30, 0x34,
           0x70, 0x74, 0x78, 0x84, 0x88, 0x8c, 0x90, 0x94, 0xa0, 0x9c)
active_callbacks, actual_calls, callback_errors = [], [], []

def write_field(slot, field, value):
    if field == 17 and value:
        value = cb
    put(player + 0xde18 + slot * 0xa4 + offsets[field - 1], value)

def callback(machine, address, length, user):
    slot = (m.reg_read(UC_X86_REG_ECX) - player - 0xde18) // 0xa4
    actual_calls.append(slot)
    index = len(actual_calls) - 1
    if index >= len(active_callbacks) or active_callbacks[index][0][0][22] != slot:
        callback_errors.append(dict(index=index, unexpectedSlot=slot))
        m.reg_write(UC_X86_REG_EAX, 0)
        return
    before, after = active_callbacks[index]
    for area in range(256):
        for field in range(1, 19):
            if before[1][area][field] != after[1][area][field]:
                write_field(area, field, after[1][area][field])
    delta = after[0][11] - before[0][11]
    put(0x4f5830, get(0x4f5830) + delta)
    m.reg_write(UC_X86_REG_EAX, after[0][12])

m.mem_write(cb, b'\xc2\x0c\x00')
m.hook_add(UC_HOOK_CODE, callback, begin=cb, end=cb)
results = []
for index, group in enumerate(groups):
    before, after = group[0], group[-1]
    h, pool = before
    active_callbacks = []
    for i in range(1, len(group) - 1, 2):
        assert group[i][0][1] == 2 and group[i + 1][0][1] == 3
        assert group[i][0][22] == group[i + 1][0][22]
        active_callbacks.append((group[i], group[i + 1]))
    actual_calls, callback_errors = [], []
    m.mem_write(player, bytes(0x19000))
    m.mem_write(manager, bytes(0x100))
    m.mem_write(stack - 0x3000, bytes(0x3100))
    for address, value in [(0x4db67c, player), (0x4db52c, manager), (player + 0x688, resource),
                           (player + 0x68c, 0), (player + 0x690, int(bool(h[6]))),
                           (resource + 0x28, h[10]), (0x4f5830, h[11]), (bomb, 77)]:
        put(address, value)
    for i, value in enumerate(h[14:17]):
        put(p + i * 4, value)
    for i, value in enumerate(h[17:19]):
        put(sizeptr + i * 4, value)
    for slot, area in enumerate(pool):
        assert area[0] == slot
        for field in range(1, 19):
            write_field(slot, field, area[field])
    args = [p, sizeptr if h[5] else 0, h[19], bomb, last, h[7], h[8], h[9]]
    put(stack, end)
    for i, value in enumerate(args):
        put(stack + 4 + i * 4, value)
    m.reg_write(UC_X86_REG_ESP, stack)
    m.reg_write(UC_X86_REG_XMM3, h[20])
    m.reg_write(UC_X86_REG_FPCW, 0x37f)
    m.reg_write(UC_X86_REG_FPSW, 0)
    m.reg_write(UC_X86_REG_FPTAG, 0xffff)
    m.reg_write(UC_X86_REG_MXCSR, 0x1f80)
    m.emu_start(0x451430, end, count=2000000)
    assert m.reg_read(UC_X86_REG_EIP) == end
    output = [m.reg_read(UC_X86_REG_EAX), get(bomb), get(0x4f5830)]
    expected = [after[0][12], after[0][13], after[0][11]]
    pool_differences = []
    for slot, area in enumerate(after[1]):
        for field in range(1, 19):
            actual = get(player + 0xde18 + slot * 0xa4 + offsets[field - 1])
            target = cb if field == 17 and area[field] else area[field]
            if actual != target:
                pool_differences.append(dict(slot=slot, field=field, native=actual, port=target))
    expected_calls = [x[0][0][22] for x in active_callbacks]
    passed = output == expected and actual_calls == expected_calls and not callback_errors and not pool_differences
    results.append(dict(index=index, stage=h[3], controlFrame=h[4], probe=bool(h[7]),
        passed=passed, native=output, port=expected, nativeCalls=actual_calls,
        portCalls=expected_calls, callbackErrors=callback_errors, poolDifferences=pool_differences))
proof = dict(passed=all(r['passed'] for r in results), cases=len(results),
    originalCollectorGeometryAndScoreInstructions=True, instructionBytesPatched=0,
    callbackResultsAndMutationsDeclaredExternal=True, actualHitCallbacksValidated=False,
    bombManagerBoundary='inactive zeroed manager; direct Bomb damage not validated',
    originalLastHitPositionCompared=False,
    originalWholeGameTimelineAccepted=False, runtimeNativeValuesFedBack=False,
    capturedBytes=len(raw), captureSha256=hashlib.sha256(raw).hexdigest(),
    nativeExecutableSha256=hashlib.sha256(image.data).hexdigest(),
    results=results, completeGame=False)
(H / 'live-damage-oracle.json').write_text(json.dumps(proof, indent=2) + '\n')
print(json.dumps(proof))
