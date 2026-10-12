#!/usr/bin/env python3
"""Which script an ANM failure came from, found from the trajectory the port printed.

A failure report carries the animation's vm id, layer and the ring of commands its own update
dispatched, as `0xoffset:opcode` pairs (AnmManager::last_error_text; before section 380 the
animation manager wrote the ring in decimal while it wrote the failure position in hex). The offsets
are positions inside the script, so the pairs identify the one script among a title's thousands
that the walk was in, and the tool prints the commands around the failure with their bytes, so what
the interpreter saw can be compared with what the file holds.

Two subtleties decide the verdict, and both are measurements rather than guesses:

  * the offsets. Reports before section 380 read as decimal in the ring and hex in the headline;
    pass `--base 10` for one of those (a `0x` prefix always means hex);
  * the opcodes. The loader rewrites an instruction's opcode in its bytes to the port's canonical
    number, and it reads its rows from `AnmOpcodes.hpp` - this tool reads the same file, so a
    path that reads `28948` at a position the file spells `304` matches once the row `304 ->
    anm_th16_layer` is applied, and only a disagreement at a position the walk reached shows up as
    one.

Usage: th-anm-trace-find.py <title> <off:op,off:op,...> [--dir DIR] [--min MATCHES] [--base 10|16]
       th-anm-trace-find.py <title> --wall "<the whole failure line>"

Since section 383 the ring carries the command's length, `0x0124:8(len 0)`, so a trajectory can
also be read against the file's lengths: a reported length that the file does not have at the same
position, and a reported zero, name where the loaded copy and the title's file stop agreeing.
"""
import glob
import os
import re
import struct
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OPCODE_HEADER = os.path.join(ROOT, 'runtimes', 'th12', 'th12_web', 'cpp', 'game',
                            'AnmOpcodes.hpp')
# Used only when the header cannot be read (the tool then still knows the rows of sections 376-380).
FALLBACK_ROWS = {3: 63, 4: 69, 5: 64, 6: 75, 7: 81, 101: 84, 102: 8, 304: 28948, 313: 66}
DIRS = {title: [os.path.join(ROOT, 'runtimes', 'th%d' % title, 'th%d_web' % title, 'artifacts',
                              'cpp', 'th%d-data' % title),
                os.path.join(ROOT, 'tools', 'tmp', 'anm%d' % title)]
        for title in (12, 13, 14, 16, 17, 18)}


def loader_rows(title):
    """raw opcode -> canonical opcode for one title, parsed from the port's own table."""
    tables = {13: 'th13_anm_opcodes', 14: 'th14_anm_opcodes', 16: 'th16_anm_opcodes',
              17: 'th16_anm_opcodes', 18: 'th16_anm_opcodes'}
    try:
        text = open(OPCODE_HEADER, encoding='utf-8').read()
    except OSError:
        return dict(FALLBACK_ROWS)
    values = {name: int(value, 16) for name, value in
              re.findall(r'constexpr u16 (anm_[a-z0-9_]+) = (0x[0-9a-fA-F]+);', text)}
    if title not in tables:
        return {}
    start = text.index(tables[title] + '[]')
    body = text[start:text.index('\n};', start)]
    rows = {}
    for raw, canonical in re.findall(r'\{\s*(\d+),\s*([A-Za-z0-9_]+),\s*\d+,\s*"[A-Za-z\-]+"\s*\}',
                                    body):
        if canonical.isdigit():
            rows[int(raw)] = int(canonical)
        elif canonical in values:
            rows[int(raw)] = values[canonical]
    return rows


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
    """Yield (slot, source_id, body) for every chunk, in loader order."""
    slot = 0
    for _, chunk in chunks(data):
        ns, nc = struct.unpack_from('<HH', chunk, 4)
        for i in range(nc):
            entry = 64 + ns * 4 + i * 8
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
            yield slot, source_id, chunk[off:cursor]
            slot += 1


