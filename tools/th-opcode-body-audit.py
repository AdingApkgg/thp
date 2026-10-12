#!/usr/bin/env python3
"""Sort each title's ECL opcode handlers by what they do to the script pointer.

The dispatch tables say which handler an opcode reaches; they do not say whether reaching it does anything. A large
share of every title's opcodes share one handler whose whole body advances the script pointer past the instruction -
for the interpreter that is a no-op, and it needs no transcription at all. This reads the handler map that
tools/th-opcode-handlers.py --emit writes, disassembles each handler body out of the title's executable, and crosses
the result with the opcodes the title's own data uses and the numbers the port already names.

    py -3 tools/th-opcode-body-audit.py --all
    py -3 tools/th-opcode-body-audit.py --title 13 --check
    py -3 tools/th-opcode-body-audit.py --all --json tools/tmp/opcode-worklist.json

The point is a work list: how many of a title's opcodes actually need a body, and which of those the port does not
name yet.
"""
import argparse
import glob
import importlib.util
import json
import re
import struct
import subprocess
import sys
from pathlib import Path

import capstone

REPO = Path(__file__).resolve().parent.parent
TMP = REPO / "tools" / "tmp"

TITLES = {
    "12": "th12", "13": "th13", "14": "th14", "16": "th16", "17": "th17", "18": "th18",
}

# Measured in round 259 and kept so that a change in an executable, in the data, in the dispatch tables or in the
# port's sources shows up as a failure rather than as a new number nobody questions. th12's row reproduces the
# section 32 matrix exactly (157 used, 112 dispatched, 107 named, 5 unnamed), which is what made the rest believable.
RECORDED = {
    "th12": dict(permitted=356, handlers=143, skipHandlers=0, bodyHandlers=143, used=157, usedHigh=112, usedLow=45,
                 usedInRange=111, usedSkip=0, usedBodies=111, usedNamed=107, namedOutOfRange=0, namedSkip=0,
                 unresolvedCount=4, outOfRangeCount=1, guardFail="0x41962b"),
    "th13": dict(permitted=704, handlers=158, skipHandlers=0, bodyHandlers=158, used=177, usedHigh=129, usedLow=48,
                 usedInRange=129, usedSkip=0, usedBodies=129, usedNamed=62, namedOutOfRange=0, namedSkip=0,
                 unresolvedCount=67, outOfRangeCount=0, guardFail="0x41f738"),
    "th14": dict(permitted=704, handlers=169, skipHandlers=0, bodyHandlers=169, used=176, usedHigh=131, usedLow=45,
                 usedInRange=131, usedSkip=0, usedBodies=131, usedNamed=64, namedOutOfRange=0, namedSkip=0,
                 unresolvedCount=67, outOfRangeCount=0, guardFail="0x429c28"),
    "th16": dict(permitted=702, handlers=174, skipHandlers=0, bodyHandlers=174, used=177, usedHigh=131, usedLow=46,
                 usedInRange=131, usedSkip=0, usedBodies=131, usedNamed=65, namedOutOfRange=0, namedSkip=0,
                 unresolvedCount=66, outOfRangeCount=0, guardFail="0x422a9b"),
    "th17": dict(permitted=702, handlers=173, skipHandlers=0, bodyHandlers=173, used=154, usedHigh=107, usedLow=47,
                 usedInRange=107, usedSkip=0, usedBodies=107, usedNamed=55, namedOutOfRange=0, namedSkip=0,
                 unresolvedCount=52, outOfRangeCount=0, guardFail="0x4265f2"),
    "th18": dict(permitted=702, handlers=175, skipHandlers=0, bodyHandlers=175, used=164, usedHigh=118, usedLow=46,
                 usedInRange=118, usedSkip=0, usedBodies=118, usedNamed=60, namedOutOfRange=0, namedSkip=0,
                 unresolvedCount=58, outOfRangeCount=0, guardFail="0x436417"),
}

SKIP_IDIOM = (
    re.compile(r"^(\w+), word ptr \[edi \+ 2\]$"),
    re.compile(r"^(\w+), edi$"),
    re.compile(r"^dword ptr \[ebx[^\]]*\], (\w+)$"),
)


