#!/usr/bin/env python3
"""Print the instructions a shipped ECL resource carries for one opcode, with their argument bytes.

The record layout is the one `th-ecl-walk.py` validates (and the port's reader uses): an `ECLH`
block per sub-routine, reached through an offset table, instructions 16 bytes in with the opcode at
+0x04, the length at +0x06, the parameter count at +0x0b and the arguments from +0x10.

Printing every occurrence of one opcode in one file answers a question a single argument read cannot:
whether a handler the port routes from TH12's dispatcher even sees the same argument shape in the
other title.

Args:
    <ecl-file> <opcode,hex>          list the records that carry an opcode
    <ecl-file> --at 0x<offset>       list the one record that contains a file offset

The second form answers "which opcode carries this name/string" without guessing: the record whose
`[cursor, cursor+length)` holds the byte is printed with its opcode and arguments.
"""
import struct
import sys

args = sys.argv[1:]
limit = 12
if '--limit' in args:
    limit = int(args[args.index('--limit') + 1])
path = args[0]
at = None
if '--at' in args:
    at = int(args[args.index('--at') + 1], 0)
    opcode = None
else:
    opcode = int(args[1], 0)

data = open(path, 'rb').read()
blocks = []
cursor_at = 0
while True:
    cursor_at = data.find(b'ECLH', cursor_at)
    if cursor_at < 0:
        break
    blocks.append(cursor_at)
    cursor_at += 4
print('  %s: %d ECLH block(s)' % (path, len(blocks)))
found = 0
for block in blocks:
    cursor = block + 16
    while cursor + 16 <= len(data):
        time_value, op, length = struct.unpack_from('<ihh', data, cursor)
        references, difficulty, parameters = struct.unpack_from('<HBB', data, cursor + 8)
        if length < 16 or cursor + length > len(data):
            break
        if (op == opcode) or (at is not None and cursor <= at < cursor + length):
            arguments = data[cursor + 16:cursor + length]
            words = ' '.join('0x%x' % v for v in struct.unpack_from('<%di' % (len(arguments) // 4), arguments)) \
                if len(arguments) >= 4 else ''
            text = ''.join(chr(b) if 32 <= b < 127 else '.' for b in arguments)
            print('    block 0x%x +0x%x: opcode=0x%x time=%d length=%d refs=0x%x diff=%d params=%d'
                  % (block, cursor - block, op, time_value, length, references, difficulty, parameters))
            print('      args: %s' % words)
            print('      text: %s' % text)
            found += 1
            if found >= limit:
                sys.exit(0)
        if op == 0:
            break
        cursor += length
what = ('offset 0x%x' % at) if at is not None else ('opcode 0x%x' % opcode)
print('  %d instruction(s) with %s' % (found, what))
