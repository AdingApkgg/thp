#!/usr/bin/env python3
"""Walk shipped ECL resources with the record format the port's reader validates, and count what is there.

The format was settled by reading the port's own resource reader beside the real bytes: a sub-routine block is
reached through an offset table of `ECLH` blocks, its instructions start 16 bytes in, and each instruction
carries its own length in the word at `+0x06`. The record is 16 bytes of header plus its arguments:

    +0x00 time (i32)        +0x08 references (u16)
    +0x04 opcode (u16)      +0x0a difficulty (u8)
    +0x06 length (u16)      +0x0b parameter_count (u8)
                            +0x0c stack_adjustment (u32)
    +0x10 arguments

Walking every title with that one rule is the check that the format really is uniform, rather than uniform in the
one title that happened to be inspected. Counts are recorded so a change in the format breaks the gate.

    py -3 tools/th-ecl-walk.py --all --check
    py -3 tools/th-ecl-walk.py --title 13 --dir runtimes/th13/th13_web/artifacts/cpp/th13-data
"""
import argparse
import glob
import json
import struct
import sys
from collections import Counter
from pathlib import Path

DATA = {
    "12": r"runtimes/th12/th12_web/artifacts/cpp/th12-data",
    "13": r"runtimes/th13/th13_web/artifacts/cpp/th13-data",
    "14": r"runtimes/th14/th14_web/artifacts/cpp/th14-data",
    "16": r"runtimes/th16/th16_web/artifacts/cpp/th16-data",
    "17": r"runtimes/th17/th17_web/artifacts/cpp/th17-data",
    "18": r"runtimes/th18/th18_web/artifacts/cpp/th18-data",
}

# Measured with this walker. A format change shows up as a count change rather than as a silent reinterpretation.
RECORDED = {
    "12": {"files": 9, "subs": 854, "clean": 854, "instructions": 28409, "opcodes": 157},
    "13": {"files": 21, "subs": 721, "clean": 721, "instructions": 21899, "opcodes": 177},
    "14": {"files": 24, "subs": 758, "clean": 758, "instructions": 24798, "opcodes": 176},
    "16": {"files": 22, "subs": 788, "clean": 788, "instructions": 24302, "opcodes": 177},
    "17": {"files": 22, "subs": 812, "clean": 812, "instructions": 24655, "opcodes": 154},
    "18": {"files": 22, "subs": 798, "clean": 798, "instructions": 22721, "opcodes": 164},
}

HEADER = 36          # the fixed part of the resource header
INSTRUCTIONS = 16    # a sub-routine's first instruction starts this far into its ECLH block


def subroutines(blob):
    """The offsets of this file's sub-routine blocks, and the declared count, or (None, None)."""
    if len(blob) < HEADER or blob[:4] != b"SCPT":
        return None, None
    header = struct.unpack_from("<H", blob, 6)[0]
    count = struct.unpack_from("<H", blob, 16)[0]
    table = HEADER + header
    if table + count * 4 > len(blob):
        return None, None
    offsets = [struct.unpack_from("<I", blob, table + i * 4)[0] for i in range(count)]
    return offsets, count


