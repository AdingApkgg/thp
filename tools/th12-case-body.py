#!/usr/bin/env python3
"""Resolve TH12 ECL opcodes to their original case body, and disassemble it.

An opcode does not map to a case body by a single table. FUN_004154d0 computes

    ecx   = opcode - 0x100            (range 0x100..0x263)
    index = byte[0x419890 + ecx]      ; byte table
    goto  [0x419654 + index*4]        ; jump table

so the jump table is indexed by the *byte table's output*, not by the opcode. Reading
[0x419654 + (opcode-0x100)*4] directly looks plausible and is wrong: it returns the
byte table's own bytes as if they were pointers, and it silently lands on another
opcode's case. That mistake was made by hand in round 26 and produced a body belonging
to opcode 411 instead of 308.

docs/th12/ecl-case-bodies.json already carries the reverse map (each case address lists
the opcodes that reach it), and tools/th12-ecl-case-map.mjs --check keeps it honest, so
this tool reads that instead of re-deriving the tables.

The stop point is the *next* case address, not the first `jmp 0x41962b`. A body can
contain more than one return path - opcode 309 has a `jg` that continues past a shared
epilogue jump - so breaking at the first epilogue jump truncates the body and invites a
wrong conclusion about what the case does. Slicing at the next case address keeps the
whole body, and epilogue jumps are annotated rather than treated as the end.

Usage:
    python tools/th12-case-body.py 308 513
    TH12_EXE=/path/th12.exe python tools/th12-case-body.py 0x134
"""

import json
import os
import pathlib
import re
import sys

from capstone import CS_ARCH_X86, CS_MODE_32, Cs

ROOT = pathlib.Path(__file__).resolve().parent.parent
DEFAULT_EXE = pathlib.Path(r"H:\Games\th\12\th12.exe")
# .text: rva 0x1000, raw 0x400. va2off(va) = raw + (va - 0x400000 - rva).
TEXT_RVA, TEXT_RAW = 0x1000, 0x400
EPILOGUE = 0x41962B
WINDOW = 0x400


def va2off(va):
    return TEXT_RAW + (va - 0x400000 - TEXT_RVA)


def load_reverse_map():
    path = ROOT / "docs/th12/ecl-case-bodies.json"
    bodies = json.loads(path.read_text(encoding="utf-8"))["bodies"]
    by_opcode = {}
    for va_text, body in bodies.items():
        for opcode in body.get("opcodes", []):
            by_opcode[opcode] = {
                "va": int(va_text, 16),
                "file": body.get("file"),
                "shared_with": body.get("opcodes", []),
            }
    return by_opcode, sorted({int(va, 16) for va in bodies})


def parse_opcode(text):
    text = text.strip()
    return int(text, 16) if text.lower().startswith("0x") else int(text, 10)


def stop_for(va, case_addresses):
    for address in case_addresses:
        if address > va:
            return min(address, va + WINDOW)
    return va + WINDOW


def disassemble(exe, va, stop):
    md = Cs(CS_ARCH_X86, CS_MODE_32)
    code = exe[va2off(va):va2off(stop)]
    lines = []
    for ins in md.disasm(code, va):
        lines.append(f"  0x{ins.address:08x}  {ins.mnemonic:<8} {ins.op_str}")
        if re.fullmatch(r"jmp\s+0x41962b", f"{ins.mnemonic} {ins.op_str}"):
            lines.append("  ^ shared epilogue: one return path, not necessarily the end")
    return lines


def main():
    if len(sys.argv) < 2:
        print(__doc__.strip())
        return 2
    exe_path = pathlib.Path(os.environ.get("TH12_EXE", DEFAULT_EXE))
    if not exe_path.exists():
        print(f"th12.exe not found at {exe_path}; set TH12_EXE", file=sys.stderr)
        return 1
    exe = exe_path.read_bytes()
    by_opcode, case_addresses = load_reverse_map()

    for argument in sys.argv[1:]:
        opcode = parse_opcode(argument)
        entry = by_opcode.get(opcode)
        print(f"=== opcode {opcode} (0x{opcode:x}) ===")
        if entry is None:
            print("  no case body recorded (unused, or refused before dispatch)")
            continue
        stop = stop_for(entry["va"], case_addresses)
        print(f"  case VA 0x{entry['va']:x}  exe offset {entry['file']}  "
              f"shared with opcodes {entry['shared_with']}  body ends 0x{stop:x}")
        for line in disassemble(exe, entry["va"], stop):
            print(line)
    return 0


if __name__ == "__main__":
    sys.exit(main())
