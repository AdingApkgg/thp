"""Audit the port's high opcode handlers against the original's real dispatch.

The authority is `tools/th12-opcode-handlers.py`: the dispatcher FUN_004154d0 reads

    handler(opcode) = u32[0x419654 + byte[0x419890 + (opcode - 0x100)] * 4]

for opcodes 0x100..0x263, and 193 of those 356 opcodes share one target, 0x41962b,
whose bytes are `xor eax,eax` followed by the stack-cookie load -- the epilogue.  Those
opcodes are NO-OPS in this dispatcher: they return immediately.

This audit classifies every `case 0xNNN:` in the port's high-opcode handler file against
that table, so a handler the original never runs cannot hide behind "it looks plausible".

    py -3 tools/th12-opcode-audit.py --audit            report, exit 0
    py -3 tools/th12-opcode-audit.py --strict           exit 1 if any port case is a no-op
                                                        in the original

A port case that the original treats as a no-op is a divergence: the original has no
behaviour to reconstruct there.  It is not automatically wrong to implement something --
a later title may legitimately differ -- but it must be declared, not assumed.
"""

import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from importlib import import_module

Image = import_module("th12-pe").Image

ROOT = Path(__file__).resolve().parent.parent
GROUP_TABLE = 0x419890
TARGET_TABLE = 0x419654
FIRST_OPCODE = 0x100
GUARD_COUNT = 0x164                      # 356
NOOP_TARGET = 0x41962B                   # the epilogue: xor eax,eax + stack cookie
PORT_FILE = ROOT / "runtimes/th12/th12_web/cpp/game/EnemyStateCommands.cpp"

CASE_RE = re.compile(r"case\s+(0x[0-9a-fA-F]+)\s*:")


def original_map(img):
    targets = []
    for i in range(GUARD_COUNT):
        t = img.u32(TARGET_TABLE + i * 4)
        if not img.is_code(t):
            break
        targets.append(t)
    out = {}
    for i in range(GUARD_COUNT):
        op = FIRST_OPCODE + i
        g = img.data[img.offset_of(GROUP_TABLE + i)]
        out[op] = targets[g] if g < len(targets) else None
    return out, targets


def port_cases(path):
    text = path.read_text(encoding="utf-8", errors="replace")
    return sorted({int(m, 16) for m in CASE_RE.findall(text)})


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--audit", action="store_true")
    ap.add_argument("--strict", action="store_true")
    args = ap.parse_args()
    if not (args.audit or args.strict):
        ap.print_help()
        return 2

    img = Image()
    img.selftest()
    omap, targets = original_map(img)
    noops = {op for op, h in omap.items() if h == NOOP_TARGET}
    real = {op for op, h in omap.items() if h is not None and h != NOOP_TARGET}

    cases = port_cases(PORT_FILE)
    print("original: %d opcodes 0x%03x..0x%03x, %d real handlers, %d no-ops (epilogue 0x%08x)"
          % (len(omap), FIRST_OPCODE, FIRST_OPCODE + GUARD_COUNT - 1, len(real), len(noops),
             NOOP_TARGET))
    print("port    : %s" % PORT_FILE.relative_to(ROOT))
    print("port cases: %d" % len(cases))
    print("")

    divergent = [c for c in cases if c in noops]
    out_of_range = [c for c in cases if c not in omap]
    agree = [c for c in cases if c in real]

    unhandled = sorted(op for op in real if op not in set(cases))

    # Every count is printed by the program in one block, so a caller that truncates the
    # output cannot mistake a cut listing for a short one.  (Reading a truncated listing as
    # the whole list happened once and was recorded as a method error.)
    print("COUNTS  portCases=%d  divergent(A)=%d  outOfRange(B)=%d  agree(C)=%d  "
          "originalWithoutPortCase(D)=%d"
          % (len(cases), len(divergent), len(out_of_range), len(agree), len(unhandled)))
    print("")

    print("A. port case is a NO-OP in the original  (%d)  <-- divergence candidates" % len(divergent))
    for c in divergent:
        print("     0x%03x" % c)
    print("")
    print("B. port case outside the original's dispatch range  (%d)" % len(out_of_range))
    for c in out_of_range:
        print("     0x%03x" % c)
    print("")
    print("C. port case has a REAL handler in the original  (%d)" % len(agree))
    for c in agree:
        print("     0x%03x -> 0x%08x" % (c, omap[c]))
    print("")

    unhandled = sorted(op for op in real if op not in set(cases))
    print("D. original has a real handler but the port has no case  (%d)" % len(unhandled))
    print("     " + " ".join("0x%03x" % o for o in unhandled[:40]) +
          (" ..." if len(unhandled) > 40 else ""))

    if args.strict and divergent:
        print("")
        print("STRICT: %d port cases are no-ops in the original" % len(divergent))
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
