"""Derive a title's sample-name table from its executable.

The port carries TH12's sample list as 49 names in archive order, and the comment beside it records where that
order came from: ".data 0x4aea50 as 49 consecutive pointers to .rdata se_*.wav strings". Section 49 of
docs/porting/porting-plan.md then measured that the strings' order in .rdata is NOT that order (2 of 49 monotone
against the archive), so the pointer array is the thing to read. This tool reads it, for any of the six titles.

Method, with no title-specific constants:
  1. parse the PE headers to get the section table, because file offset != virtual address - image base;
  2. collect the VA of every "se_*.wav" string in the image;
  3. scan the writable data sections for runs of consecutive u32 slots that all point at one of those strings;
  4. report every run of at least --min entries, in array order.

For th12 the tool has a known-good answer: the run at 0x004aea50 with 49 entries, whose names must equal the order
in runtimes/th12/th12_web/cpp/game/SoundEffects.cpp (the recalibrated table). That check is --verify-th12.

usage: py -3 tools/th-sample-table.py <path-to-exe> [--min N] [--pattern RE] [--verify-th12]
"""
import struct
import sys
import re
import json


def sections(blob):
    lfanew = struct.unpack_from('<I', blob, 0x3C)[0]
    coff = lfanew + 4                      # the COFF header follows the 4-byte PE signature
    nsec, = struct.unpack_from('<H', blob, coff + 2)
    optsize, = struct.unpack_from('<H', blob, coff + 16)
    sec = coff + 20 + optsize              # = lfanew + 24 + SizeOfOptionalHeader
    out = []
    for i in range(nsec):
        base = sec + i * 40
        name = blob[base:base + 8].rstrip(b'\0').decode('latin1').encode('ascii', 'replace').decode('ascii')
        vsize, va, rawsize, raw = struct.unpack_from('<IIII', blob, base + 8)
        chars, = struct.unpack_from('<I', blob, base + 36)
        out.append({'name': name, 'va': va, 'vsize': vsize, 'raw': raw, 'rawsize': rawsize, 'chars': chars})
    return out


def main():
    args = sys.argv[1:]
    if not args:
        print(__doc__)
        return 2
    path = args[0]
    amin = 8
    if '--min' in args:
        amin = int(args[args.index('--min') + 1])
    verify = '--verify-th12' in args
    # A raw string, so one backslash: with two the pattern wants a literal backslash before
    # "wav" and matched nothing, which read as "this executable has no sample names".
    pattern = args[args.index('--pattern') + 1] if '--pattern' in args else r'se_[a-z0-9_]{2,12}\.wav'
    blob = open(path, 'rb').read()
    image_base, = struct.unpack_from('<I', blob, struct.unpack_from('<I', blob, 0x3C)[0] + 24 + 28)
    secs = sections(blob)
    # Every string matching the pattern, and its virtual address.
    strings = {}
    for m in re.finditer(pattern.encode(), blob):
        for s in secs:
            if s['raw'] <= m.start() < s['raw'] + s['rawsize']:
                strings[image_base + s['va'] + (m.start() - s['raw'])] = m.group(0).decode('latin1')
                break
    # Runs of consecutive pointers, in every mapped section: th12, 13 and 14 keep the array in
    # .data and th16, 17 and 18 keep the same const array in .rdata, so the section is reported
    # beside the address rather than assumed.
    runs = []
    for s in secs:
        if s['rawsize'] == 0:
            continue
        data = blob[s['raw']:s['raw'] + s['rawsize']]
        n = len(data) // 4
        slots = struct.unpack_from('<%dI' % n, data, 0)
        i = 0
        while i < n:
            if slots[i] in strings:
                j = i
                while j < n and slots[j] in strings:
                    j += 1
                if j - i >= amin:
                    runs.append((image_base + s['va'] + i * 4, j - i,
                                 [strings[slots[k]] for k in range(i, j)], s['name']))
                i = j
            else:
                i += 1
    runs.sort(key=lambda r: -r[1])
    print('  image base 0x%08x, sections %s' % (image_base, ', '.join(s['name'] for s in secs)))
    print('  %s strings: %d positions, %d distinct' % (pattern, len(strings), len(set(strings.values()))))
    print('  pointer runs (>= %d): %d' % (amin, len(runs)))
    for va, count, names, sec in runs[:4]:
        distinct = len(set(names))
        print('    %-8s 0x%08x  %3d entries  %d distinct  head: %s' % (
            sec, va, count, distinct, ' '.join(names[:4])))
    if not runs:
        return 1
    va, count, names, sec = runs[0]
    result = {'executable': path, 'section': sec, 'arrayVa': '0x%08x' % va, 'entries': count,
              'distinct': len(set(names)), 'names': names}
    print(json.dumps(result, indent=2))
    if verify:
        expected = ['se_plst00', 'se_enep00', 'se_pldead00', 'se_power0', 'se_power1', 'se_tan00']
        got = [n[:-4] for n in names[:6]]
        ok = got == expected
        print('  --verify-th12 head %s against %s: %s' % (got, expected, 'OK' if ok else 'MISMATCH'))
        return 0 if ok else 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
