"""Dump TH14's bullet-transform dispatch tables.

The walker at 0x18140 selects the handler for the current entry's opcode with two tables in .text:
a 64-entry byte table at 0x419110 (for opcodes 1..0x40) whose values index a jump table at 0x4190f4.
Opcodes above that go through the compare chain at 0x185f3 (0x81..0x8000), 0x18a3e (>0x8000) and
0x190e9 (0x41..0x7f), whose own tables this script locates by disassembling them.
"""
import importlib.util
import struct
from pathlib import Path

ROOT = Path('H:/code/thp')
spec = importlib.util.spec_from_file_location('window', ROOT / 'tools/th-code-window.py')
window = importlib.util.module_from_spec(spec)
spec.loader.exec_module(window)
import capstone

blob = open('H:/Games/th/14/th14.exe', 'rb').read()
text_rva, raw, size = window.code_section(blob)


def image(offset, length):
    return blob[raw + (offset - text_rva):raw + (offset - text_rva) + length]


byte_table = image(0x19110, 64)
print('  byte table 0x419110 (opcode 1..0x40):')
print('    ' + ' '.join('%02x' % value for value in byte_table))
highest = max(byte_table)
targets = struct.unpack_from('<%dI' % (highest + 1), image(0x190f4, 4 * (highest + 1)))
print('  jump table 0x4190f4: %d entries' % len(targets))
for index, target in enumerate(targets):
    opcodes = [op for op in range(1, 0x41) if byte_table[op - 1] == index]
    print('    [%2d] %#010x   opcodes %s' % (index, target,
                                             ','.join('%#x' % op for op in opcodes) or '-'))

md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
md.detail = True
md.skipdata = True
print('  chain regions:')
for label, start, span in (('0x81..0x8000', 0x185f3, 0x90), ('>0x8000', 0x18a3e, 0xa0),
                           ('0x41..0x7f', 0x190e9, 0x60), ('0x8000', 0x18a06, 0x40),
                           ('0x80', 0x185e2, 0x18)):
    print('    --- %s at %#x ---' % (label, start))
    for ins in md.disasm(image(start, span), start):
        print('      %#010x  %s %s' % (ins.address, ins.mnemonic, ins.op_str))