def load(name):
    path = Path(__file__).resolve().parent / name
    spec = importlib.util.spec_from_file_location(path.stem.replace("-", "_"), path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def sections(image):
    """(imageBase, [(rva, pointerToRawData, span)]) from the PE headers, following e_lfanew as tools/tmp/xdis.py does."""
    lfanew = struct.unpack_from("<I", image, 0x3C)[0]
    base = struct.unpack_from("<I", image, lfanew + 0x34)[0]
    count = struct.unpack_from("<H", image, lfanew + 6)[0]
    size = struct.unpack_from("<H", image, lfanew + 20)[0]
    table = lfanew + 24 + size
    out = []
    for i in range(count):
        at = table + i * 40
        vsize = struct.unpack_from("<I", image, at + 8)[0]
        rva = struct.unpack_from("<I", image, at + 12)[0]
        raw_size = struct.unpack_from("<I", image, at + 16)[0]
        raw = struct.unpack_from("<I", image, at + 20)[0]
        out.append((rva, raw, max(vsize, raw_size)))
    return base, out


def body(image, base, map_, address, limit):
    rva = address - base
    for srva, raw, span in map_:
        if srva <= rva < srva + span:
            return image[raw + rva - srva:]
    raise SystemExit("handler 0x%08x is not inside any section" % address)


def handler_map(title):
    path = TMP / ("handlers-%s.json" % title)
    # Cached addresses may belong to another VM or executable. Always re-derive.
    subprocess.run([sys.executable, str(REPO / "tools" / "th-opcode-handlers.py"),
                    "--title", title, "--emit", str(path)], check=True, stdout=subprocess.DEVNULL)
    return json.loads(path.read_text(encoding="utf-8"))


def used_opcodes(title, walk):
    """Opcode -> how many times the title's own data uses it, which is what orders the transcription work."""
    directory = REPO / "runtimes" / title / (title + "_web") / "artifacts" / "cpp" / (title + "-data")
    used = {}
    for file in sorted(glob.glob(str(directory / "*.ecl"))):
        blob = Path(file).read_bytes()
        offsets, _ = walk.subroutines(blob)
        if not offsets:
            continue
        for start in offsets:
            records, _ = walk.walk(blob, start, offsets)
            for record in records:
                used[record["opcode"]] = used.get(record["opcode"], 0) + 1
    return used


def virtual(base, map_, offset):
    """The virtual address of a file offset. A file offset is not `virtual - base`: the first section maps 0x400 to
    0x1000, so the two differ by 0xC00 and a decode addressed as `base + offset` lands 0xC00 bytes early, which is
    exactly the kind of error that produces a plausible branch to the wrong place."""
    for srva, raw, span in map_:
        if raw <= offset < raw + span:
            return base + srva + (offset - raw)
    raise SystemExit("file offset %#x is not inside any section" % offset)


def guard_fail(image, base, map_, group, bound, jump, disassembler):
    """The address an out-of-range opcode reaches, read from the dispatch site in the executable.

    The site is pinned by three things at once: it loads the group byte from the group table, its guard compares the
    index against this title's bound, and the load is immediately followed by a jump through the title's target table.
    Matching the group address alone is not enough, because the same four bytes occur elsewhere in the image and a
    disassembly started there produces a branch that looks real. Out-of-range opcodes reach this failure target and
    nothing else, so whether it merely returns or advances the script pointer decides whether they need a body.
    """
    needle = struct.pack("<I", group)
    for at in range(len(image) - 10):
        if image[at] == 0x0F and image[at + 1] == 0xB6 and image[at + 3:at + 7] == needle:
            for shift in range(0, 16):
                start = at - shift
                # Decoded at its virtual address, so a branch's printed target is a virtual address too.
                instructions = list(disassembler.disasm(image[start:at], virtual(base, map_, start)))
                if len(instructions) < 2 or "(bad)" in " ".join(i.mnemonic for i in instructions):
                    continue
                if instructions[-1].address + instructions[-1].size != virtual(base, map_, at):
                    continue
                branch = instructions[-1]
                if branch.mnemonic != "ja" and branch.mnemonic != "jbe":
                    continue
                guard = instructions[-2]
                try:
                    if guard.mnemonic != "cmp" or int(guard.op_str.split(",")[1].strip(), 0) != bound:
                        continue
                except (ValueError, IndexError):
                    continue
                following = list(disassembler.disasm(image[at + 7:at + 39], virtual(base, map_, at + 7)))
                # Allow compiler bookkeeping between the byte lookup and indirect jump.
                branch_index = next((i for i,p in enumerate(following) if p.mnemonic != 'mov' and p.mnemonic != 'movzx'), None)
                if branch_index is None or following[branch_index].mnemonic != "jmp" or hex(jump) not in following[branch_index].op_str:
                    continue
                candidate = int(branch.op_str, 16)
                try:
                    body(image, base, map_, candidate, candidate + 4)
                except SystemExit:
                    continue
                return candidate
    raise SystemExit("no dispatch site found for group table %#x" % group)


def skips_instruction(instructions):
    """True when a short handler only moves the script pointer past the current instruction.

    Two shapes occur, and they differ by which side the arithmetic lands on. TH12 and TH13 compute the next address in
    a register and store it; TH16, TH17 and TH18 read the length into a register and add it to the stored pointer. In
    both, the first instruction reads the instruction's length word at `[edi + 2]` and the arithmetic adds that length
    to where the script pointer is kept, with no call in between. The later titles also index with `[edi + ebx + 2]`.
    """
    if not instructions:
        return False
    head = instructions[0]
    if head.mnemonic != "movzx" or "word ptr [edi" not in head.op_str or "+ 2]" not in head.op_str:
        return False
    register = head.op_str.split(",")[0].strip()
    for instruction in instructions[1:4]:
        if instruction.mnemonic == "call":
            return False
        if instruction.mnemonic == "add" and instruction.op_str.split(",")[0].strip() == register:
            other = instruction.op_str.split(",")[1].strip()
            return "edi" in other or "word ptr" not in other
        if instruction.mnemonic == "add" and register in instruction.op_str \
                and instruction.op_str.split(",")[0].strip().startswith("dword ptr"):
            return True
    return False


def is_noop(image, base, map_, address, disassembler):
    """True when the code at an address only advances the script pointer or returns.

    Two shapes occur. The skip shape advances the script pointer past the instruction. The other is the compiler's
    failure epilogue: set the return value to zero, restore the stack cookie through the security-check call, pop, and
    return, writing nothing outside the stack frame. Both leave the enemy untouched, which is what makes an opcode that
    reaches them need no transcription.
    """
    raw = body(image, base, map_, address, address + 0x60)[:0x60]
    instructions = []
    for instruction in disassembler.disasm(raw, address):
        instructions.append(instruction)
        if instruction.mnemonic in ("ret", "jmp"):
            break
    if not instructions:
        return False
    if skips_instruction(instructions):
        return True
    if instructions[-1].mnemonic != "ret" or instructions[0].mnemonic != "xor" or instructions[0].op_str != 'eax, eax':
        return False
    # Every write in the epilogue is to the stack frame or the exception handler slot, and the only call is the stack
    # cookie check that the compiler inserts. Nothing here can touch an enemy.
    for index, instruction in enumerate(instructions):
        if instruction.mnemonic not in ('xor','mov','pop','ret','call'):
            return False
        if instruction.mnemonic == 'xor' and instruction.op_str not in ('eax, eax','ecx, esp','ecx, ebp'):
            return False
        if instruction.mnemonic == 'mov':
            destination, source = [part.strip() for part in instruction.op_str.split(',',1)]
            stack_cookie = destination == 'ecx' and source.startswith(('dword ptr [esp','dword ptr [ebp'))
            restore = instruction.op_str in ('esp, ebp','esp, ebx','dword ptr fs:[0], ecx')
            if not stack_cookie and not restore:
                return False
        if instruction.mnemonic == 'pop' and instruction.op_str not in ('ecx','ebx','esi','edi','ebp'):
            return False
        if instruction.mnemonic == "call":
            # The sole allowed call is the stack-cookie check, with ecx just decoded.
            previous = instructions[index-1] if index else None
            if previous is None or previous.mnemonic != 'xor' or previous.op_str not in ('ecx, esp','ecx, ebp'):
                return False
    return True


def classify(title, port_names):
    data = handler_map(title)
    # The executable path lives in the handler tool's title table, which is also the table that named the dispatch
    # addresses, so the bytes read here are the bytes the dispatch was read from.
    executable = load("th-opcode-handlers.py").TITLES[title]["exe"]
    image = Path(executable).read_bytes()
    base, map_ = sections(image)
    handlers_data = data["handlers"]
    addresses = sorted(int(a, 16) for a in handlers_data)
    disassembler = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)

    handlers = {}
    for index, address in enumerate(addresses):
        limit = addresses[index + 1] if index + 1 < len(addresses) else address + 0x180
        raw = body(image, base, map_, address, limit)[:limit - address]
        # A handler ends where it transfers control, not where the next handler starts: the shared skip handler is
        # four instructions and a tail jump, and the bytes after it belong to unrelated code, calls included.
        instructions = []
        for instruction in disassembler.disasm(raw, address):
            instructions.append(instruction)
            if instruction.mnemonic in ("ret", "jmp"):
                break
        calls = [i for i in instructions if i.mnemonic == "call"]
        heads = instructions[:3]
        idiom = skips_instruction(instructions)
        handlers[address] = {
            "opcodes": handlers_data["%#010x" % address]["opcodes"],
            "instructions": len(instructions),
            "calls": len(calls),
            "idiom": idiom,
            "skip": idiom and not calls,
            "head": " ".join(i.mnemonic + " " + i.op_str for i in heads),
        }

    permitted = sum(len(h["opcodes"]) for h in handlers.values())
    skip = [h for h in handlers.values() if h["skip"]]
    first = int(data["firstOpcode"], 16)
    last = int(data["lastOpcode"], 16)
    counts = used_opcodes(title, load("th-ecl-walk.py"))
    used = set(counts)
    used_high = {o for o in used if o >= first}
    opcode_skip = set()
    for handler in skip:
        opcode_skip.update(int(op, 16) for op in handler["opcodes"])
    title_table = load("th-opcode-handlers.py").TITLES[title]
    target = guard_fail(image, base, map_, title_table["group"], title_table["bound"], title_table["jump"], disassembler)
    fail_is_noop = is_noop(image, base, map_, target, disassembler)
    # An opcode outside the permitted range never reaches the group table: the guard sends it to the failure branch,
    # so its body is whatever that branch does, not the handler some table entry would have named. Everything below
    # is therefore counted over the guarded range only; counting over every used opcode made TH13 report 115 bodies
    # where 50 of its 128 dispatched opcodes are even in range.
    out_of_range = sorted(o for o in used_high if o > last)
    in_range = {o for o in used_high if o <= last}
    skip_used = sorted(o for o in in_range if o in opcode_skip)
    # A skip handler advances the script pointer, so the opcode needs no body whether or not the port has a case for
    # that number. Keeping the named set free of skips is what makes bodies = named + unresolved an identity.
    named_used = sorted(o for o in in_range if o in port_names and o not in opcode_skip)
    unresolved = sorted(o for o in in_range if o not in opcode_skip and o not in port_names)
    return {
        "title": title,
        "permitted": permitted,
        "handlers": len(handlers),
        "skipHandlers": len(skip),
        "bodyHandlers": len(handlers) - len(skip),
        "used": len(used),
        "usedHigh": len(used_high),
        "usedLow": len(used) - len(used_high),
        "usedInRange": len(in_range),
        "usedSkip": len(skip_used),
        "usedSkipOpcodes": [hex(o) for o in skip_used],
        # In-range opcodes that reach a handler with a body, i.e. the ones a transcription could be missing.
        "usedBodies": len(in_range) - len(skip_used),
        "usedNamed": len(named_used),
        # Diagnostics, not work: a number the port implements for another title, and one this title skips anyway.
        "namedOutOfRange": len([o for o in used_high if o > last and o in port_names]),
        "namedSkip": len([o for o in in_range if o in port_names and o in opcode_skip]),
        "guardFail": hex(target),
        "guardFailIsNoop": fail_is_noop,
        "outOfRange": [hex(o) for o in out_of_range],
        "outOfRangeCount": len(out_of_range),
        "unresolved": [hex(o) for o in unresolved],
        "unresolvedCount": len(unresolved),
    }


