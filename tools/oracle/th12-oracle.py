"""Run th12.exe's own machine code locally, so a ported function can be checked against the original.

    py -3 tools/oracle/th12-oracle.py --selftest
    py -3 tools/oracle/th12-oracle.py --rng-steps 8 --seed 60128 --out tools/tmp/oracle-rng.json

Same conventions the rules already use: an implementation is either known port code or an original routine
disassembled from this executable, and a disagreement stops the work rather than being averaged away. The oracle
takes no view on which is right - it is the original's side of the comparison, and it is only usable once it has
been checked against a function whose behaviour is already known, which is what --selftest does: it runs the
engine RNG out of the executable and compares it with the mixer written out from the disassembly in section 22.

Register convention note: the engine RNG takes its object pointer in esi rather than on the stack, which is what
the call sites in the executable set up before entering 0x4643d0. The oracle therefore takes an optional esi, and
the RNG wrappers below pass the fake object that way.
"""
import argparse
import json
import struct
import sys
from pathlib import Path

from unicorn import Uc, UC_ARCH_X86, UC_MODE_32, UC_HOOK_CODE, UC_PROT_ALL
from unicorn.x86_const import (
    UC_X86_REG_EAX, UC_X86_REG_AX, UC_X86_REG_EBP, UC_X86_REG_EBX, UC_X86_REG_ECX,
    UC_X86_REG_EDI, UC_X86_REG_EDX, UC_X86_REG_EIP, UC_X86_REG_ESI, UC_X86_REG_ESP,
)

EXE = Path("H:/Games/th/12/th12.exe")
IMAGE_BASE = 0x400000
HEAP = 0x600000
STACK = 0x700000
PAGE = 0x1000

# The engine RNG, transcribed in section 22 and re-read here so the self-test is not just a copy of the port.
RNG_ENTRY = 0x4643d0


def sections(data):
    lfanew = struct.unpack_from("<I", data, 0x3C)[0]
    count = struct.unpack_from("<H", data, lfanew + 6)[0]
    opt = struct.unpack_from("<H", data, lfanew + 0x14)[0]
    table = lfanew + 0x18 + opt
    out = []
    for i in range(count):
        o = table + i * 40
        name = data[o:o + 8].split(b"\0")[0].decode("ascii", "replace")
        vsize, rva, raw_size, raw = struct.unpack_from("<IIII", data, o + 8)
        out.append((name, rva, vsize, raw, raw_size))
    return out


class Oracle:
    def __init__(self, exe=EXE):
        self.data = Path(exe).read_bytes()
        self.sections = sections(self.data)
        self.image_size = max(rva + max(vsize, raw_size) for _, rva, vsize, _, raw_size in self.sections)
        self.image_size = (self.image_size + 0xFFFF) & ~0xFFFF
        self.uc = Uc(UC_ARCH_X86, UC_MODE_32)
        self.uc.mem_map(IMAGE_BASE, self.image_size, UC_PROT_ALL)
        self.uc.mem_write(IMAGE_BASE, self.data[:0x400])
        for name, rva, vsize, raw, raw_size in self.sections:
            if raw_size:
                self.uc.mem_write(IMAGE_BASE + rva, self.data[raw:raw + raw_size])
        self.uc.mem_map(HEAP, 0x100000, UC_PROT_ALL)
        self.uc.mem_map(STACK, 0x100000, UC_PROT_ALL)
        self.heap = HEAP
        self.stack = STACK + 0xF000
        self.return_sentinel = HEAP + 0xF000
        self.uc.mem_write(self.return_sentinel, b"\xf4")
        self.instructions = 0
        self.trace = None

    def alloc(self, size, align=16):
        address = (self.heap + align - 1) & ~(align - 1)
        self.heap = address + size
        return address

    def function_start(self, va, limit=0x200):
        """Walk back over the int3 padding that separates functions, reading the mapped image rather than the file:
        .text's raw offset and its virtual one differ, and the mapping is the authority."""
        address = va
        while address > IMAGE_BASE and address - va < limit and self.read(address - 1, 1)[0] == 0xCC:
            address -= 1
        while self.read(address, 1)[0] == 0xCC:
            address += 1
        return address

    def call(self, va, args=(), esi=None, ecx=None, edx=None, steps=20000, trace=0):
        """Call one routine with edx:ecx/system-style args on the stack and optional register setup."""
        uc = self.uc
        esp = self.stack
        for value in reversed(list(args)):
            esp -= 4
            uc.mem_write(esp, struct.pack("<I", value & 0xFFFFFFFF))
        esp -= 4
        uc.mem_write(esp, struct.pack("<I", self.return_sentinel))
        uc.reg_write(UC_X86_REG_ESP, esp)
        uc.reg_write(UC_X86_REG_EBP, self.stack)
        for reg, value in ((UC_X86_REG_ESI, esi), (UC_X86_REG_ECX, ecx), (UC_X86_REG_EDX, edx)):
            if value is not None:
                uc.reg_write(reg, value & 0xFFFFFFFF)
        self.instructions = 0
        self.trace = []
        handle = None

        def on_code(u, address, size, user):
            self.instructions += 1
            if trace and len(self.trace) < trace:
                self.trace.append(address)

        if trace:
            handle = uc.hook_add(UC_HOOK_CODE, on_code)
        try:
            uc.emu_start(va, self.return_sentinel, count=steps)
        finally:
            if handle is not None:
                uc.hook_del(handle)
        return uc.reg_read(UC_X86_REG_AX), uc.reg_read(UC_X86_REG_EAX)

    # --- memory helpers ---------------------------------------------------------------------------------
    def write(self, address, blob):
        self.uc.mem_write(address, blob)

    def read(self, address, size):
        return self.uc.mem_read(address, size)

    def u16(self, address):
        return struct.unpack("<H", self.read(address, 2))[0]

    def put_u16(self, address, value):
        self.write(address, struct.pack("<H", value & 0xFFFF))

    def u32(self, address):
        return struct.unpack("<I", self.read(address, 4))[0]

    def put_u32(self, address, value):
        self.write(address, struct.pack("<I", value & 0xFFFFFFFF))

    def rng(self, seed, calls=0):
        """A fake engine RNG object: seed at +0, call counter at +4, exactly the layout the machine code uses."""
        obj = self.alloc(8)
        self.put_u16(obj, seed)
        self.put_u16(obj + 2, 0)
        self.put_u32(obj + 4, calls)
        return obj


