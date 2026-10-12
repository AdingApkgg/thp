#!/usr/bin/env python3
"""The message interpreter's MSG 28 and 29 bodies, read from each title's own executable.

The port carries both numbers for TH13 from its image (28: 0x428c8e loads the payload's two floats
into the dialogue state at +0x194/+0x198; 29: 0x429c2d sets style bits 2..5 from the payload's low
four bits) and says TH12 has neither - which the corpus agrees with, TH12's messages containing no
28 or 29 at all. The generation's messages contain both (28 with an eight-byte payload everywhere,
29 with four bytes), so their bodies are measured the same way: the instructions of TH13's own
handlers are the control, and each title is asked for the same shape in its own image.

Usage: th-msg-op-body.py [title...]
"""
import collections
import importlib
import json
import os
import re
import struct
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'tools'))
Image = importlib.import_module('th12-pe').Image
from capstone import Cs, CS_ARCH_X86, CS_MODE_32  # noqa: E402

CONTROL = {13: {'28': (0x428c8e, 0x194, 0x198), '29': (0x429c2d, 0x3c)}}
EXES = {12: 'H:/Games/th/12/th12.exe', 13: 'H:/Games/th/13/th13.exe', 14: 'H:/Games/th/14/th14.exe',
        16: 'H:/Games/th/16/th16.exe', 17: 'H:/Games/th/17/th17.exe', 18: 'H:/Games/th/18/th18.exe'}


def disassembler():
    md = Cs(CS_ARCH_X86, CS_MODE_32)
    md.detail = False
    # .text is not a single stream of instructions; without skipdata the sweep stops at the first
    # byte capstone cannot decode, which on th13 is after 3540 of the section's instructions.
    md.skipdata = True
    return md


def decode_at(img, md, va, count):
    at = img.offset_of(va)
    if not at:
        return []
    return list(md.disasm(bytes(img.data[at:at + 64]), va))[:count]


MEMORY = re.compile(r'\[([a-z0-9]+) \+ ([^\]\s]+)\]')


def memory_target(text):
    """`dword ptr [edi + 0x194]` -> ('edi', 0x194); `[eax + 4]` -> ('eax', 4).

    Capstone renders a displacement below 10 as decimal and above it in hex, so the number is
    parsed by its own prefix; `[edi + eax]` (base plus index) has no number and is not one.
    """
    match = MEMORY.search(text)
    if match:
        try:
            return match.group(1), int(match.group(2), 0)
        except ValueError:
            return None, None
    plain = re.search(r'\[([a-z0-9]+)\]', text)
    if plain:
        return plain.group(1), 0
    return None, None


def sweep(img, keep):
    """Stream `.text` and yield the last `keep` instructions at every step."""
    md = disassembler()
    for name, base, _size, raw_off, raw_size in img.sections:
        if name != '.text':
            continue
        history = collections.deque(maxlen=keep)
        for ins in md.disasm(bytes(img.data[raw_off:raw_off + raw_size]), base):
            history.append(ins)
            if len(history) == keep:
                yield list(history)


def scan(title):
    """MSG 28's shape: fld ptr [R+4] / fstp ptr [S+X] / fld ptr [R+8] / fstp ptr [S+Y]."""
    img = Image(EXES[title])
    found = []
    seen = set()
    for body in sweep(img, 4):
        if body[0].mnemonic != 'fld' or body[2].mnemonic != 'fld':
            continue
        if body[1].mnemonic != 'fstp' or body[3].mnemonic != 'fstp':
            continue
        source_a, low = memory_target(body[0].op_str)
        source_b, high = memory_target(body[2].op_str)
        if source_a != source_b or low != 4 or high != 8:
            continue
        first = memory_target(body[1].op_str)
        second = memory_target(body[3].op_str)
        if first[0] != 'edi' or second[0] != 'edi' or first[1] == 0 or second[1] == 0:
            continue
        key = (body[0].address, first[1], second[1])
        if key in seen:
            continue
        seen.add(key)
        found.append((body[0].address, first[1], second[1]))
    return sorted(found)


def scan29(title):
    """MSG 29's shape: mov R,[P+4] ; add R,R ; add R,R ; ... and R,mask."""
    img = Image(EXES[title])
    found = []
    seen = set()
    for body in sweep(img, 6):
        if body[0].mnemonic != 'mov' or body[1].mnemonic != 'add' or body[2].mnemonic != 'add':
            continue
        source, at = memory_target(body[0].op_str)
        if source is None or at != 4:
            continue
        register = body[0].op_str.split(',')[0].strip()
        if body[1].op_str.replace(' ', '') != '%s,%s' % (register, register):
            continue
        if body[2].op_str.replace(' ', '') != '%s,%s' % (register, register):
            continue
        mask = None
        for insn in body[3:]:
            if insn.mnemonic == 'and' and register in insn.op_str and ',' in insn.op_str:
                mask = int(insn.op_str.split(',')[1].strip(), 16)
        if mask is None:
            continue
        key = (body[0].address, mask)
        if key in seen:
            continue
        seen.add(key)
        found.append((body[0].address, mask))
    return sorted(found)


for title in ([int(a) for a in sys.argv[1:]] or sorted(EXES)):
    if title == 12:
        continue
    bodies_28 = scan(title)
    bodies_29 = scan29(title)
    print('  th%d: %d site(s) with the 28 shape, %d with the 29 shape' %
          (title, len(bodies_28), len(bodies_29)))
    for va, first, second in bodies_28:
        known = CONTROL.get(title, {}).get('28')
        mark = 'CONTROL' if known and (va, first, second) == known else ''
        if mark or title not in CONTROL:
            print('    28 at 0x%x writes the two floats to +0x%x and +0x%x  %s' %
                  (va, first, second, mark))
    for va, mask in bodies_29:
        known = CONTROL.get(title, {}).get('29')
        mark = 'CONTROL' if known and (va, mask) == known else ''
        if mark or title not in CONTROL:
            print('    29 at 0x%x masks the payload with 0x%x  %s' % (va, mask, mark))
    if title in CONTROL:
        assert CONTROL[title]['28'] in bodies_28, 'the control 28 body was not found'
        assert CONTROL[title]['29'] in bodies_29, 'the control 29 body was not found'

