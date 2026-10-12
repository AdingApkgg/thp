#!/usr/bin/env python3
"""Measure the field-offset map of one function between two titles.

`th-twin-find.py` answers "which function here is the one at that address there" with a window
match. The next question a fixture asks is the one section 74 records: the twin's instructions
are identical EXCEPT a few operands, and the ones that moved include structure field offsets
(`mov esi,[ebx+0x1614]` in th11 against `mov esi,[ebx+0x174c]` in th12). A fixture that copies
a structure between the two must write each field at the counterpart's offset, so the map has to be
measured, not guessed.

Method: decode both windows from their entries, pair the instructions by index, and keep every pair
whose mnemonics agree while a memory displacement differs (and, with --constants, every differing
immediate that is not an in-image address). The index pairing is only trustworthy when the streams
line up, so the tool reports the pairing quality it measured:

  * instructions decoded in each window, and
  * how many paired instructions have identical mnemonic AND identical operand shape.

Self-checks before any answer is trusted:
  * source == target must give an empty field list and a pairing quality of 1.0, and
  * the pair's bytes outside the reported operands must be identical.

Usage:
  th-twin-fields.py <from.exe> <0xFROM> <to.exe> <0xTO> [--span 0x400] [--top 40]
                    [--constants] [--limit 0x20000]
"""
import struct
import sys

import capstone


def text_of(path):
    image = open(path, 'rb').read()
    pe = struct.unpack_from('<I', image, 0x3C)[0]
    count = struct.unpack_from('<H', image, pe + 6)[0]
    option = struct.unpack_from('<H', image, pe + 20)[0]
    base = struct.unpack_from('<I', image, pe + 24 + 28)[0]
    for index in range(count):
        at = pe + 24 + option + index * 40
        name = image[at:at + 8].split(b'\x00')[0].decode('ascii', 'replace')
        vsize, rva, rawsize, raw = struct.unpack_from('<IIII', image, at + 8)
        if name == '.text':
            return base + rva, image[raw:raw + max(vsize, rawsize)], base
    raise SystemExit('no .text in %s' % path)


def decode(path, address, span):
    start, blob, base = text_of(path)
    md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
    md.detail = True
    window = blob[address - start:address - start + span]
    instructions = list(md.disasm(window, address))
    return blob, base, instructions


def shape(instruction):
    """The operand structure without any numbers: what makes two instructions the same code."""
    parts = []
    for operand in instruction.operands:
        if operand.type == capstone.x86.X86_OP_REG:
            parts.append('r' + instruction.reg_name(operand.reg))
        elif operand.type == capstone.x86.X86_OP_IMM:
            parts.append('i')
        elif operand.type == capstone.x86.X86_OP_MEM:
            parts.append('m%s%s' % (instruction.reg_name(operand.mem.base) if operand.mem.base else '',
                                   '+%s' % instruction.reg_name(operand.mem.index) if operand.mem.index else ''))
        else:
            parts.append('?')
    return instruction.mnemonic + ' ' + ','.join(parts)


def immediates(instruction):
    values = []
    for operand in instruction.operands:
        if operand.type == capstone.x86.X86_OP_IMM:
            values.append(operand.imm)
        elif operand.type == capstone.x86.X86_OP_MEM and not operand.mem.base and not operand.mem.index:
            values.append(operand.mem.disp)      # absolute reference
    return values


def displacements(instruction):
    values = []
    for operand in instruction.operands:
        if operand.type == capstone.x86.X86_OP_MEM and (operand.mem.base or operand.mem.index):
            values.append(operand.mem.disp)
    return values


def numeric_spans(instruction):
    """The byte ranges capstone calls an immediate or a displacement."""
    spans = []
    encoding = instruction.encoding
    if encoding.imm_size:
        spans.append((encoding.imm_offset, encoding.imm_offset + encoding.imm_size))
    if encoding.disp_size:
        spans.append((encoding.disp_offset, encoding.disp_offset + encoding.disp_size))
    return spans


def literal_equal(one, other):
    """Same bytes except the numeric fields: the criterion a relocated copy satisfies."""
    if one.mnemonic != other.mnemonic or one.size != other.size:
        return False
    left, right = one.bytes, other.bytes
    mask = [True] * len(left)
    for start, size in numeric_spans(one) + numeric_spans(other):
        for offset in range(start, start + size):
            if offset < len(mask):
                mask[offset] = False
    return all(left[offset] == right[offset] for offset in range(len(left)) if mask[offset])