# The two-draw variant, an interior entry in the same cluster. --rng32-steps calls it so next32 can be checked too.
RNG32_ENTRY = 0x4644fd


def reference_next32(seed, calls):
    """Section 22's reading of the two-draw variant, used to check the oracle ran the right routine."""
    first = ((seed ^ 0x9630) - 0x6553) & 0xFFFF
    seed = ((first << 2) | (first >> 14)) & 0xFFFF
    second = ((seed ^ 0x9630) - 0x6553) & 0xFFFF
    seed = ((second << 2) | (second >> 14)) & 0xFFFF
    return seed, calls + 2, ((first << 16) | second) & 0xFFFFFFFF


def reference_next16(seed, calls):
    """The mixer written out of section 22, used only to check that the oracle really ran the routine."""
    mixed = ((seed ^ 0x9630) - 0x6553) & 0xFFFF
    seed = ((mixed << 2) | (mixed >> 14)) & 0xFFFF
    return seed, calls + 1


def selftest():
    oracle = Oracle()
    entry = oracle.function_start(RNG_ENTRY)
    print(f"  engine RNG entry: 0x{entry:06x} (from 0x{RNG_ENTRY:06x} walked back over padding)")
    bad = 0
    steps = 6
    for start in (0x0000, 0x0001, 0x1234, 0xEAE0, 0x749B, 0xFFFF):
        seed, calls = start, 0
        tag = f"seed 0x{start:04x}"
        agreed = 0
        for step in range(steps):
            obj = oracle.rng(seed, calls)
            ax, eax = oracle.call(entry, esi=obj, trace=8 if step == 0 else 0)
            oracle_seed, oracle_calls = oracle.u16(obj), oracle.u32(obj + 4)
            seed, calls = reference_next16(seed, calls)
            if (oracle_seed, oracle_calls, ax) != (seed, calls, seed):
                bad += 1
                print(f"    {tag} step {step}: oracle seed=0x{oracle_seed:04x} calls={oracle_calls} ax=0x{ax:04x} "
                      f"vs reference 0x{seed:04x}/{calls}")
            else:
                agreed += 1
            seed, calls = oracle_seed, oracle_calls
        print(f"    {tag}: {agreed} of {steps} steps agree")
    if bad:
        print(f"  FAIL: the oracle and the written-out mixer disagree on {bad} steps")
        return 1
    print("  PASS: the oracle runs the executable's own engine RNG and returns exactly the written-out mixer")
    return 0


def rng32_sequence(seed, steps, calls=0):
    oracle = Oracle()
    entry = oracle.function_start(RNG32_ENTRY)
    out = []
    obj = oracle.rng(seed, calls)
    for _ in range(steps):
        ax, eax = oracle.call(entry, esi=obj)
        seed, calls = oracle.u16(obj), oracle.u32(obj + 4)
        out.append({"seed": seed, "calls": calls, "value": eax})
    return entry, out


def rng_sequence(seed, steps, calls=0):
    oracle = Oracle()
    entry = oracle.function_start(RNG_ENTRY)
    out = []
    obj = oracle.rng(seed, calls)
    for _ in range(steps):
        ax, eax = oracle.call(entry, esi=obj)
        seed, calls = oracle.u16(obj), oracle.u32(obj + 4)
        out.append({"seed": seed, "calls": calls, "ax": ax})
    return out


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--selftest", action="store_true")
    parser.add_argument("--rng-steps", type=int, default=0)
    parser.add_argument("--rng32-steps", type=int, default=0)
    parser.add_argument("--seed", type=lambda s: int(s, 0), default=0)
    parser.add_argument("--out")
    args = parser.parse_args()
    if args.selftest:
        return selftest()
    if args.rng32_steps:
        entry, steps = rng32_sequence(args.seed, args.rng32_steps)
        payload = {"function": "engine RNG next32", "entry": f"0x{entry:06x}", "seed": args.seed, "steps": steps}
        if args.out:
            Path(args.out).write_text(json.dumps(payload, indent=1))
            print(f"  wrote {len(steps)} two-draw steps to {args.out}")
        else:
            print(json.dumps(payload, indent=1))
        return 0
    if args.rng_steps:
        steps = rng_sequence(args.seed, args.rng_steps)
        payload = {"function": "engine RNG next16", "entry": f"0x{RNG_ENTRY:06x}", "seed": args.seed, "steps": steps}
        if args.out:
            Path(args.out).write_text(json.dumps(payload, indent=1))
            print(f"  wrote {len(steps)} steps to {args.out}")
        else:
            print(json.dumps(payload, indent=1))
        return 0
    parser.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())
