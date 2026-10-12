#!/usr/bin/env python3
"""Dump one ANM script's instruction stream, addressed by its global slot.

The port's AnmResource::open appends sprites and scripts per chunk in table order, so a
script's slot is what the compositor binds. Argument slots are 4 bytes each and follow the
8-byte command header; `references` (read by the interpreter) says whether a value is a
direct number or an indirection into 10000..10022.
"""
import struct
import sys


def chunks(data):
    base = 0
    while True:
        if len(data) - base < 64:
            return
        stride, = struct.unpack_from('<I', data, base + 36)
        size = stride or (len(data) - base)
        yield base, data[base:base + size]
        if not stride:
            return
        base += stride


def scripts(data):
    """Yield (slot, source_id, bytes) for every chunk, in loader order."""
    slot = 0
    for base, c in chunks(data):
        ns, nc = struct.unpack_from('<HH', c, 4)
        for i in range(nc):
            entry = 64 + ns * 4 + i * 8
            source_id, off = struct.unpack_from('<iI', c, entry)
            cursor = off
            while True:
                opcode, length = struct.unpack_from('<hH', c, cursor)
                if opcode == -1:
                    cursor += 8
                    break
                cursor += length
            yield slot, source_id, c[off:cursor]
            slot += 1


def dump(path, slot):
    data = open(path, 'rb').read()
    for index, source_id, body in scripts(data):
        if index != slot:
            continue
        print('  %s slot %d (source_id %d, %d bytes)' % (path.split('/')[-1], slot, source_id, len(body)))
        cursor = 0
        shown = 0
        while cursor + 8 <= len(body):
            opcode, length, time, references = struct.unpack_from('<hHhH', body, cursor)
            args = body[cursor + 8:cursor + length]
            text = ' '.join('%d=0x%08x' % (n, struct.unpack_from('<I', args, n * 4)[0]) for n in range(len(args) // 4))
            print('    +0x%03x op=%-3d len=%3d time=%-4d refs=0x%04x args=%s' % (cursor, opcode, length, time, references, text))
            if opcode == -1:
                return
            shown += 1
            if shown >= 40:
                print('    ...')
                return
            cursor += length
        return
    print('  %s has no slot %d' % (path, slot))


if __name__ == '__main__':
    dump(sys.argv[1], int(sys.argv[2]))