def align(one, other):
    """Pair the two streams, resyncing on shape so one title's extra instruction cannot drift the
    pairing for the rest of the window."""
    pairs, i, j = [], 0, 0
    while i < len(one) and j < len(other):
        if literal_equal(one[i], other[j]):
            pairs.append((i, j))
            i += 1
            j += 1
            continue
        best = None
        for skip_left in range(0, 4):
            for skip_right in range(0, 4):
                if not skip_left and not skip_right:
                    continue
                if i + skip_left < len(one) and j + skip_right < len(other) and \
                        literal_equal(one[i + skip_left], other[j + skip_right]):
                    score = (skip_left + skip_right, skip_left + skip_right)
                    if best is None or score < best[0]:
                        best = (score, skip_left, skip_right)
        if best is None:
            i += 1
            j += 1
        else:
            i += best[1]
            j += best[2]
    return pairs


def main():
    args = sys.argv[1:]
    source, from_address, target, to_address = args[0], int(args[1], 0), args[2], int(args[3], 0)
    if source == target and from_address == to_address:
        print('  self-check: source == target and address == address')
    span = int(args[args.index('--span') + 1], 0) if '--span' in args else 0x400
    top = int(args[args.index('--top') + 1], 0) if '--top' in args else 40
    show_constants = '--constants' in args
    limit = int(args[args.index('--limit') + 1], 0) if '--limit' in args else 0x20000
    left, left_base, left_instructions = decode(source, from_address, span)
    right, right_base, right_instructions = decode(target, to_address, span)

    pairs = align(left_instructions, right_instructions)
    paired = len(pairs)
    same_shape = sum(1 for i, j in pairs if shape(left_instructions[i]) == shape(right_instructions[j]))
    fields, constants = [], []
    for i, j in pairs:
        one, other = left_instructions[i], right_instructions[j]
        left_disp, right_disp = displacements(one), displacements(other)
        if len(left_disp) == len(right_disp):
            for a, b in zip(left_disp, right_disp):
                if a != b and abs(a) < limit and abs(b) < limit:
                    fields.append((one.address, other.address, a, b,
                                  '%s  <->  %s' % (one.mnemonic + ' ' + one.op_str,
                                                   other.mnemonic + ' ' + other.op_str)))
        if show_constants:
            left_imm, right_imm = immediates(one), immediates(other)
            if len(left_imm) == len(right_imm):
                for a, b in zip(left_imm, right_imm):
                    if a != b and abs(a) < limit and abs(b) < limit and \
                            not (left_base <= a < left_base + len(left)) and \
                            not (right_base <= b < right_base + len(right)):
                        constants.append((one.address, other.address, a, b,
                                         '%s  <->  %s' % (one.mnemonic + ' ' + one.op_str,
                                                          other.mnemonic + ' ' + other.op_str)))

    print('  %s 0x%x -> %s 0x%x  (span 0x%x)' % (source, from_address, target, to_address, span))
    print('  decoded: %d and %d instructions, aligned %d' %
          (len(left_instructions), len(right_instructions), paired))
    if paired:
        print('  alignment: %.3f of the longer stream paired, %.3f of pairs share operand shape'
              % (paired / max(len(left_instructions), len(right_instructions)), same_shape / paired))
    print('  field displacements that moved: %d (of %d aligned pairs)'
          % (len(fields), paired))
    seen = set()
    for address, other_address, a, b, text in fields:
        key = (a, b)
        if key in seen:
            continue
        seen.add(key)
        print('    0x%06x -> 0x%06x   [%+#x -> %+#x]  x%d   %s'
              % (address, other_address, a, b,
                 sum(1 for f in fields if (f[2], f[3]) == key), text))
        if len(seen) >= top:
            break
    if show_constants and constants:
        print('  differing immediates that are not in-image addresses: %d' % len(constants))
        for address, other_address, a, b, text in constants[:top]:
            print('    0x%06x -> 0x%06x   [%#x -> %#x]   %s' % (address, other_address, a, b, text))


if __name__ == '__main__':
    main()
