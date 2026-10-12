#!/usr/bin/env python3
"""RETIRED: this historical heuristic mixed ANM and ECL interpreters.

Do not use its output to infer ECL layout. Use th-dispatch-finder.mjs --check for
the domain-verified dispatch and th-ecl-port-check.mjs --all for resource layout.
--historical exposes the old measurements only for investigating that mistake.

Original (incorrect) description follows:
Measure how each title's ECL interpreter encodes an instruction, from the interpreter's own code.

The dispatcher loop reloads the instruction pointer from the enemy object and reads the opcode out of it:

    th13  0x4624fd  mov edi, dword ptr [ebx + 0x28]     ; the interpreter's instruction pointer
          0x462500  movsx ecx, word ptr [edi + 4]
          0x462514  movsx eax, word ptr [edi]

so the instruction starts with a 16-bit opcode. What differs between titles is how the pointer then advances,
and that decides the whole on-disk argument layout:

    th12  `lea eax, [edi + 0x10]` / `add edi, 0x10`     - a FIXED 16-byte instruction
    th13  `movzx edx, word ptr [edi + 2]` / `add edx, edi` - a VARIABLE length taken from the instruction

A fixed layout means arguments live at `header + index * 4`; a variable one means they live after the header and
the port cannot reuse the other title's reader. This is measured here by counting the instruction shapes, so the
per-title answer is a count rather than a reading of one function.

    py -3 tools/th-ecl-format.py            report
    py -3 tools/th-ecl-format.py --check    exit 1 if a recorded title's shape no longer matches
"""
import argparse
import struct
import sys
from importlib import import_module
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
Image = import_module("th12-pe").Image

EXES = {
    "th12": "H:/Games/th/12/th12.exe",
    "th13": "H:/Games/th/13/th13.exe",
    "th14": "H:/Games/th/14/th14.exe",
    "th16": "H:/Games/th/16/th16.exe",
    "th17": "H:/Games/th/17/th17.exe",
    "th18": "H:/Games/th/18/th18.exe",
}

# What the counts were measured to be. `fixed` entries are the `[edi + 0x10]` shapes, `variable` the
# `movzx ..., [edi + 2]` shapes. A title counts as variable-length when the variable shape dominates.
RECORDED = {
    "th12": {"fixed": 11, "variable": 0, "sizeField": 4, "shape": "fixed", "peak": 0x04},
    "th13": {"fixed": 31, "variable": 104, "sizeField": 105, "shape": "variable", "peak": 0x06},
    "th14": {"fixed": 6, "variable": 0, "sizeField": 2, "shape": "fixed", "peak": 0x04},
    "th16": {"fixed": 7, "variable": 112, "sizeField": 112, "shape": "variable", "peak": 0x06},
    "th17": {"fixed": 12, "variable": 6, "sizeField": 8, "shape": "fixed", "peak": 0x04},
    "th18": {"fixed": 12, "variable": 109, "sizeField": 113, "shape": "variable", "peak": 0x06},
}
ARG_BASE = 0x08        # measured identical in all six titles

# Instruction shapes that reveal the advance. Each is a byte pattern, not an address, so the measurement is
# independent of where the function sits: a search for an address would only find the one function it names.
FIXED = [b"\x8d\x47\x10",              # lea eax, [edi + 0x10]
         b"\x83\xc7\x10"]              # add edi, 0x10


def text_bytes(path):
    img = Image(path)
    name, base, size, raw_off, raw_size = next(s for s in img.sections if s[0] == ".text")
    with open(path, "rb") as handle:
        handle.seek(raw_off)
        return handle.read(raw_size), base, img


def count_fixed(code):
    return sum(code.count(p) for p in FIXED)


def count_variable(code):
    """`movzx r32, word ptr [edi + 2]` - the load of the instruction's own length word.

    Matching the whole instruction by shape rather than by a fixed destination register matters: the destination
    varies between sites, and `add edx, edi` (the following instruction) is far too generic to count - it occurs
    throughout the image and inflated the first measurement to twice the truth.
    """
    n = 0
    for i in range(len(code) - 4):
        if code[i] == 0x0F and code[i + 1] == 0xB7 and (code[i + 2] & 0xC7) == 0x47 and code[i + 3] == 0x02:
            n += 1
    return n


def operand_histogram(code):
    """Offsets a handler reads out of the instruction pointer, so the operand base is measured.

    The header ends where a rising run of reads begins. Measured on all six titles this is `+0x08` everywhere,
    which is what pins the first argument: a handler reads `[edi + 8]` for its first operand and `[edi + 0xc]`
    for its second. The peak below that separates the groups - the fixed titles peak at the time word, and the
    variable ones peak at the parameter mask byte at `+0x06`, which their handlers test explicitly.
    """
    hist = {}
    prefixes = (b"\x8b", b"\x0f\xb6", b"\x0f\xb7", b"\x0f\xbf", b"\xf6", b"\xd9", b"\xd8")
    for i in range(len(code) - 6):
        for prefix in prefixes:
            if not code.startswith(prefix, i):
                continue
            m = code[i + len(prefix)]
            if (m & 0xC7) == 0x47:
                at = code[i + len(prefix) + 1]
                hist[at] = hist.get(at, 0) + 1
            break
    base = min([k for k, v in hist.items() if k >= 8 and v >= 20], default=None)
    peak = max(hist.items(), key=lambda kv: kv[1])[0] if hist else None
    return {"argBase": base, "peak": peak}


