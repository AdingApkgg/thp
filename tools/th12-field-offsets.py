#!/usr/bin/env python3
"""Machine-derived map of TH12 EnemyState field offsets.

Every ECL case body reaches the enemy state through EBX, so the offsets the bodies actually touch are
evidence, not guesses. This tool disassembles each case body recorded in docs/th12/ecl-case-bodies.json,
histograms the EBX-relative displacements, and compares them with the offsets the port declares in its own
static_asserts. It exists because widening the oracle's byte comparison past the movement region needs to
know which offsets agree: the answer here is that past the movement region they do not, so the comparison
cannot simply be extended.

Two premises are enforced rather than assumed, because round 40 found both could quietly fail:

  - a body ends where the next body starts, so an access is never attributed to a body it does not belong
    to. A scratch probe that used a fixed window attributed a shared tail to dozens of opcodes at once;
  - EBX still holds the enemy state. A body may reload it with another object, which is what 0x1c6 does:
    its whole body is a call into the effect pool, and FUN_004615a0 writes a position at +0x430 on a pool
    instance. Every access after a write to EBX is excluded and counted, so the histogram cannot report
    another object's fields as enemy state.

Usage: py -3 tools/th12-field-offsets.py [--check]
"""
import collections, hashlib, json, sys
from pathlib import Path
from capstone import Cs, CS_ARCH_X86, CS_MODE_32, CS_AC_WRITE
from capstone.x86 import X86_OP_MEM, X86_OP_REG, X86_REG_EBX

ROOT = Path(__file__).resolve().parents[1]
EXE = Path(r'H:\Games\th\12\th12.exe')
OUT = ROOT / 'docs' / 'th12' / 'state-offsets.json'
LOW, HIGH = 0x0, 0x1800
# offsets the port asserts for itself, from runtimes/th12/th12_web/cpp/game/EnemyState.hpp
PORT_OFFSETS = {
    0x124: 'integers', 0x154: 'lifetime', 0x174: 'absolute_position', 0x20c: 'absolute_angle',
    0x374: 'emitters', 0x1414: 'emitter_offset', 0x1474: 'emitter_origin', 0x14d4: 'visual_size',
    0x14f0: 'health', 0x159c: 'flags', 0x1630: 'script_owner',
}
# the four Movements sit here in both layouts, which the 0x12c body confirms by naming 0x34, 0x68 and 0x9c
SHARED_REGION = {'start': 0x0, 'end': 0xd0,
                 'why': 'previous/current/absolute/relative at 0x0/0x34/0x68/0x9c in both layouts'}


def main():
    raw = EXE.read_bytes()
    md = Cs(CS_ARCH_X86, CS_MODE_32)
    md.detail = True
    doc = json.loads((ROOT / 'docs' / 'th12' / 'ecl-case-bodies.json').read_text())
    starts = sorted(int(k, 16) for k in doc['bodies'])
    hist = collections.Counter()
    reloaded = 0
    excluded = 0
    for i, va in enumerate(starts):
        end = starts[i + 1] if i + 1 < len(starts) else va + 0x400
        end = min(end, va + 0x600)
        base = 0x400 + (va - 0x401000)
        ebx_written = False
        saw_reload = False
        for ins in md.disasm(raw[base:base + (end - va)], va):
            if ebx_written:
                saw_reload = True
            for op in ins.operands:
                if op.type == X86_OP_MEM and op.mem.base == X86_REG_EBX and op.mem.index == 0:
                    if LOW <= op.mem.disp <= HIGH:
                        if ebx_written:
                            excluded += 1
                        else:
                            hist[op.mem.disp] += 1
            # A write to EBX makes every later [EBX+disp] somebody else's field, so the access is dropped
            # rather than counted. regs_access() reports only implicit registers, so the explicit operand
            # is what has to be inspected.
            for op in ins.operands:
                if op.type == X86_OP_REG and op.reg == X86_REG_EBX and (op.access & CS_AC_WRITE):
                    ebx_written = True
        if saw_reload:
            reloaded += 1
    result = {
        'game': 'th12',
        'source': str(EXE),
        'exeSha256': hashlib.sha256(raw).hexdigest(),
        'bodiesScanned': len(starts),
        'bodiesWithEbxReload': reloaded,
        'accessesExcludedAfterEbxReload': excluded,
        'totalEbxAccesses': sum(hist.values()),
        'distinctOffsets': len(hist),
        'sharedRegion': SHARED_REGION,
        'offsets': {('0x%04x' % d): c for d, c in sorted(hist.items())},
        'portOffsets': {'0x%04x' % d: n for d, n in sorted(PORT_OFFSETS.items())},
        'portOffsetsNeverTouchedByABody': [('0x%04x' % d) for d in sorted(PORT_OFFSETS) if not hist.get(d)],
        'topOffsets': [{'offset': '0x%04x' % d, 'count': c} for d, c in hist.most_common(32)],
    }
    text = json.dumps(result, indent=1) + '\n'
    if '--check' in sys.argv:
        if OUT.exists() and OUT.read_text() == text:
            print('state-offsets.json is current (%d offsets, %d bodies)'
                  % (result['distinctOffsets'], result['bodiesScanned']))
            return 0
        print('FAIL: docs/th12/state-offsets.json differs from a fresh scan')
        return 1
    OUT.write_text(text)
    print('bodies scanned: %d, ebx accesses: %d, distinct offsets: %d'
          % (result['bodiesScanned'], result['totalEbxAccesses'], result['distinctOffsets']))
    print('port offsets never touched: %s' % ', '.join(result['portOffsetsNeverTouchedByABody']))
    print('wrote %s' % OUT)
    return 0


if __name__ == '__main__':
    sys.exit(main())