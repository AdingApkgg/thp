"""Bounded, unmodified retail end-menu state dispatch and timer evidence.

No Native process, draw, capture delivery, score consumer or whole-game timing
is executed. Relative-call inventories are static byte scans of original .text.
"""
import hashlib
import importlib.util
import json
import struct
from pathlib import Path

from capstone import Cs, CS_ARCH_X86, CS_MODE_32
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import UC_X86_REG_EBX, UC_X86_REG_ECX, UC_X86_REG_EIP, UC_X86_REG_ESI, UC_X86_REG_ESP

ROOT = Path(__file__).resolve().parents[1]
HELPER = ROOT / 'tools/th14-loading-lifecycle-evidence-check.py'
OUTPUT = ROOT / 'docs/porting/th14-end-menu-state-verified-oct14.json'
MENU, CONTROL, STACK = 0x600100, 0x601000, 0x7ff000


def binding(path):
    data = path.read_bytes()
    return dict(path=path.relative_to(ROOT).as_posix(), bytes=len(data), sha256=hashlib.sha256(data).hexdigest())


def main():
    spec = importlib.util.spec_from_file_location('original_loading_image', HELPER)
    helper = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(helper)
    image = helper.Image()  # This verifies the retail executable's SHA-256.
    md = Cs(CS_ARCH_X86, CS_MODE_32)
    def unit(address, count):
        data = image.bytes(address, count)
        return dict(address=hex(address), bytes=count, hex=data.hex(), sha256=hashlib.sha256(data).hexdigest(),
                    instructions=[dict(address=hex(i.address), mnemonic=i.mnemonic, operands=i.op_str)
                                  for i in md.disasm(data, address)])
    def machine():
        u = image.machine()
        u.mem_write(MENU, bytes(0x600))
        u.mem_write(CONTROL, bytes(0x600))
        u.reg_write(UC_X86_REG_ESP, STACK)
        return u
    def put(u, address, value):
        u.mem_write(address, struct.pack('<I', value & 0xffffffff))
    def get(u, address):
        return struct.unpack('<I', u.mem_read(address, 4))[0]
    def run(u, start, stops):
        reached = []
        def stop(guest, address, size, unused):
            if address in stops:
                reached.append(address)
                guest.emu_stop()
        hook = u.hook_add(UC_HOOK_CODE, stop)
        u.emu_start(start, 0, count=200)
        u.hook_del(hook)
        assert len(reached) == 1 and u.reg_read(UC_X86_REG_EIP) == reached[0]
        return reached[0]

    # The state selector is entered after the real 449f20 replay check. Its
    # original bytes are not changed and it calls no external routine.
    entry_rows = []
    for flags, expected in ((0, 23), (0x10, 31), (0x20, 30), (0x30, 31), (0x110, 31)):
        u = machine()
        put(u, 0x4f58b8, flags)
        u.reg_write(UC_X86_REG_ESI, MENU)
        u.reg_write(UC_X86_REG_ECX, CONTROL)
        assert run(u, 0x449f5d, {0x449f91}) == 0x449f91
        assert get(u, MENU + 4) == expected
        assert get(u, CONTROL + 0x80) == (0x10 if expected in (23, 30) else 0)
        assert bytes(u.mem_read(0x449f5d, 0x34)) == image.bytes(0x449f5d, 0x34)
        entry_rows.append(dict(flags=hex(flags), maskedRunFlags=hex(flags & 0x30), state=expected,
                               controlFlags=get(u, CONTROL + 0x80)))

    table = list(struct.unpack('<10I', image.bytes(0x44bd54, 40)))
    expected_table = [0x44b11b, 0x44b2d6, 0x44b2d6, 0x44b3bc, 0x44b534,
                      0x44b763, 0x44b9ed, 0x44bcc8, 0x44b16c, 0x44b1b6]
    assert table == expected_table
    dispatch = []
    for state in range(22, 32):
        u = machine()
        put(u, MENU + 4, state)
        u.reg_write(UC_X86_REG_ECX, MENU)
        reached = run(u, 0x44b0f0, set(table))
        assert reached == table[state - 22]
        assert bytes(u.mem_read(0x44b0f0, 43)) == image.bytes(0x44b0f0, 43)
        dispatch.append(dict(state=state, index=state-22, target=hex(reached)))

    timer_rows = []
    for state, target, threshold in ((23, 0x44b2d6, 10), (24, 0x44b2d6, 10),
                                      (30, 0x44b16c, 10), (31, 0x44b1b6, 80)):
        for timer in (-1, 0, 9, 10, 79, 80, 81):
            u = machine()
            put(u, MENU + 4, state)
            put(u, MENU + 0x14, timer)
            u.reg_write(UC_X86_REG_EBX, MENU)
            ready = target + 10
            reached = run(u, target, {0x44bd43, ready})
            assert (reached == ready) == (timer >= threshold)
            assert bytes(u.mem_read(target, 10)) == image.bytes(target, 10)
            timer_rows.append(dict(state=state, timer=timer, threshold=threshold,
                                   ready=timer >= threshold, reached=hex(reached)))

    text = next(s for s in image.sections if s['rva'] == 0x1000)
    raw = image.data[text['raw']:text['raw'] + text['rawSize']]
    base = image.base + text['rva']
    callers = {}
    for target in (0x449f20, 0x449d30, 0x44b0f0):
        calls = [base + at for at in range(len(raw)-4)
                 if raw[at] == 0xe8 and base+at+5+struct.unpack_from('<i', raw, at+1)[0] == target]
        callers[hex(target)] = [hex(a) for a in calls]
    assert callers == {'0x449f20':['0x43708a','0x4371ac'],
                       '0x449d30':['0x43216a','0x44deba'], '0x44b0f0':['0x448362']}

    # Bind the original completion/score/capture calls. These are static units;
    # their consumers are deliberately not executed by this proof.
    assertions = {0x436fa8:0x434c10, 0x436fec:0x448ef0, 0x43708a:0x449f20,
                  0x4371ac:0x449f20, 0x44a02d:0x44c1a0, 0x44a080:0x44be40,
                  0x44b1cd:0x44c1a0, 0x44b220:0x44be40, 0x44b2e0:0x447da0,
                  0x44b176:0x447da0, 0x44b24f:0x447f90, 0x44b2c1:0x44c1a0}
    for address, target in assertions.items():
        data = image.bytes(address, 5)
        assert data[0] == 0xe8 and address+5+struct.unpack_from('<i',data,1)[0] == target
    out = dict(schema='th14-end-menu-state-evidence-v1', diagnosticEvidenceVerified=True,
               completeGame=False, nativeEquivalent=False, executableSha256=helper.EXPECTED_EXE_SHA,
               sourceBindings=[binding(HELPER), binding(Path(__file__)),
                               binding(ROOT/'runtimes/th12/th12_web/cpp/game/PauseEnd.cpp'),
                               binding(ROOT/'runtimes/th12/th12_web/cpp/game/GameSession.cpp'),
                               binding(ROOT/'artifacts/th14/stage-completion-native.json')],
               originalCodeUnmodified=True, controlledStateSelectionCases=entry_rows,
               originalJumpTable=dict(address='0x44bd54', bytesHex=image.bytes(0x44bd54,40).hex(),
                                     sha256=hashlib.sha256(image.bytes(0x44bd54,40)).hexdigest(), rows=dispatch),
               controlledTimerCases=timer_rows, relativeCallByteScan=callers,
               relativeCallByteScanScope='Original .text every-byte e8 scan; not a proof excluding dynamic or indirect calls.',
               originalUnits=[unit(a,n) for a,n in ((0x449f20,0x71),(0x44b0f0,43),(0x436f90,0x10e),
                              (0x43713b,0x7a),(0x44b1b6,0x120),(0x44b2d6,0xe6),(0x44b16c,0x4a),
                              (0x449d6d,23),(0x43215a,0x24),(0x44dea6,0x24))],
               conclusions=dict(
                   normal449f20Entry='flags&0x30==0 selects Native23; dispatch44b2d6 requires10. No80 recapture in this branch.',
                   completedStagePractice='Within the completion436f90 path, non-replay flags0x10 reaches43708a->449f20, selects31, and44b1b6 waits80 before a new text52 and deferred44be40 capture, then compact144 choices.',
                   completedSpellPractice='Within the completion436f90 path, non-replay flags0x20 reaches43708a->449f20, selects30, and44b16c waits10 without the second capture.',
                   ordinaryExtraCompletion='Normal non-replay stage7 reaches4371ac->449f20 and state23; normal stage6 takes ending path rather than this call.',
                   deathEntrypoints='The two static449d30 callers are43216a and44deba, distinct from449f20 completion callers. Therefore global0x10 alone does not establish a death uses the80-frame completion path.',
                   currentPortGap='PauseEnd begin_end(practice=true, cleared=true, spell_practice_id<0) enters portable21/end_menu21 with10-frame handling; the corresponding Native completed StagePractice31 uses80 and second deferred capture. Ordinary and completed SpellPractice should not be changed to80 on this evidence.'),
               scope='43 bounded original selector/dispatch/timer cases with declared memory; static completion/death caller paths and capture callsites only. No complete retail menus, score insertion, deferred postDraw capture, pixels, input flow, all death contexts or whole-game equivalence verified.')
    assert len(entry_rows)+len(dispatch)+len(timer_rows)==43
    OUTPUT.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(dict(output=OUTPUT.relative_to(ROOT).as_posix(), diagnosticEvidenceVerified=True,
                         originalBoundedCases=43, normalThreshold=10, completedStagePracticeThreshold=80,
                         completedSpellPracticeThreshold=10, nativeEquivalent=False),ensure_ascii=False))


if __name__ == '__main__':
    main()