def size_field_reads(code):
    """How often a handler reads the byte at `[edi + 2]`, the field that would hold an instruction's own length.

    This is the independent half of the measurement. The advance shape says how the pointer moves; this says
    whether the second word of the instruction is read as a field at all. They agree title by title, which is
    what makes the layout a result rather than a guess: a title where `[edi + 2]` is read a hundred times is
    unlikely to be reading padding, and one that never reads it cannot be variable-length.
    """
    n = 0
    prefixes = (b"\x8b", b"\x0f\xb6", b"\x0f\xb7", b"\x0f\xbf", b"\xf6", b"\xd9", b"\xd8")
    for i in range(len(code) - 6):
        for prefix in prefixes:
            if not code.startswith(prefix, i):
                continue
            m = code[i + len(prefix)]
            if (m & 0xC7) == 0x47 and code[i + len(prefix) + 1] == 0x02:
                n += 1
            break
    return n


def measure(title):
    code, base, img = text_bytes(EXES[title])
    size_field = size_field_reads(code)
    variable = count_variable(code)
    got = {
        "fixed": count_fixed(code),
        "variable": variable,
        "sizeField": size_field,
        # Variable-length only when both instruments agree: the pointer advances by a length read out of the
        # instruction, and handlers actually read that field. Either alone can be coincidence.
        "shape": "variable" if variable > 0 and size_field >= 32 else "fixed",
    }
    got.update(operand_histogram(code))
    return got


def loop_header(title):
    """The opcode offset and the time offset, read from the dispatcher loop that reloads the pointer.

    Both titles read the opcode at +0 and the time word at +4; this exists so the claim "the instruction
    starts with the opcode" is checked on every title rather than asserted for one and assumed for the rest.
    """
    code, base, img = text_bytes(EXES[title])
    # `8b 7b 28` = mov edi, [ebx + 0x28]  followed by the first field read out of edi.
    for at in range(len(code) - 24):
        if code[at:at + 3] != b"\x8b\x7b\x28":
            continue
        nxt = code[at + 3:at + 24]
        fields = []
        for k in range(len(nxt) - 3):
            if nxt[k] == 0x0F and nxt[k + 1] == 0xBF:      # movsx r32, word ptr [edi + disp8]
                fields.append(nxt[k + 3])
            elif nxt[k] == 0x0F and nxt[k + 1] == 0xB7:
                fields.append(nxt[k + 3])
        if fields:
            return {"va": img.va_of(0) and base + at, "fields": fields[:3]}
    return {"va": None, "fields": []}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--historical", action="store_true")
    args = ap.parse_args()
    if not args.historical or args.check:
        ap.error('retired: ANM/ECL domain confusion invalidates these format claims; use node tools/th-ecl-port-check.mjs --all')
    print('HISTORICAL INVALID MEASUREMENTS: do not use these numbers as an ECL format specification.')

    bad = 0
    for title, path in EXES.items():
        if not Path(path).is_file():
            print("  %s: SKIP (no executable at %s)" % (title, path))
            continue
        got = measure(title)
        shape = got["shape"]
        want = RECORDED.get(title)
        note = ""
        if want is not None:
            problems = []
            if want["fixed"] != got["fixed"]: problems.append("fixed %d != %d" % (got["fixed"], want["fixed"]))
            if want["variable"] != got["variable"]: problems.append("variable %d != %d" % (got["variable"], want["variable"]))
            if want.get("sizeField") is not None and want["sizeField"] != got["sizeField"]:
                problems.append("sizeField %d != %d" % (got["sizeField"], want["sizeField"]))
            if want.get("shape") is not None and want["shape"] != shape:
                problems.append("shape %s != %s" % (shape, want["shape"]))
            if want.get("peak") is not None and want["peak"] != got["peak"]:
                problems.append("peak +0x%02x != +0x%02x" % (got["peak"], want["peak"]))
            if got["argBase"] != ARG_BASE:
                problems.append("argBase +0x%02x != +0x%02x" % (got["argBase"], ARG_BASE))
            if problems:
                bad += 1
                note = "  <-- FAIL: " + "; ".join(problems)
        print("  %s: fixed=%d variable=%d sizeFieldReads=%d argBase=%s peak=%s  -> %s-length%s"
              % (title, got["fixed"], got["variable"], got["sizeField"],
                 ('+0x%02x' % got["argBase"]) if got["argBase"] is not None else 'n/a',
                 ('+0x%02x' % got["peak"]) if got["peak"] is not None else 'n/a',
                 shape, note))
    if args.check:
        sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
