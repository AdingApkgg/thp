"""Record the TH12 laser layout that the executable shows, and check the port against it.

    py -3 tools/th-laser-layout.py            # derive the anchors and write docs/porting/laser-layout.json
    py -3 tools/th-laser-layout.py --check    # fail if the document no longer matches the executable

The laser command family 0x25c..0x262 finds an object by id and then writes into it at fixed offsets, so the
transcription depends on knowing where those fields live in TH12. Three functions settle it, and all three are read
from the executable rather than assumed:

  0x412960  walks the laser list matching `[object + D] == id`, which makes D the id field
  0x412900  copies three dwords to `[object + D]`.., a vector
  0x412920  stores one float at `[object + D]`

TH12's answers disagree with the port's LaserState, which is inherited from TH11 and measured at 0x440 bytes with its
id at 0x6c. The offsets TH12 uses reach 0x470, so TH12's laser cannot be 0x440 bytes, and its id cannot be at 0x6c.
That is not a transcription bug to guess around: the family cannot be written faithfully until TH12's laser layout is
rebuilt, and this document exists so the gap is a measurement rather than a suspicion. `agreesWithPort` is what a
future round flips, and the check fails when any derived anchor changes, so the record cannot rot.
"""
import argparse
import json
import struct
import sys
from pathlib import Path

import capstone

REPO = Path(__file__).resolve().parent.parent
EXECUTABLE = Path("H:/Games/th/12/th12.exe")
OUT = REPO / "docs/porting/laser-layout.json"
ANCHORS = {
    # address -> (meaning, mnemonic to read, smallest displacement that is the field rather than an argument load)
    "0x412960": ("id compared while walking the list", "cmp", 0x40),
    "0x412900": ("three dwords copied, a vector", "mov", 0x100),
    "0x412920": ("one float stored", "fstp", 0x100),
}
# Measured from the port by tests/cpp/probe-laser-offsets.mjs, which asks the built runtime for offsetof rather than
# reading the declaration order.
PORT = {"sizeof": 0x440, "id": 0x6c, "motion": 0x70}
IDS = {"th12": "id"}


def sections(image):
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


def derive():
    image = EXECUTABLE.read_bytes()
    base, sects = sections(image)
    disassembler = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
    found = {}
    for text, (meaning, mnemonic, minimum) in ANCHORS.items():
        address = int(text, 16)
        rva = address - base
        pointer = [raw + rva - srva for srva, raw, span in sects if srva <= rva < srva + span][0]
        offsets = []
        for instruction in disassembler.disasm(image[pointer:pointer + 0x60], address):
            # Stop at the function's end instead of running into its neighbour: the window used to include the next
            # function and read its displacements as if they belonged here.
            if instruction.mnemonic.startswith("ret") or instruction.mnemonic == "int3":
                break
            if instruction.mnemonic != mnemonic:
                continue
            for match in __import__("re").finditer(r"\+ (0x[0-9a-f]+)\]", instruction.op_str):
                value = int(match.group(1), 16)
                if value >= minimum:
                    offsets.append(value)
        if not offsets:
            print("  FAIL %s: no displacement found in %s - the address or the executable changed" % (text, meaning))
            sys.exit(1)
        found[text] = {"meaning": meaning, "offsets": sorted(set(offsets))}
    highest = max(o for row in found.values() for o in row["offsets"])
    return found, highest, spawn_size(image, base, sects, disassembler)


SPAWN = 0x41BB40
ALLOCATOR = 0x46C9EA


def spawn_size(image, base, sects, disassembler):
    """The size the spawn function asks for, which is the laser object's size.

    0x41bb40 checks the manager's count against 0x100 and its id counter against 0x10000 - the same capacity and id
    floor the port's LaserManager carries - and then allocates the object with `push <size> ; call 0x46c9ea`. Reading
    that immediate is what makes TH12's laser 0xfa4 bytes instead of a number inferred from field offsets.
    """
    rva = SPAWN - base
    pointer = [raw + rva - srva for srva, raw, span in sects if srva <= rva < srva + span][0]
    instructions = list(disassembler.disasm(image[pointer:pointer + 0x200], SPAWN))
    for index, instruction in enumerate(instructions):
        if instruction.mnemonic != "push" or not instruction.op_str.startswith("0x"):
            continue
        size = int(instruction.op_str, 16)
        if size < 0x100:
            continue
        for following in instructions[index + 1:index + 4]:
            if following.mnemonic == "call" and following.op_str == "0x%x" % ALLOCATOR:
                return size
    print("  FAIL 0x%x: no allocation size found before the allocator call" % SPAWN)
    sys.exit(1)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    found, highest, size = derive()
    document = {
        "source": "displacements read from th12.exe by tools/th-laser-layout.py",
        "anchors": found,
        "objectSize": "0x%x" % size,
        "highestOffsetTouched": "0x%x" % highest,
        "minimumSizeImplied": "0x%x" % (highest + 4),
        "port": {"sizeof": "0x%x" % PORT["sizeof"], "id": "0x%x" % PORT["id"], "motion": "0x%x" % PORT["motion"], "lineSize": "0xe8c", "infiniteSize": "0xeb0",
                 "measuredBy": "tests/cpp/probe-laser-offsets.mjs"},
        "agreesWithPort": size == PORT["sizeof"] and PORT["id"] == found["0x412960"]["offsets"][-1],
        "why": ("TH12 reaches 0x%x, so its LaserState is at least 0x%x bytes; the port's is 0x%x with its id at 0x%x. "
                "The 0x25c..0x262 family writes position, speed and width fields whose TH12 offsets therefore have no "
                "counterpart in the port's struct, and guessing them would put the writes on the wrong fields. The "
                "family waits on rebuilding TH12's laser layout."
                % (highest, highest + 4, PORT["sizeof"], PORT["id"])),
    }
    text = json.dumps(document, indent=1, sort_keys=True) + "\n"
    if args.check:
        if not OUT.exists() or OUT.read_text(encoding="utf-8") != text:
            print("  FAIL %s is stale - rerun tools/th-laser-layout.py" % OUT.relative_to(REPO))
            sys.exit(1)
        print("  th12 laser: offsets reach 0x%x, port sizeof 0x%x, id port 0x%x vs th12 0x%x, agrees=%s"
              % (highest, PORT["sizeof"], PORT["id"], found["0x412960"]["offsets"][-1], document["agreesWithPort"]))
        sys.exit(0)
    OUT.write_text(text, encoding="utf-8", newline="\n")
    print("  wrote %s" % OUT.relative_to(REPO))
    print("  th12 laser object 0x%x bytes, offsets reach 0x%x, port sizeof 0x%x, agrees=%s" % (size, highest, PORT["sizeof"], document["agreesWithPort"]))


if __name__ == "__main__":
    main()
