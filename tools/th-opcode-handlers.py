"""Every title's opcode -> handler map, read straight out of the binary's two-level dispatch.

`tools/th12-opcode-handlers.py` established the shape for th12 and this is the same reading applied to the whole
series, so that a newly surveyed title becomes checked the same way th12 is. The dispatcher guards on the opcode,
normalises it to an index, reads one byte per opcode from a level-1 table, and jumps through a level-2 target table:

    handler(op) = u32[jump + byte[group + (op - first)] * 4]

The level-1 table is the part that is easy to miss: reading only the target table makes most permitted opcodes look
as if they had no handler, when their sharing lives in the bytes.

WHAT IS VALIDATED, per title
  * the target table's length is DISCOVERED by stopping at the first non-code entry, and must equal the length the
    guard-derived scan in `tools/th-dispatch-finder.mjs` records - two different routes to the same number;
  * every one of the permitted opcodes must have a group index inside the discovered table;
  * th12 keeps its own anchors, because they were established independently (target[0]'s body contains the spawn
    call site that an earlier measurement pinned to opcode 0x100).

    py -3 tools/th-opcode-handlers.py --title th13 --check
    py -3 tools/th-opcode-handlers.py --all --check
    py -3 tools/th-opcode-handlers.py --title th13 --emit artifacts/th13-opcode-handlers.json
"""

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from importlib import import_module

Image = import_module("th12-pe").Image
ROOT = Path(__file__).resolve().parents[1]

# exe paths, table addresses, the guard's normalisation bound and the target count, all from the executables as
# recorded in tools/th-dispatch-finder.mjs. `bound` is the largest normalised index the guard lets through, so the
# number of permitted opcodes is bound + 1.
TITLES = json.loads((ROOT / 'tools/ecl-dispatches.json').read_text(encoding='utf-8'))
for _row in TITLES.values():
    for _key in ('jump', 'group', 'opcodeLoad'):
        _row[_key] = int(_row[_key], 0)
TITLES['th12'].update(anchor_target0=0x41555D, anchor_spawn=0x4156DC)


def build_targets(img, title):
    """Target table, stopping at the first entry that is not a code address."""
    count = title["bound"] + 1
    targets = []
    for i in range(count):
        t = img.u32(title["jump"] + i * 4)
        if not img.is_code(t):
            break
        targets.append(t)
    return targets


def build_map(img, title, targets):
    """[(opcode, group_index, handler)] for every permitted opcode."""
    out = []
    for i in range(title["bound"] + 1):
        op = title["first"] + i
        g = img.data[img.offset_of(title["group"] + i)]
        out.append((op, g, targets[g] if g < len(targets) else None))
    return out


def check(name, title, verbose=True):
    img = Image(title["exe"])
    if name == "th12":
        img.selftest()
    fails = []
    if title.get('domain') != 'ECL':
        fails.append('dispatch is not classified as ECL')
    if img.read(title['opcodeLoad'], 4).hex() != title['opcodeBytes']:
        fails.append('ECL opcode load (+4) differs from the verified instruction')
    from capstone import Cs, CS_ARCH_X86, CS_MODE_32
    block = list(Cs(CS_ARCH_X86,CS_MODE_32).disasm(img.read(title['opcodeLoad'],0x60),title['opcodeLoad']))
    jump = next((ins for ins in block if ins.mnemonic == 'jmp'), None)
    if jump is None or hex(title['jump']) not in jump.op_str:
        fails.append('opcode load is not connected to the recorded indirect dispatch')

    targets = build_targets(img, title)
    if len(targets) != title["targets"]:
        fails.append("discovered %d targets, expected %d" % (len(targets), title["targets"]))

    if "anchor_target0" in title and targets and targets[0] != title["anchor_target0"]:
        fails.append("target[0] = 0x%08x, expected 0x%08x" % (targets[0], title["anchor_target0"]))
    if "anchor_spawn" in title and len(targets) >= 2 and not (targets[0] <= title["anchor_spawn"] < targets[1]):
        fails.append("spawn call site 0x%08x is not inside opcode 0x%03x's body [0x%08x, 0x%08x)"
                     % (title["anchor_spawn"], title["first"], targets[0], targets[1]))

    if not targets:
        fails.append("no targets discovered at all")
        mapping = []
    else:
        mapping = build_map(img, title, targets)
        unresolved = [(op, g) for op, g, h in mapping if h is None]
        if unresolved:
            fails.append("%d opcodes have a group index outside the target table (first: opcode 0x%03x -> group %d)"
                         % (len(unresolved), unresolved[0][0], unresolved[0][1]))

    distinct = len({h for _, _, h in mapping if h is not None})
    if title.get("distinct") is not None and distinct != title["distinct"]:
        fails.append("distinct handlers across all opcodes = %d, expected %d" % (distinct, title["distinct"]))

    if verbose:
        print("%s  guard bound 0x%03x -> opcodes 0x%03x..0x%03x (%d permitted)"
              % (name, title["bound"], title["first"], title["first"] + title["bound"], title["bound"] + 1))
        print("     level 1 byte table 0x%08x, level 2 target table 0x%08x: %d targets, %d distinct handlers resolved"
              % (title["group"], title["jump"], len(targets), distinct))
        for f in fails:
            print("     FAIL " + f)
    return fails, mapping


def emit(name, title, path):
    img = Image(title["exe"])
    targets = build_targets(img, title)
    mapping = build_map(img, title, targets)
    by_handler = defaultdict(list)
    for op, g, h in mapping:
        by_handler[h].append(op)
    handlers = {}
    for h, ops in sorted(by_handler.items(), key=lambda kv: (kv[0] is None, kv[0] or 0)):
        ops.sort()
        entry = {"opcodes": ["0x%03x" % o for o in ops], "opcodeCount": len(ops)}
        if h is not None:
            entry["firstBytes"] = img.read(h, 8).hex(" ")
        handlers["0x%08x" % (h or 0)] = entry
    doc = {
        "title": name,
        "domain": "ECL",
        "dispatch": "two level",
        "level1ByteTable": "0x%08x" % title["group"],
        "level2TargetTable": "0x%08x" % title["jump"],
        "guardBound": "0x%x" % title["bound"],
        "firstOpcode": "0x%03x" % title["first"],
        "lastOpcode": "0x%03x" % (title["first"] + title["bound"]),
        "opcodeCount": title["bound"] + 1,
        "targetCount": len(targets),
        "distinctHandlers": len(by_handler),
        "source": "%s two-level dispatch tables, read from the binary" % title["exe"],
        "handlers": handlers,
    }
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(doc, indent=1, sort_keys=True), encoding="utf-8")
    print("wrote %s  (%d handlers over %d opcodes)" % (out, len(by_handler), title["bound"] + 1))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--title", default="th12")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--emit", metavar="PATH")
    args = ap.parse_args()
    if not args.check and not args.emit:
        ap.print_help()
        return 2
    names = list(TITLES) if args.all else [args.title]
    rc = 0
    for name in names:
        if name not in TITLES:
            print("unknown title %s" % name)
            return 2
        fails, _ = check(name, TITLES[name])
        if fails:
            rc = 1
            continue
        elif args.check:
            print("     OK %s: all %d opcodes resolve" % (name, TITLES[name]["bound"] + 1))
        if args.emit:
            emit(name, TITLES[name], args.emit if len(names) == 1 else args.emit.replace(".json", "-%s.json" % name))
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