def worklist(rows, mentions):
    """The opcodes the port does not name, ordered by how much transcribing one would buy.

    The unnamed sets of the five later titles overlap heavily, so an opcode wanted by all six and used often is worth
    far more than one wanted by a single title. Titles count first, then how many times the data uses it.
    """
    walker = load("th-ecl-walk.py")
    counts = {row["title"]: used_opcodes(row["title"], walker) for row in rows}
    wanted = {}
    for row in rows:
        for opcode in map(lambda text: int(text, 16), row["unresolved"]):
            entry = wanted.setdefault(opcode, {"titles": [], "uses": 0})
            entry["titles"].append(row["title"])
            entry["uses"] += counts[row["title"]][opcode]
    order = sorted(wanted.items(), key=lambda item: (-len(item[1]["titles"]), -item[1]["uses"], item[0]))
    print("  %-8s %6s %7s  %s" % ("opcode", "titles", "uses", "named by the port / titles"))
    for opcode, entry in order:
        print("  %-8s %6d %7d  %s" % (hex(opcode), len(entry["titles"]), entry["uses"],
                                      "no" if opcode not in mentions else "yes"))
    # A transcription starts at an address, so the addresses are printed for the opcodes more than one title wants.
    maps = {row["title"]: {int(op, 16): int(address, 16)
                           for address, entry in handler_map(row["title"])["handlers"].items()
                           for op in entry["opcodes"]} for row in rows}
    names = [row["title"] for row in rows]
    print("  addresses for the opcodes wanted by more than one title")
    print("  %-8s %s" % ("opcode", "  ".join("%-11s" % n for n in names)))
    for opcode, entry in order:
        if len(entry["titles"]) < 2:
            break
        cells = "  ".join("%-11s" % (hex(maps[n][opcode]) if opcode in maps[n] else "-") for n in names)
        print("  %-8s %s" % (hex(opcode), cells))
    return order


