"""Wildcard byte-pattern search over th12.exe's .text, with a built-in positive control.

WHY BYTES AND NOT DISASSEMBLY
A linear disassembly sweep of .text desynchronises at the first embedded jump table, so
every later instruction boundary is wrong.  That mistake was made and recorded.  A byte
pattern search has no boundaries to get wrong, and a match address is by construction an
instruction start, so context can then be disassembled safely from the match itself.

Pattern syntax: hex bytes separated by spaces.  `?` is a wildcard nibble, `??` a wildcard
byte.  Example:

    py -3 tools/th12-pattern.py --find "b8 16 00 00 00 00 40 00"
    py -3 tools/th12-pattern.py --check

`--check` runs built-in positive controls: patterns that are known to match.  A search
that reports nothing is only meaningful once the same machinery is shown to report
something, so the control is not optional.

The loose tail patterns matter: `b8 16 00 00 00 00 40 00` catches any instruction that
sets bit 0x400000 of the field at +0x16b8 whatever its addressing form, whereas a full
opcode pattern would only catch one encoding.
"""

import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from importlib import import_module

Image = import_module("th12-pe").Image

TEXT_VA = 0x401000
TEXT_LEN = 0x96C00

# name -> pattern.  These are known to exist; --check fails if any reports nothing.
CONTROLS = [
    ("selector global load", "a1 a8 0c 4b 00"),          # mov eax, [0x4b0ca8]  (6 sites)
    ("manager global load", "a1 dc 43 4b 00"),           # mov eax, [0x4b43dc]
    ("epilogue jump", "e9 02 1b 00 00"),                 # jmp 0x41962b (the deregister's tail)
    ("register write", "89 44 b1 1c"),                   # mov [ecx+esi*4+0x1c], eax
    ("the deregister clear", "c7 44 8a 1c"),             # mov [edx+ecx*4+0x1c], imm32 (source is an
                                                          #   immediate, so the opcode is C7, not 89)
]


def compile_pattern(text):
    parts = text.split()
    rx = []
    for p in parts:
        if p == "??":
            rx.append(".")
        elif "?" in p:
            rx.append(p.replace("?", "."))
        else:
            rx.append(re.escape(bytes.fromhex(p).decode("latin-1")))
    return re.compile("".join(rx).encode("latin-1"), re.DOTALL)


def search(img, text, verbose=True):
    rx = compile_pattern(text)
    buf = img.read(TEXT_VA, TEXT_LEN)
    hits = [m.start() for m in rx.finditer(buf)]
    if verbose:
        print("%-42s %d hit(s)" % (text, len(hits)))
        for off in hits[:40]:
            va = TEXT_VA + off
            # a match address is an instruction start, so this is boundary-safe
            try:
                body = img.read(va, 24)
            except ValueError:
                body = b""
            print("     0x%08x  %s" % (va, body.hex(" ")))
    return hits


def check(img):
    fails = []
    print("POSITIVE CONTROLS")
    for name, pat in CONTROLS:
        hits = search(img, pat, verbose=False)
        status = "ok" if hits else "FAIL"
        print("  %-24s %-34s %d hit(s)  %s" % (name, pat, len(hits), status))
        if not hits:
            fails.append(name)
    # a deliberately impossible pattern must find nothing -- this is the other direction
    neg = search(img, "de ad be ef de ad be ef de ad be ef", verbose=False)
    print("  %-24s %-34s %d hit(s)  %s" % ("negative control", "de ad be ef x3", len(neg),
                                           "ok" if not neg else "FAIL"))
    if neg:
        fails.append("negative control matched")
    print("")
    if fails:
        print("CHECK FAILED: " + ", ".join(fails))
    else:
        print("OK  pattern search validated in both directions")
    return fails


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--find", metavar="PATTERN")
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()
    if not (args.find or args.check):
        ap.print_help()
        return 2
    img = Image()
    img.selftest()
    rc = 0
    if args.check:
        rc = 1 if check(img) else 0
    if args.find:
        search(img, args.find)
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
