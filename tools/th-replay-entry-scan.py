#!/usr/bin/env python3
"""Where a title's replay stage record keeps the entry pair.

A record stores the position a stage starts the player at. In every attract demo a title ships,
that position is x = 0 and y = 51200 - 1/128 turns the second into the 400 pixels a stage puts
the player at - so the pair is a measurement rather than a guess: look for exactly that pair of
words inside the record's own fixed part, and require the same offset in *every* demo of the
title. TH12 answers +0x30 (the row the port carries) and TH13, TH14, TH16, TH17 and TH18 all
answer +0xC, and each title answers nothing else.

  py -3 tools/th-replay-entry-scan.py [titles...] [--dump]

The control is built in: 12 must answer +0x30 and 13 +0xC, both of which are already read out
of their machine code in `Replay.hpp`. `--dump` prints, for each title, what its demos hold at
the offset the port reads today and the one this reports.
"""
import argparse
import struct
from pathlib import Path

module = {}
_source = Path('tools/th-replay-container.py').read_text(encoding='utf-8').partition('if __name__')[0]
exec(compile(_source, 'th-replay-container', 'exec'), module)
decode_with, demo_files = module['decode_with'], module['demo_files']

PAIR = {11: ((0xaa, 0xe1, 0x800), (0x3d, 0x7a, 0x40)),
        12: ((0x5e, 0xe1, 0x800), (0x7d, 0x3a, 0x40))}
GENERATION = ((0x5c, 0xe1, 0x400), (0x7d, 0x3a, 0x100))
FILE_HEADER = {11: 0x70, 12: 0x70, 13: 0x74, 14: 0x94, 16: 0xA0, 17: 0xA0, 18: 0xC8}
STAGE_HEADER = {11: 0x90, 12: 0xA0, 13: 0xC4, 14: 0xDC, 16: 0x294, 17: 0x158, 18: 0x126C}
ENTRY = 51200
TODAY = {12: 0x30, 18: 0x30, 13: 0x30, 14: 0x30, 16: 0x30, 17: 0x30}  # the row before round 587


def bodies(title):
    for path in demo_files(title):
        data = path.read_bytes()
        packed, unpacked = struct.unpack_from('<II', data, 0x1C)
        yield path.name, decode_with(data, packed, unpacked, PAIR.get(title, GENERATION))


def scan(title):
    names, files = [], []
    for name, body in bodies(title):
        names.append(name)
        files.append(body)
    base, span = FILE_HEADER[title], STAGE_HEADER[title]
    hits = [offset for offset in range(0, span - 8, 4)
            if all(struct.unpack_from('<II', body, base + offset) == (0, ENTRY) for body in files)]
    return names, files, hits


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('titles', nargs='*', type=int)
    parser.add_argument('--dump', action='store_true')
    args = parser.parse_args()
    for title in args.titles or sorted(FILE_HEADER):
        names, files, hits = scan(title)
        if not files:
            continue
        print('  th%-3d pair (0, %d) at record +%s on all %d demo(s)'
              % (title, ENTRY, ' and +'.join('0x%x' % h for h in hits) or 'nowhere', len(files)))
        if args.dump:
            for offset, label in ((TODAY.get(title, 0x30), 'the row the port read'), (hits[0] if hits else None, 'this scan')):
                if offset is None:
                    continue
                values = [struct.unpack_from('<II', body, FILE_HEADER[title] + offset) for body in files]
                print('      %-19s +0x%-4x %s' % (label, offset, ' '.join('%d/%d' % v for v in values)))


if __name__ == '__main__':
    main()