def walk(blob, start, offsets):
    """Instructions of one sub-routine, plus the offset the walk stopped at.

    A record is usable when it is at least a header long, word-aligned, and stays inside the file; anything
    else ends the walk, and the caller compares the stop offset with the sub-routine entries so that a truncated
    walk is visible instead of being counted as a complete one.
    """
    at = start + INSTRUCTIONS
    out = []
    while at + INSTRUCTIONS <= len(blob):
        opcode = struct.unpack_from("<H", blob, at + 4)[0]
        length = struct.unpack_from("<H", blob, at + 6)[0]
        if length < INSTRUCTIONS or length % 4 or at + length > len(blob):
            break
        record = {
            "at": at,
            "opcode": opcode,
            "length": length,
            "time": struct.unpack_from("<i", blob, at)[0],
            "references": struct.unpack_from("<H", blob, at + 8)[0],
            "difficulty": blob[at + 0xA],
            "parameterCount": blob[at + 0xB],
            "arguments": [struct.unpack_from("<I", blob, at + 16 + 4 * i)[0] for i in range((length - 16) // 4)],
        }
        out.append(record)
        at += length
    return out, at


def measure(title, directory):
    files = sorted(glob.glob(str(Path(directory) / "*.ecl")))
    counts = {"files": 0, "subs": 0, "clean": 0, "instructions": 0, "rejected": 0}
    opcodes, sizes, offsets = Counter(), Counter(), []
    for path in files:
        blob = Path(path).read_bytes()
        starts, declared = subroutines(blob)
        if starts is None:
            counts["rejected"] += 1
            continue
        counts["files"] += 1
        for start in starts:
            if blob[start:start + 4] != b"ECLH":
                counts["rejected"] += 1
                continue
            instructions, end = walk(blob, start, starts)
            for ins in instructions:
                opcodes[ins["opcode"]] += 1
                sizes[ins["length"]] += 1
            counts["subs"] += 1
            counts["instructions"] += len(instructions)
            if instructions and (end in starts or end == len(blob)):
                counts["clean"] += 1
    counts["opcodes"] = len(opcodes)
    counts["sizeMin"] = min(sizes) if sizes else None
    counts["sizeMax"] = max(sizes) if sizes else None
    counts["mostCommon"] = opcodes.most_common(3)
    counts["sizes"] = sorted(sizes)[:8]
    counts["opcodeHigh"] = max(opcodes) if opcodes else None
    offsets.append(len(files))
    return counts


def report(title, counts):
    print("  th%-3s files=%-4d subs=%-5d clean=%-5d instructions=%-6d distinct opcodes=%-4d sizes=%d..%d"
          % (title, counts["files"], counts["subs"], counts["clean"], counts["instructions"],
             counts["opcodes"], counts["sizeMin"] or 0, counts["sizeMax"] or 0))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--title")
    ap.add_argument("--dir")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--json", metavar="PATH", help="write the per-title totals as JSON so another implementation can be compared")
    args = ap.parse_args()

    if args.all:
        titles = sorted(DATA, key=int)
        targets = [(t, DATA[t]) for t in titles if Path(DATA[t]).is_dir()]
        if not targets:
            print("  no extracted ECL directories found")
            sys.exit(1)
    elif args.title and args.dir:
        targets = [(args.title, args.dir)]
    else:
        targets = [(args.title or "?", args.dir or "")]

    bad = 0
    total = Counter()
    for title, directory in targets:
        counts = measure(title, directory)
        report(title, counts)
        total.update({k: v for k, v in counts.items() if isinstance(v, int)})
        want = RECORDED.get(title)
        if args.check and want is not None:
            for key in ("files", "subs", "clean", "instructions", "opcodes"):
                if want[key] != counts[key]:
                    bad += 1
                    print("      FAIL %s %s recorded=%d measured=%d" % (title, key, want[key], counts[key]))
            if counts["rejected"]:
                bad += 1
                print("      FAIL %s rejected=%d" % (title, counts["rejected"]))
        if args.title and counts["subs"] and counts["clean"] != counts["subs"]:
            print("      %d of %d sub-routines walked to a stop point" % (counts["clean"], counts["subs"]))
    if args.all:
        print("  all: %d sub-routines, %d clean, %d instructions"
              % (total["subs"], total["clean"], total["instructions"]))
        if total["clean"] != total["subs"]:
            bad += 1
    if args.json:
        # Written so that a second implementation - the port's own walker - can be compared number by number instead
        # of against a total someone remembered.
        payload = {}
        for title, directory in targets:
            counts = measure(title, directory)
            payload[title] = {k: v for k, v in counts.items() if isinstance(v, int)}
        Path(args.json).write_text(json.dumps(payload, indent=1, sort_keys=True), encoding="utf-8")
        print("  wrote %s" % args.json)
    if args.check:
        sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
