#!/usr/bin/env python3
"""Read a replay file's header fields, so the numbers in Replay.cpp stay a measurement.

A replay starts with a four-byte magic, a version word, and - for TH12 and TH13 - the packed and
unpacked sizes at +0x1c and +0x20. The magic and version are the title's: this prints them for
every *.rpy in a directory, which is how `t12r`/4 and `t13r`/2 were read (the four attract demos
each title ships), and how a future title's would be.

Usage: th-replay-table.py <dir-or-file>...
"""
import glob
import os
import struct
import sys


def main(paths):
    files = []
    for path in paths:
        files.extend(sorted(glob.glob(os.path.join(path, '*.rpy'))) if os.path.isdir(path) else [path])
    if not files:
        print('  no .rpy files')
        return
    print('  %-34s %-6s %-5s %9s %10s %10s' % ('file', 'magic', 'ver', 'bytes', 'packed', 'unpacked'))
    versions = set()
    for path in files:
        data = open(path, 'rb').read()
        if len(data) < 0x24:
            print('  %-34s short (%d bytes)' % (os.path.basename(path), len(data)))
            continue
        magic, version = struct.unpack_from('<IH', data, 0)
        packed, unpacked = struct.unpack_from('<II', data, 0x1c)
        versions.add((magic.to_bytes(4, 'little'), version))
        print('  %-34s %-6s %-5d %9d %10d %10d' %
              (os.path.basename(path), magic.to_bytes(4, 'little').decode('ascii', 'replace'),
               version, len(data), packed, unpacked))
    print('  magic/version pairs seen: %s' %
          ' '.join('%s/%d' % (m.decode('ascii', 'replace'), v) for m, v in sorted(versions)))


if __name__ == '__main__':
    main(sys.argv[1:] or ['.'])
