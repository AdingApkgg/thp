"""Check retail TH14 high-score selection and the saved practice replay mode.

Executes unchanged x86 blocks with declared virtual score records. This checks
selection, not native filesystem loading, complete playback or GPU rendering.
"""
from pathlib import Path
import argparse
import hashlib
import importlib
import json
import struct
import sys

ROOT = Path(__file__).resolve().parents[1]
SHA = lambda data: hashlib.sha256(data).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--decoded', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    out = args.output.resolve()
    assert out.is_relative_to(ROOT / 'artifacts/th14') and not out.exists()
    sys.path[:0] = [str(ROOT / 'tools/tmp/th14-analysis-python'), str(ROOT / 'tools')]
    from unicorn import Uc, UC_ARCH_X86, UC_MODE_32
    from unicorn.x86_const import UC_X86_REG_ESP, UC_X86_REG_EBX, UC_X86_REG_EIP
    image = importlib.import_module('th-anm-handlers').handlers(14)[0]
    assert SHA(image.data) == 'f08e885e28d2e0fc8c579e88034dd7de8f2a648d8f08ce781cf08eadc9ffe353'
    decoded = args.decoded.read_bytes()
    assert len(decoded) >= 0x170 and struct.unpack_from('<I', decoded, 0x78)[0] == 1
    header = decoded[0x94:0x170]
    stage, seed, frames, payload = struct.unpack_from('<HHII', header)
    assert len(decoded) == 0x170 + payload and frames * 6 <= payload
    m = Uc(UC_ARCH_X86, UC_MODE_32)
    for _, address, size, offset, length in image.sections:
        first = address & ~4095
        m.mem_map(first, ((address + size + 4095) & ~4095) - first)
        m.mem_write(address, image.data[offset:offset + length])
    base = 0x70000000
    m.mem_map(base, 0x80000)
    manager, sheet, control, replay_header = [base + n for n in (0x100, 0x1000, 0x3000, 0x4000)]
    score, stack = base + 0x10000, base + 0x7f000

    def put(address, value):
        m.mem_write(address, struct.pack('<I', value & 0xffffffff))

    def get(address):
        return struct.unpack('<I', m.mem_read(address, 4))[0]

    def run(start, stop):
        m.reg_write(UC_X86_REG_ESP, stack)
        m.emu_start(start, stop, count=2000)
        assert m.reg_read(UC_X86_REG_EIP) == stop

    constructor = []
    for initial_flags in (0, 0x10, 0x20):
        m.mem_write(manager, bytes(0x400))
        put(manager + 0x10, 1)
        put(manager + 0x1c, replay_header)
        put(0x4db688, manager)
        put(0x4db558, control)
        put(0x4f58a4, stage)
        put(0x4f58b8, initial_flags)
        m.mem_write(replay_header, decoded[:0x94])
        m.mem_write(sheet, header)
        m.mem_write(control, bytes(0x100))
        record = manager + (stage * 5 + 0x19) * 8
        put(record + 0x10, sheet)
        m.reg_write(UC_X86_REG_EBX, manager)
        run(0x4549cf, 0x454a6c)
        expected_flags = 0x20 if struct.unpack_from('<i', header, 0x30)[0] >= 0 else 0
        assert get(0x4f58b8) == expected_flags
        constructor.append(dict(initialFlags=initial_flags, replayFlags=get(0x4f58b8)))
    replay_flags = constructor[0]['replayFlags']
    cases = []
    stage_modes = [(d, s) for d in range(4) for s in range(1, 7)] + [(4, 7)]
    for selection in range(6):
        for difficulty, stage_number in stage_modes:
            char, subtype = divmod(selection, 2)
            record = score + selection * 0x5298
            ranking = record + difficulty * 0x118 + 0x18
            practice = record + 0x7f8 + (stage_number + difficulty * 8) * 8
            spell = record + 0xa18 + 3 * 0x9c
            rank_value = 100000 + selection * 100 + difficulty
            practice_value = 52 + selection * 100 + stage_number
            spell_value = 700 + selection * 100
            put(ranking, rank_value)
            m.mem_write(ranking + 5, b'\x02')
            put(practice, practice_value)
            put(spell, spell_value)
            for mode, flags, value, continues in (
                ('ordinary', 0, rank_value, 2),
                ('live-practice', 0x10, practice_value, 0),
                ('practice-replay', replay_flags, rank_value, 2),
                ('spell-practice', 0x20, spell_value, 0),
            ):
                put(0x4db68c, score)
                put(0x4f5828, char)
                put(0x4f582c, subtype)
                put(0x4f5834, difficulty)
                put(0x4f5844, 3)
                put(0x4f58a4, stage_number)
                put(0x4f58b8, flags)
                put(0x4f5898, 0xdeadbeef)
                put(0x4f589c, 0xdeadbeef)
                run(0x435bb1, 0x435c7b)
                actual = [get(0x4f5898), get(0x4f589c)]
                assert actual == [value, continues], (selection, difficulty, stage_number, mode, actual)
                cases.append(dict(selection=selection, difficulty=difficulty, stage=stage_number,
                                  mode=mode, scoreUnits=actual[0], continues=actual[1]))
    report = dict(schema='th14/practice-high-score-native/1', passed=True,
                  caseCount=len(cases), constructorCases=constructor, cases=cases,
                  decodedSha256=SHA(decoded), executableSha256=SHA(image.data),
                  toolSha256=SHA(Path(__file__).read_bytes()),
                  instructionSlices=[dict(address=a, bytes=n, sha256=SHA(image.read(a, n)))
                                     for a, n in ((0x4549cf, 0x9d), (0x435bb1, 0xca))],
                  practiceReplayUsesOrdinaryRanking=replay_flags == 0,
                  declaredVirtualScores=True, originalInstructionsModified=False,
                  originalProcessLaunched=False, completeGame=False)
    out.mkdir(parents=True)
    (out / 'native.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({k: v for k, v in report.items() if k not in ('cases', 'instructionSlices')}))


if __name__ == '__main__':
    main()
