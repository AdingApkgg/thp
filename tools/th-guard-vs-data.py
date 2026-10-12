#!/usr/bin/env python3
"""Compare each title's measured guard range against the opcodes its shipped scripts actually use.

A guard's range is measured from the image; this asks the independent question of which of its opcodes the data
reaches, and which used opcodes fall outside. Measured this way, th12 and th14 are covered by their guards while
th13, th16, th17 and th18 are not - roughly a third of each of those titles' command opcodes sits outside its own
guard. Every one of those four also uses `0x12c`, one below the `0x12d` their guards begin at, and th14's guard
begins at `0x12c`; so at least part of the gap may be a first-value that is off by one rather than a second
dispatcher.

    py -3 tools/th-guard-vs-data.py --check
"""
import argparse
import glob
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

# first opcode and permitted count, as recorded in docs/porting/plan section 2b.
GUARD = {
    "12": (0x100, 356),
    "13": (0x12D, 208),
    "14": (0x12C, 704),
    "16": (0x12D, 313),
    "17": (0x12D, 313),
    "18": (0x12D, 314),
}

# Measured with this tool; a guard or a corpus change shows up here rather than silently.
RECORDED = {
    "12": {"high": 112, "inGuard": 111, "outGuard": 1},
    "13": {"high": 129, "inGuard": 50, "outGuard": 79},
    "14": {"high": 131, "inGuard": 131, "outGuard": 0},
    "16": {"high": 131, "inGuard": 107, "outGuard": 24},
    "17": {"high": 107, "inGuard": 88, "outGuard": 19},
    "18": {"high": 118, "inGuard": 96, "outGuard": 22},
}

# The one below the guard start that four titles share, and the first value their guards use.
FIRST_BELOW = 0x12C
GUARD_START = 0x12D


def used_opcodes(title, directory):
    ops = Counter()
    for path in sorted(glob.glob(str(Path(directory) / "*.ecl"))):
        blob = Path(path).read_bytes()
        if len(blob) < 36 or blob[:4] != b"SCPT":
            continue
        header = struct.unpack_from("<H", blob, 6)[0]
        count = struct.unpack_from("<H", blob, 16)[0]
        table = 36 + header
        if table + count * 4 > len(blob):
            continue
        for i in range(count):
            start = struct.unpack_from("<I", blob, table + i * 4)[0]
            if blob[start:start + 4] != b"ECLH":
                continue
            at = start + 16
            while at + 16 <= len(blob):
                opcode = struct.unpack_from("<H", blob, at + 4)[0]
                length = struct.unpack_from("<H", blob, at + 6)[0]
                if length < 16 or length % 4 or at + length > len(blob):
                    break
                ops[opcode] += 1
                at += length
    return ops


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()

    bad = 0
    print("  title  high opcodes  inside guard  outside guard  outside (top)")
    for title in sorted(DATA, key=int):
        if not Path(DATA[title]).is_dir():
            print("  th%-4s (no extracted resources)" % title)
            continue
        ops = used_opcodes(title, DATA[title])
        first, permitted = GUARD[title]
        last = first + permitted - 1
        high = {k: v for k, v in ops.items() if k >= 0x100}
        inside = sorted(k for k in high if first <= k <= last)
        outside = sorted(k for k in high if not first <= k <= last)
        listed = ", ".join("%#x" % k for k in outside[:4])
        print("  th%-4s %-12d %-13d %-14d %s" % (title, len(inside) + len(outside), len(inside), len(outside), listed))
        want = RECORDED.get(title)
        if args.check and want is not None:
            for key, value in (("high", len(inside) + len(outside)),
                               ("inGuard", len(inside)), ("outGuard", len(outside))):
                if want[key] != value:
                    bad += 1
                    print("      FAIL %s %s recorded=%d measured=%d" % (title, key, want[key], value))
        if title in ("13", "16", "17", "18"):
            if FIRST_BELOW not in high:
                bad += 1
                print("      FAIL th%s no longer uses %#x, so the off-by-one note needs revisiting"
                      % (title, FIRST_BELOW))
            elif first == GUARD_START:
                print("      note: %#x is used but sits one below the guard start %#x"
                      % (FIRST_BELOW, GUARD_START))
    if args.check:
        sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
