"""Which functions are byte-identical to a given one once every in-image operand is masked?

The shape guard of section 91 compares one site with one twin. This is the same guard as a class search,
which is the question the four `spawn mode` rows need: they are byte-identical to each other apart from
their literals, so tools/th-twin-find.py collapsed them onto one candidate and the rows were withdrawn,
and the call graph cannot separate them either - `--derive-calls` over all 147 anchored bases derived
none of them, because every caller of that cluster is itself unanchored. What remains is the class: a
th12 function whose masked bytes equal the th11 function's is a twin, and if the class has four members
on both sides the set is settled even where the bijection is not.

The first version of this tool - section 97.3 - recomputed the wildcards on each side from that side's own
section ranges, so a dword that looks like an address in th11 may not look like one in th12 and the two
masked windows were compared at different byte positions. It reported zero members for every spawn
function, and that zero was the instrument's, not the image's. The wildcards are the source's; the target
window is masked at exactly those positions. This is the same mistake `pattern_and_wild` in
tools/th-twin-batch.py avoids, and section 98.2 records it.

  py -3 tools/th-shape-classes.py --source H:/Games/th/11/th11.exe --at 0x455a00 \
      --target H:/Games/th/12/th12.exe --span 48
"""
import argparse
import io
import re
import struct

import capstone

_ARGS = argparse.ArgumentParser()
_ARGS.add_argument('--source', required=True)
_ARGS.add_argument('--at', required=True)
_ARGS.add_argument('--target', required=True)
_ARGS.add_argument('--span', type=lambda text: int(text, 0), default=48)
_ARGS.add_argument('--limit', type=lambda text: int(text, 0), default=24)
_OPTS = _ARGS.parse_args()

MD = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
MD.detail = True


def image(image):
    """Return (blob, base, ranges) for the executable section, with the ranges of every section."""
    data = io.open(image, 'rb').read()
    pe = struct.unpack_from('<I', data, 0x3c)[0]
    count = struct.unpack_from('<H', data, pe + 6)[0]
    header = struct.unpack_from('<H', data, pe + 20)[0]
    base = struct.unpack_from('<I', data, pe + 0x34)[0]
    text, text_base, ranges = None, None, []
    for index in range(count):
        offset = pe + 24 + header + index * 40
        name = data[offset:offset + 8].rstrip(b'\x00').decode('latin1')
        virtual_size, va, raw_size, raw = struct.unpack_from('<IIII', data, offset + 8)
        # The wildcard test needs the MAPPED range, not the raw one: th11's .data has references above
        # its raw_size (0x4c3268 is one), and with raw_size only, a window whose first instruction reads a
        # global reported zero wildcarded bytes and then demanded the global's address match th12's - so
        # every "target class: 0 members" was the instrument's verdict, not the image's. Section 98.3.
        if virtual_size or raw_size:
            ranges.append((base + va, base + va + max(virtual_size, raw_size)))
        if name == '.text' and raw_size:
            text, text_base = data[raw:raw + raw_size], base + va
    return text, text_base, ranges


def wildcards(window, ranges, address):
    """Byte positions that belong to an operand the translation is allowed to move.

    Two rules, and the second one is section 98.5's finding. An in-image dword is an absolute reference
    (a call displacement into .text, a pointer into .data) and moves between titles - that is the rule the
    table was built with. A MEM operand with a base or index register and a non-zero displacement is a
    field offset into a structure, and it moves too: 0x455760's `mov esi, dword ptr [edx + 0x7b562c]` is
    0x4612d0's `mov esi, dword ptr [edx + 0x8856b8]`. The byte-level rule did not mask those, so it
    demanded they match and reported no twin at all, while the shape-level rule in tools/th-twin-batch.py
    counts them as the same operand kind and reported paired 1.000 over 27/27 instructions. Both cannot be
    the instrument; the displacement is taken as an operand here.
    """
    flags = bytearray(len(window))
    for index in range(len(window) - 3):
        value = struct.unpack_from('<I', window, index)[0]
        if any(low <= value < high for low, high in ranges):
            flags[index:index + 4] = b'\x01\x01\x01\x01'
    for insn in MD.disasm(bytes(window), address):
        for operand in insn.operands:
            if operand.type != capstone.x86.X86_OP_MEM or operand.mem.disp == 0:
                continue
            if not (operand.mem.base or operand.mem.index):
                continue
            # Only a LARGE displacement: a small one is a field offset inside a structure, which the
            # table's own rule keeps as a literal - the anchored row for 0x401fd0 records 48 literal bytes
            # in a 48-byte window, i.e. no wildcards at all. The first version of this rule masked every
            # non-zero disp32 and reported 23 of 48 bytes wildcarded on that same window, which is how the
            # self-check caught the fourth fix being a defect in turn. Section 98.8.
            if abs(operand.mem.disp) < 0x10000:
                continue
            # The disp32 is the trailing field of a [base + disp32] encoding.
            start = insn.address - address + insn.size - 4
            if start >= 0:
                flags[start:start + 4] = b'\x01\x01\x01\x01'
    return flags


def masked(blob, base, address, span, flags):
    window = bytearray(blob[address - base:address - base + span])
    for index, flag in enumerate(flags):
        if flag:
            window[index] = 0
    return bytes(window)


def entries(blob, base):
    """Every address of the section that a linear sweep reaches, i.e. a real instruction boundary.

    The first version searched only call targets plus int3-padded entries. That is not the candidate
    universe: a function reached only through an indirect call or a jump table need not be a call target
    and need not be preceded by padding, so `target class: 0 members` was again the instrument's verdict
    rather than the image's. Section 91's alignment rule is the guard - a window may only start where a
    sweep makes the address an instruction boundary - and here it filters a whole-section byte scan.
    """
    boundaries = set()
    address = base
    end = base + len(blob)
    while address < end:
        boundaries.add(address)
        stream = next(MD.disasm(blob[address - base:address - base + 16], address, count=1), None)
        if stream is None:
            address += 1
        else:
            address += stream.size
    return boundaries


source_text, source_base, source_ranges = image(_OPTS.source)
target_text, target_base, _ = image(_OPTS.target)
at = int(_OPTS.at, 16)
source_window = source_text[at - source_base:at - source_base + _OPTS.span]
flags = wildcards(source_window, source_ranges, at)
wanted = masked(source_text, source_base, at, _OPTS.span, flags)
print('  %s 0x%x: %d of %d bytes wildcarded, masked window %s'
      % (_OPTS.source, at, sum(flags), len(flags), wanted.hex()[:48] + '...'))

# The wildcarded bytes are the source's, so the search is a regex over the whole section: a byte scan is
# what makes this a class search rather than an entry-list lookup, and at 600 KB it is also the only
# affordable way to do it.
pattern = b''.join(b'.' if flag else re.escape(bytes([byte]))
                   for byte, flag in zip(source_window, flags))


def sweep(blob, base, ranges):
    found = [match.start() + base for match in re.finditer(pattern, blob, re.DOTALL)]
    boundaries = entries(blob, base)
    return sorted(address for address in found if address in boundaries)


print('  source class: %d members' % len(sweep(source_text, source_base, source_ranges)))
for address in sweep(source_text, source_base, source_ranges)[:_OPTS.limit]:
    print('    0x%x' % address)

target_class = sweep(target_text, target_base, None)
print('  target class: %d members' % len(target_class))
for address in target_class[:_OPTS.limit]:
    stream = list(MD.disasm(target_text[address - target_base:address - target_base + 16], address))
    first = '%s %s' % (stream[0].mnemonic, stream[0].op_str) if stream else '<no instruction>'
    print('    0x%x  %s' % (address, first))
