"""Give title 12 the last link of the device chain: the fixture and the checker.

Title 12 has the handler table, the boundary, the call convention and, since section 348, an oracle
corpus of 4400 cases. The five siblings (13, 14, 16, 17, 18) all have the same last link: a
fixture that runs the port with PORT_TITLE set, and a checker that derives the port-to-native map
from the corpus and fails when a slot has no candidate. This scaffold copies the TH17 pair - the most
recent shape, with the arrangement census already inside - and rewrites only the title literals and
the two ABI constants title 12 differs in: the position slot (+0x3f0, not +0x28) and the address
the native probe puts the script at. It is idempotent and refuses to run without --force if the
targets exist.

Usage: py -3 tools/th12-anm-check-scaffold.py [--force]
"""
import argparse, hashlib, io, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RT = ROOT / 'runtimes/th12/th12_web'
CHECKER = ROOT / 'tools/th12-anm-check.mjs'
FIXTURE = RT / 'tests/cpp/th12-anm-fixture.cpp'
SRC_CHECKER = ROOT / 'tools/th17-anm-check.mjs'
SRC_FIXTURE = RT / 'tests/cpp/th17-anm-fixture.cpp'

CHECKER_EDITS = [
    ('artifacts/th17/anm-check', 'artifacts/th12/anm-check'),
    ('artifacts/th17/anm-native.json', 'artifacts/th12/anm-native.json'),
    ("execFileSync('py', ['-3', resolve(root, 'tools/th-anm-native-newer.py'), '--title=17'],",
     "execFileSync('py', ['-3', resolve(root, 'tools/th12-anm-native.py')],"),
    ("const fixture = 'tests/cpp/th17-anm-fixture.cpp';",
     "const fixture = 'tests/cpp/th12-anm-fixture.cpp';"),
    ("'-DPORT_TITLE=17'", "'-DPORT_TITLE=12'"),
    ("resolve(out, 'th17.wasm')", "resolve(out, 'th12.wasm')"),
    ('const PORT_TITLE_NUMBER = 17;', 'const PORT_TITLE_NUMBER = 12;'),
    ("const CODE_BASE = 0x70002000;  // the native probe puts the script at this address",
     "// Title 12's own ABI, and the generator records the address its probe put the script at.\n"
     "const CODE_BASE = Number(proof.measured.codeBase ?? '0x70110000');\n"
     "const POSITION_SLOT = Number(proof.measured.positionSlot ?? '0x28');"),
    ('native.readUInt32LE(0x28)', 'native.readUInt32LE(POSITION_SLOT)'),
    ('if (slot === 0x28) {', 'if (slot === POSITION_SLOT) {'),
    ("const ARRANGEMENT_SLOTS = {16: [0x530, 0x534], 17: [0x530, 0x534], 18: [0x534, 0x538]}[PORT_TITLE_NUMBER];",
     "const ARRANGEMENT_SLOTS = {\n"
     "  12: [0x47c, 0x3fc],  // the two hottest non-position words of the th12 corpus\n"
     "  16: [0x530, 0x534], 17: [0x530, 0x534], 18: [0x534, 0x538]}[PORT_TITLE_NUMBER];"),
    ("'tools/th-anm-native-newer.py', 'tools/th17-anm-check.mjs'",
     "'tools/th12-anm-native.py', 'tools/th12-anm-check.mjs'"),
    ('// The oracle (tools/th-anm-native-newer.py) records the whole 0x700-byte context of the original at the next',
     '// The oracle (tools/th12-anm-native.py) records the whole 0x700-byte context of the original at the next'),
    ('// dispatch boundary, because the field layout there is TH17\x27s own: it writes its flag word at +0x530',
     "// dispatch boundary, because the field layout there is TH12's own: its ABI keeps the script\n"
     "// pointer at +0x3f0"),
]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--force', action='store_true')
    args = parser.parse_args()
    for target in (CHECKER, FIXTURE):
        if target.exists() and not args.force:
            print('  %s exists; pass --force to rewrite' % target.relative_to(ROOT))
            return
    text = io.open(SRC_CHECKER, encoding='utf-8').read()
    missed = []
    for old, new in CHECKER_EDITS:
        if old not in text:
            missed.append(old[:56])
            continue
        text = text.replace(old, new)
    text = text.replace('TH17', 'TH12')
    CHECKER.write_text(text, encoding='utf-8', newline='')
    fixture = io.open(SRC_FIXTURE, encoding='utf-8').read().replace('TH17', 'TH12').replace(
        'th17', 'th12')
    FIXTURE.write_text(fixture, encoding='utf-8', newline='')
    print('  %-42s %7d bytes' % (CHECKER.relative_to(ROOT), CHECKER.stat().st_size))
    print('  %-42s %7d bytes' % (FIXTURE.relative_to(ROOT), FIXTURE.stat().st_size))
    for line in missed:
        print('  MISSED: %s' % line)
    print('  the title literals left in the checker: %d occurrences of 17 in paths' %
          sum(1 for line in io.open(CHECKER, encoding='utf-8') if 'th17' in line))
    for i, line in enumerate(io.open(CHECKER, encoding='utf-8'), 1):
        if 'th17' in line or 'TH17' in line:
            print('    %d: %s' % (i, line.strip()[:96]))
    print('  sha256 checker %s' % hashlib.sha256(CHECKER.read_bytes()).hexdigest()[:32])
    print('  sha256 fixture %s' % hashlib.sha256(FIXTURE.read_bytes()).hexdigest()[:32])


main()