def report(row):
    print("  %s  %d permitted opcodes over %d handlers: %d skip-style, %d with bodies"
          % (row["title"], row["permitted"], row["handlers"], row["skipHandlers"], row["bodyHandlers"]))
    print("       data uses %d opcodes: %d below the dispatch table (the interpreter's own core), %d through it; "
          "of those %d land on a skip handler and %d reach a body"
          % (row["used"], row["usedLow"], row["usedHigh"], row["usedSkip"], row["usedBodies"]))
    print("       the port names %d of the dispatched ones; %d used opcodes are past the guard and reach %s (%s)" % (row["usedNamed"], row["outOfRangeCount"], row["guardFail"], "a no-op" if row["guardFailIsNoop"] else "a body"))
    if row["namedSkip"] or row["namedOutOfRange"]:
        print("       note: %d of the named ones are a skip in this title and %d are past its guard, so the port's case for them must not run here"
              % (row["namedSkip"], row["namedOutOfRange"]))
    if row["unresolved"]:
        print("       used, reaches a body, not named by the port (%d): %s"
              % (len(row["unresolved"]), " ".join(row["unresolved"])))
    else:
        print("       used, reaches a body, not named by the port: none")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--title")
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--worklist", action="store_true",
                        help="order the unnamed opcodes by how many titles want them and how often they are used")
    parser.add_argument("--json", metavar="PATH")
    args = parser.parse_args()

    coverage = load("th-opcode-coverage.py")
    # A case label, not a mention: the mention-based count called five unimplemented laser opcodes named because TH11
    # comments described bodies they never had. See the note on port_cases() in th-opcode-coverage.py.
    names = coverage.port_cases() | coverage.port_exact_ops()
    titles = sorted(TITLES, key=int) if args.all or not args.title else [args.title]
    rows, bad = [], 0
    for digits in titles:
        row = classify(TITLES[digits], names)
        report(row)
        rows.append(row)
        want = RECORDED.get(TITLES[digits])
        if args.check and want:
            for key in want:
                if want[key] != row[key]:
                    bad += 1
                    print("       FAIL %s %s recorded=%s measured=%s" % (row["title"], key, want[key], row[key]))
    if args.worklist:
        worklist(rows, names)
    if args.json:
        Path(args.json).write_text(json.dumps({r["title"]: r for r in rows}, indent=1, sort_keys=True),
                                   encoding="utf-8")
        print("  wrote %s" % args.json)
    if args.check:
        sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