def instruction(body, offset):
    opcode, length, time, references = struct.unpack_from('<hHhH', body, offset)
    args = body[offset + 8:offset + length]
    values = ['%d=0x%08x' % (n, struct.unpack_from('<I', args, n * 4)[0])
              for n in range(len(args) // 4)]
    return opcode, length, time, references, values


def parse_offset(token, base):
    return int(token, 16) if token[:2].lower().startswith('0x') else int(token, base)


def find(title, trace, minimum, base, window=None, script=None):
    rows = loader_rows(title)
    print('  th%d: %d loader row(s) read from %s' % (title, len(rows), OPCODE_HEADER))
    if script:
        address, size, resource, at_load, now, changed, away = script
        print('  the port\'s own reading: script 0x%s of %s bytes, the resource\'s 0x%s' %
              (address, size, resource))
        print('     hash 0x%s at load, 0x%s now%s%s' %
              (at_load, now, ' (the loaded script changed)' if changed else '',
               ' (the vm points away from the resource)' if away else ''))
    files = []
    for directory in DIRS[title]:
        files += sorted(glob.glob(os.path.join(directory, '*.anm')))
    if not files:
        print('  th%d: no ANM files exported (dump them with tools/th-archive-dump.mjs)' % title)
        return
    wanted = []
    for pair in trace:
        found = re.match(r'^([^:]+):(\d+)(?:\(len (\d+)\))?$', pair.strip())
        if not found:
            sys.exit('  cannot read the trace pair %r' % pair)
        wanted.append((parse_offset(found.group(1), base), int(found.group(2), 10),
                      int(found.group(3)) if found.group(3) else None))
    for path in files:
        data = open(path, 'rb').read()
        for slot, source_id, body in scripts(data):
            rawops, canon, lens = {}, {}, {}
            cursor = 0
            while cursor + 8 <= len(body):
                opcode, length, _, _, _ = instruction(body, cursor)
                rawops[cursor] = opcode
                canon[cursor] = rows.get(opcode, opcode)
                lens[cursor] = length
                if length < 8:
                    break
                cursor += length
            matched = sum(1 for offset, opcode, _ in wanted if canon.get(offset) == opcode)
            if matched < minimum:
                continue
            reported = [(offset, memory) for offset, _, memory in wanted if memory is not None]
            agree = [offset for offset, memory in reported
                     if offset in lens and lens[offset] == memory]
            disagree = [(offset, memory, lens.get(offset)) for offset, memory in reported
                       if lens.get(offset) != memory]
            print('  %s slot %d (source_id %d, %d bytes): %d of %d pairs%s' %
                  (os.path.basename(path), slot, source_id, len(body), matched, len(wanted),
                   '' if not reported else
                   '; memory and file agree on the length at %d of %d positions' %
                   (len(agree), len(reported))))
            last_offset, last_opcode, last_memory = wanted[-1]
            if last_offset in rawops:
                raw = rawops[last_offset]
                print('     the report stopped at +0x%x with %d; the file spells %d, which this'
                      ' title\'s own row turns into %d' %
                      (last_offset, last_opcode, raw, rows.get(raw, raw)))
                if last_memory is not None and lens.get(last_offset) != last_memory:
                    print('     the file\'s own length there is %d and the loaded command\'s is %d'
                          '%s' % (lens[last_offset], last_memory,
                                  '; a zero length is a command the walk cannot step over'
                                  if last_memory == 0 else ''))
            else:
                print('     the report stopped at +0x%x, where the file has no instruction'
                      % last_offset)
            if disagree:
                print('     the lengths part first at +0x%x: the loaded command is %d, the'
                      ' file\'s is %s' %
                      (disagree[0][0], disagree[0][1],
                       'absent' if disagree[0][2] is None else disagree[0][2]))
            if window:
                offset, memory = window
                if offset + len(memory) <= len(body):
                    same = sum(1 for i, byte in enumerate(memory) if body[offset + i] == byte)
                    print('     the loaded window at +0x%x: %d of %d bytes are the file\'s own'
                          % (offset, same, len(memory)))
                    best = []
                    for delta in (-16, -12, -8, -4, 4, 8, 12, 16):
                        at = offset + delta
                        if at < 0 or at + len(memory) > len(body):
                            continue
                        hits = sum(1 for i, byte in enumerate(memory) if body[at + i] == byte)
                        best.append((hits, delta))
                    if best:
                        hits, delta = max(best)
                        print('     the same bytes stand in the file at +0x%x (%+d): %d of %d'
                              % (offset + delta, delta, hits, len(memory)))

            at = max(0, last_offset - 16)
            while at < last_offset + 32:
                if at in rawops:
                    opcode, length, time, references, values = instruction(body, at)
                    mark = '  <- the failure' if at == last_offset else ''
                    print('        +0x%03x op=%-3d (%d) len=%3d time=%-4d refs=0x%04x args=%s%s'
                          % (at, opcode, rows.get(opcode, opcode), length, time, references,
                             ' '.join(values), mark))
                at += 4
            print('     the whole walk of this script: %s' %
                  ' '.join('0x%x:%d->%d' % (at, rawops[at], canon[at])
                           for at in sorted(rawops)))


def main(argv):
    minimum, base, window, pairs, script = None, 16, None, None, None
    title = int(argv[0])
    if '--wall' in argv:
        wall = argv[argv.index('--wall') + 1]
        pairs = [m.group(0) for m in
                 re.finditer(r'0x([0-9a-fA-F]{4,}):(\d+)(?:\(len (\d+)\))?', wall)]
        header = re.search(r'bytes \+0x([0-9a-fA-F]+):((?: [0-9a-fA-F]{2})+)', wall)
        if header:
            window = (int(header.group(1), 16),
                      bytes(int(byte, 16) for byte in header.group(2).split()))
        hashes = re.search(r'script 0x([0-9a-fA-F]+) of (\d+) bytes, the resource\'s '
                           r'0x([0-9a-fA-F]+); hash 0x([0-9a-fA-F]+) at load, '
                           r'0x([0-9a-fA-F]+) now', wall)
        if hashes:
            script = (hashes.group(1), hashes.group(2), hashes.group(3), hashes.group(4),
                      hashes.group(5), hashes.group(4) != hashes.group(5),
                      hashes.group(1) != hashes.group(3))
    if pairs is None:
        pairs = argv[1].split(',')
        base = 16
    minimum = len(pairs) - 2
    if '--dir' in argv:
        DIRS[title] = [argv[argv.index('--dir') + 1]]
    if '--min' in argv:
        minimum = int(argv[argv.index('--min') + 1])
    if '--base' in argv:
        base = int(argv[argv.index('--base') + 1])
    find(title, pairs, minimum, base, window, script)


if __name__ == '__main__':
    if len(sys.argv) < 3:
        sys.exit(__doc__)
    main(sys.argv[1:])
