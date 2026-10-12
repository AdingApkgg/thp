#!/usr/bin/env python3
"""The script slots of an ANM file, read the way the port's loader reads it.

`AnmResource::open` walks a file chunk by chunk and mixes two tables whose counts sit next to each
other in the header, which is a place to swap them:

  * the u16 at +4 counts the **sprites**: `64 + i*4` holds each sprite's offset, and the loader
    requires it to be at or past `table_end = 64 + ns*4 + nc*8`;
  * the u16 at +6 counts the **scripts** the chunk's texture owns: their records start at
    `64 + ns*4`, eight bytes each (an i32 source id and a u32 offset), and their end is the first
    instruction with opcode -1.

The scripts are appended chunk by chunk, so a script's global slot is the running sum of the earlier
chunks' script counts. That sum is the number every `create(resource, script, file)` is checked
against, which is what a reader needs when a title's dialogue animation fails to create.

Controls, both run before the tool was kept:
  * TH12's own ascii.anm is 2 chunks with 15 + 6 scripts = 21 slots, and `th-anm-script-dump.py`
    (which walks the same two tables) dumps slot 20 without complaint;
  * TH12's st05logo.anm and the generation's (out of the title's archive through
    `th-archive-dump.mjs`) both come out at 7 script slots, which is what says the dialogue's
    `create(8, logo, 2, 27)` has script 2 in range while a 74-slot text resource has slot 0.

Usage: th-anm-script-slots.py <anm-file> [more...]
"""
import struct
import sys


def chunks(data):
    """Yield (base, chunk) for each chunk in loader order."""
    base = 0
    while base + 64 <= len(data):
        stride, = struct.unpack_from('<I', data, base + 36)
        size = stride or (len(data) - base)
        size = min(size, len(data) - base)
        yield base, data[base:base + size]
        if not stride:
            return
        base += stride


def sprites(chunk):
    count, = struct.unpack_from('<H', chunk, 4)
    return [struct.unpack_from('<I', chunk, 64 + i * 4)[0] for i in range(count)]


def scripts(chunk):
    """Yield (source_id, bytes) for a chunk's scripts, in loader order."""
    ns, nc = struct.unpack_from('<HH', chunk, 4)
    for i in range(nc):
        entry = 64 + ns * 4 + i * 8
        if entry + 8 > len(chunk):
            return
        source_id, off = struct.unpack_from('<iI', chunk, entry)
        cursor = off
        while cursor + 8 <= len(chunk):
            opcode, length = struct.unpack_from('<hH', chunk, cursor)
            if opcode == -1:
                cursor += 8
                break
            if length < 8:
                break
            cursor += length
        yield source_id, chunk[off:cursor]


def main(paths):
    for path in paths:
        data = open(path, 'rb').read()
        print('  %s' % path)
        slot = 0
        for number, (base, chunk) in enumerate(chunks(data)):
            ns, nc = struct.unpack_from('<HH', chunk, 4)
            stride, = struct.unpack_from('<I', chunk, 36)
            name_off, = struct.unpack_from('<I', chunk, 16)
            stop = data.find(b'\0', base + name_off) if 64 <= name_off < len(chunk) else -1
            name = data[base + name_off:stop].decode('latin-1') if stop > 0 else ''
            print('    chunk %d at 0x%-6x format %d  %2d sprites  %2d scripts  %s' %
                  (number, base, struct.unpack_from('<I', chunk, 0)[0], ns, nc, name))
            for source_id, body in scripts(chunk):
                if slot == 0 or source_id == 0:
                    if body:
                        opcode, length, time, references = struct.unpack_from('<hHhH', body, 0)
                        print('      slot %2d (source %d, %d bytes) starts op=%d len=%d time=%d' %
                              (slot, source_id, len(body), opcode, length, time))
                slot += 1
        print('    %s: %d script slot(s) in %d chunk(s)' %
              (path.split('/')[-1], slot, len(list(chunks(data)))))


if __name__ == '__main__':
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    main(sys.argv[1:])
