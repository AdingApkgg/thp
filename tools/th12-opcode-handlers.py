"""th12.exe opcode -> handler map, read straight out of the binary's two-level dispatch.

The dispatcher (EnemyInf's virtual slot 0, FUN_004154d0) guards with

    if (0x163 < (int)opcode - 0x100u) goto default;

so opcodes 0x100..0x263 -- 0x164 of them, 356 -- are dispatched.  The dispatch is TWO
LEVELS, which the code at 0x41553f states outright:

    0x41553f  movzx ecx, byte ptr [ecx + 0x419890]      level 1: one byte per opcode
    0x415546  jmp   dword ptr [ecx*4 + 0x419654]        level 2: the target table

    handler(opcode) = u32[0x419654 + byte[0x419890 + (opcode - 0x100)] * 4]

Reading only the target table was a real mistake: it has 143 entries, so 213 of the 356
permitted opcodes appeared to have no handler at all, when in fact the sharing lives in
the byte table.

WHY THIS FILE IS THE AUTHORITY
The decompiler's recovered `case` labels are incomplete (173 labels for 311 real
distinct handlers), so structural conclusions about which opcode has its own handler must
come from these two tables and not from the decompiled C.  That mistake was made once and
retracted.

SELF-VALIDATION
Nothing about the shape is assumed:
  * the target table's length is DISCOVERED by stopping at the first non-code entry --
    assuming the guard's 356 there was wrong, and 203 entries were instruction bytes;
  * every group index must be inside the target table, for ALL 356 opcodes;
  * target[0] must be the handler whose body contains the spawn call site 0x4156dc, which
    an independent measurement pinned to opcode 0x100.

    py -3 tools/th12-opcode-handlers.py --check
    py -3 tools/th12-opcode-handlers.py --emit artifacts/th12-opcode-handlers.json
"""

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from importlib import import_module

Image = import_module("th12-pe").Image

GROUP_TABLE = 0x419890                       # one byte per opcode
TARGET_TABLE = 0x419654                      # handler addresses, indexed by the byte
GUARD_BOUND = 0x163
FIRST_OPCODE = 0x100
GUARD_COUNT = GUARD_BOUND + 1                # 356 opcodes permitted by the guard
ANCHOR_SPAWN_CALL = 0x4156DC                 # inside opcode 0x100's body (measured, not read)
ANCHOR_TARGET0 = 0x41555D
EXPECT_TARGETS = 143
EXPECT_DISTINCT = 143                        # distinct handlers across all 356 opcodes
# 193 of the 356 opcodes share one target, 0x41962b, whose bytes are xor eax,eax followed by the
# stack-cookie load: the epilogue.  It is also the destination of the 0x415557 jne, so those 193
# opcodes are NO-OPS in this dispatcher.  An earlier count of 311 came from counting instruction
# bytes past the target table's real end, which the length discovery above now prevents.


def build_targets(img):
    """Target table, stopping at the first entry that is not a code address."""
    targets = []
    for i in range(GUARD_COUNT):
        t = img.u32(TARGET_TABLE + i * 4)
        if not img.is_code(t):
            break
        targets.append(t)
    return targets


def build_map(img, targets, count=GUARD_COUNT):
    """[(opcode, group_index, handler)] for every permitted opcode."""
    out = []
    for i in range(count):
        op = FIRST_OPCODE + i
        g = img.data[img.offset_of(GROUP_TABLE + i)]
        out.append((op, g, targets[g] if g < len(targets) else None))
    return out


def check(img, verbose=True):
    fails = []

    targets = build_targets(img)
    ntargets = len(targets)
    if ntargets != EXPECT_TARGETS:
        fails.append("discovered %d targets, expected %d" % (ntargets, EXPECT_TARGETS))

    if targets and targets[0] != ANCHOR_TARGET0:
        fails.append("target[0] = 0x%08x, expected 0x%08x" % (targets[0], ANCHOR_TARGET0))
    if ntargets >= 2 and not (targets[0] <= ANCHOR_SPAWN_CALL < targets[1]):
        fails.append(
            "spawn call site 0x%08x is not inside opcode 0x100's body [0x%08x, 0x%08x)"
            % (ANCHOR_SPAWN_CALL, targets[0], targets[1])
        )

    mapping = build_map(img, targets)
    unresolved = [(op, g) for op, g, h in mapping if h is None]
    if unresolved:
        fails.append(
            "%d opcodes have a group index outside the target table (first: opcode 0x%03x -> "
            "group %d)" % (len(unresolved), unresolved[0][0], unresolved[0][1])
        )

    distinct = len({h for _, _, h in mapping if h is not None})
    if distinct != EXPECT_DISTINCT:
        fails.append("distinct handlers across all opcodes = %d, expected %d"
                     % (distinct, EXPECT_DISTINCT))

    if verbose:
        print("guard bound 0x%x  ->  opcodes 0x%03x..0x%03x  (%d)"
              % (GUARD_BOUND, FIRST_OPCODE, FIRST_OPCODE + GUARD_COUNT - 1, GUARD_COUNT))
        print("level 1  byte table 0x%08x  (%d opcodes)" % (GROUP_TABLE, GUARD_COUNT))
        print("level 2  target table 0x%08x  %d targets, %d distinct targets"
              % (TARGET_TABLE, ntargets, len(set(targets))))
        print("resolved handlers across all opcodes: %d distinct" % distinct)
        print("anchor: target[0] = 0x%08x, spawn call site 0x%08x inside its body"
              % (targets[0], ANCHOR_SPAWN_CALL))
        if fails:
            print("FAIL:")
            for f in fails:
                print("  - " + f)
        else:
            print("OK  two-level opcode handler map validated (all %d opcodes resolve)"
                  % GUARD_COUNT)
    return fails


def emit(img, path):
    targets = build_targets(img)
    mapping = build_map(img, targets)
    by_handler = defaultdict(list)
    for op, g, h in mapping:
        by_handler[h].append(op)

    handlers = {}
    for h, ops in by_handler.items():
        ops.sort()
        entry = {"opcodes": ["0x%03x" % o for o in ops], "opcodeCount": len(ops)}
        if h is not None:
            entry["firstBytes"] = img.read(h, 8).hex(" ")
        handlers["0x%08x" % (h or 0)] = entry

    doc = {
        "dispatch": "two level",
        "level1ByteTable": "0x%08x" % GROUP_TABLE,
        "level2TargetTable": "0x%08x" % TARGET_TABLE,
        "guardBound": "0x%x" % GUARD_BOUND,
        "firstOpcode": "0x%03x" % FIRST_OPCODE,
        "lastOpcode": "0x%03x" % (FIRST_OPCODE + GUARD_COUNT - 1),
        "opcodeCount": GUARD_COUNT,
        "targetCount": len(targets),
        "distinctHandlers": len(by_handler),
        "source": "th12.exe two-level dispatch tables, read from the binary",
        "note": "authority for opcode->handler; the decompiler's case labels are incomplete",
        "handlers": handlers,
    }
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(doc, indent=1, sort_keys=True), encoding="utf-8")
    print("wrote %s  (%d handlers over %d opcodes)" % (out, len(by_handler), GUARD_COUNT))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--emit", metavar="PATH")
    args = ap.parse_args()
    if not args.check and not args.emit:
        ap.print_help()
        return 2
    img = Image()
    img.selftest()
    rc = 0
    if args.check:
        rc = 1 if check(img) else 0
    if args.emit:
        emit(img, args.emit)
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
