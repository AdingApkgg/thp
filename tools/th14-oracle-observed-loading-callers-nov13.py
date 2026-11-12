"""Execute retail ASCII16 for the RNG inputs observed in the ordinary C++ run.

This tests actual VM instruction/RNG call sequences, not wall-clock scheduling.
Sprite selection and the security cookie are explicit component boundaries.
"""
from pathlib import Path
import hashlib
import importlib
import json
import struct
import sys
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import UC_X86_REG_EBX, UC_X86_REG_ECX, UC_X86_REG_ESP

R = Path(__file__).resolve().parents[1]
H = R / 'artifacts/th14/helper-clear-oracle-nov13'
O = H / 'observed-loading-callers-oracle'
O.mkdir(exist_ok=False)
sys.path.insert(0, str(R / 'tools'))
ui = importlib.import_module('th14-ui-oracle')
vm_oracle = importlib.import_module('th14-anm-vm-oracle')
scripts = importlib.import_module('th-anm-script-dump')
image = importlib.import_module('th12-pe').Image('H:/Games/th/14/th14.exe')
sha = lambda data: hashlib.sha256(data).hexdigest()
assert sha(image.data) == 'f08e885e28d2e0fc8c579e88034dd7de8f2a648d8f08ce781cf08eadc9ffe353'
trace_path = H / 'application/start-mode3/loading-rng-callers.json'
trace = json.loads(trace_path.read_bytes())
assert trace['stride'] == 24 and not trace['nativePaired']
rows = [dict(zip(trace['fields'], trace['words'][i:i + 24])) for i in range(0, len(trace['words']), 24)]
assert len(rows) == trace['count'] == 1560
assert all(row['file'] == 2 and row['script'] == 16 and row['handle'] == 0 for row in rows)
assert all(row['point'] == index % 2 * 4 for index, row in enumerate(rows))
archive = json.loads((R / 'artifacts/archive-differential/th14.json').read_bytes())
ascii_path = Path(archive['extraction']) / 'ascii.anm'
ascii_bytes = ascii_path.read_bytes()
assert sha(ascii_bytes) == 'fc1c2295fda07140b475b2ddd45d221920534e4a011c529e76578609d69a9284'
code = next(body for index, _, body in scripts.scripts(ascii_bytes) if index == 16)
expected_offsets = [84, 120, 156, 192, 276, 328, 348, 368, 408, 408, 408, 460]
assert len(code) == 596
assert len(rows) % 24 == 0
retail = ui.Retail(image)
retail.stub(0x46f1e0, 8)  # Sprite selection is supplied, not part of the RNG claim.
m, VM, CODE, RATE, f = retail.machine, ui.VM, ui.DATA, vm_oracle.RATE, ui.float_word
observed = []
pending = []

def hook(machine, pc, _size, _user):
    if pc == 0x403310 and machine.reg_read(UC_X86_REG_ECX) == 0x4db508:
        sp = machine.reg_read(UC_X86_REG_ESP)
        offset = machine.reg_read(UC_X86_REG_EBX) - CODE
        observed.append({'point': 0, 'instructionOffset': offset,
                         'seed': retail.words(0x4db508, 1)[0] & 0xffff,
                         'calls': retail.words(0x4db50c, 1)[0]})
        pending.append((retail.words(sp, 1)[0], sp + 4, offset))
    elif pending and pc == pending[-1][0] and machine.reg_read(UC_X86_REG_ESP) == pending[-1][1]:
        _, _, offset = pending.pop()
        observed.append({'point': 4, 'instructionOffset': offset,
                         'seed': retail.words(0x4db508, 1)[0] & 0xffff,
                         'calls': retail.words(0x4db50c, 1)[0]})

m.hook_add(UC_HOOK_CODE, hook)
cases = []
exception = None
try:
    for start in range(0, len(rows), 24):
        expected = rows[start:start + 24]
        assert [row['instructionOffset'] for row in expected[::2]] == expected_offsets
        seed, calls = expected[0]['seed'], expected[0]['calls']
        # Same defaults as the separately qualified ANM component. The real
        # script executes all its time -1 prelude and time 0 RNG instructions.
        m.mem_write(VM, bytes(0x5cc))
        m.mem_write(CODE, code)
        retail.put(RATE, f(1))
        retail.put(VM + 0x18, 3, 0)
        retail.put(VM + 0x28, CODE)
        retail.put(VM + 0x38, CODE, f(120), f(140), 0)
        retail.put(VM + 0x60, f(1), f(1), f(1), f(1), 0, 0, f(1), f(1), f(16), f(24), 0, 0)
        retail.put(VM + 0x4e0, f(1), f(3.141592653589793), 65536)
        retail.put(VM + 0x534, 0xffffffff, 0x88334455)
        retail.put(VM + 0x548, 0xffffffff, 0, 0, RATE, 1, 0xffffffff, 0, 0, RATE, 1)
        retail.put(0x4f7a6c, f(1))
        retail.put(0x4f7a80, 320, 16, 320, 16)
        m.mem_write(0x4db508, struct.pack('<HHIHHI', seed, 0, calls, expected[0]['visualSeed'], 0, expected[0]['visualCalls']))
        observed.clear()
        pending.clear()
        retail.run(0x46fe50)
        assert not pending
        expected_words = [{key: row[key] for key in ['point', 'instructionOffset', 'seed', 'calls']} for row in expected]
        differences = [{'index': index, 'native': a, 'cpp': b} for index, (a, b) in enumerate(zip(observed, expected_words)) if a != b]
        cases.append({'particleOrdinal': start // 24, 'initialSeed': seed, 'initialCalls': calls,
                      'nativeEvents': list(observed), 'expectedEvents': expected_words,
                      'differentEvents': differences, 'sameEventCount': len(observed) == len(expected_words)})
except Exception as error:
    exception = repr(error)
passed = exception is None and len(cases) == 65 and all(row['sameEventCount'] and not row['differentEvents'] for row in cases)
report = {'passed': passed, 'cases': cases, 'exception': exception, 'particleInitialUpdates': len(cases),
          'retailVmUpdateEntry': '0x46fe50', 'rngEntry': '0x403310',
          'originalScriptBytesUnchanged': True, 'sourceTraceSha256': sha(trace_path.read_bytes()),
          'asciiSha256': sha(ascii_bytes), 'script16Sha256': sha(code), 'executableSha256': sha(image.data),
          'toolSha256': sha(Path(__file__).read_bytes()), 'suppliedServices': ['security cookie', 'sprite selection'],
          'initialSeedAndCountFromObservedCppCallBoundary': True, 'referenceValuesFedToRunningCpp': False,
          'actualNativeFactoryOrPhysicalScheduleCompared': False, 'vmGeometryCompared': False,
          'ordinaryGameNativePairAccepted': False, 'completeGame': False}
(O / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps({key: value for key, value in report.items() if key != 'cases'}))
if not passed:
    print(json.dumps(cases[:1]))
    sys.exit(1)
