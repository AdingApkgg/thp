#!/usr/bin/env python3
"""Check that a code table's rows name the twin function's ENTRY.

Section 75's finding: the fixture substitutes host behaviour by writing a five-byte jump over the
address a row maps, so a row whose target is one byte inside a function makes the guest execute the
entry's `push` and then jump, stranding the pushed register under the stub's frame. The row that did
it was measured - its own confidence said "candidate" - and the failure surfaced two rounds later as
an emulator trap in the stack page.

Decodability is not the test: one byte inside a function is still decodable (`0x4621c1` decodes as
`push esi`). The test is the one section 75 used to re-measure the pair - align the two windows
from the two addresses and require the FIRST pair to be the first instruction of each. That is what
a window match alone does not give.

  node-level self-check, run in the round that added this tool:
    pair (th11 0x4569c0, th12 0x4621c0): entries align
    pair (th11 0x4569c0, th12 0x4621c1): entries do NOT align (first pair src#0 <-> tgt#k)

Usage:
  th-twin-rows.py <table.json> <src.exe> <tgt.exe> [--span 0x40] [--quiet]
  th-twin-rows.py --pair <src.exe> <0xSRC> <tgt.exe> <0xTGT> [--span 0x40]
  th-twin-rows.py --verdict <exe> <0xADDR>
"""
import io
import json
import os
import re
import struct
import sys
from importlib.machinery import SourceFileLoader

import capstone

FIELDS = SourceFileLoader('twinfields', 'tools/th-twin-fields.py').load_module()


def image(path):
    """The .text of an image, named by virtual address (cached per path)."""
    if path not in CACHE:
        data = open(path, 'rb').read()
        pe = struct.unpack_from('<I', data, 0x3C)[0]
        count = struct.unpack_from('<H', data, pe + 6)[0]
        option = struct.unpack_from('<H', data, pe + 20)[0]
        base = struct.unpack_from('<I', data, pe + 24 + 28)[0]
        for index in range(count):
            at = pe + 24 + option + index * 40
            name = data[at:at + 8].split(b'\x00')[0].decode('ascii', 'replace')
            vsize, rva, rawsize, raw = struct.unpack_from('<IIII', data, at + 8)
            if name == '.text':
                CACHE[path] = (base + rva, data[raw:raw + max(vsize, rawsize)])
                break
        else:
            raise SystemExit('no .text in %s' % path)
    return CACHE[path]


CACHE = {}


def window(path, address, span):
    start, blob = image(path)
    md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
    md.detail = True
    return list(md.disasm(blob[address - start:address - start + span], address))


def first_instruction(path, address):
    start, blob = image(path)
    if not (start <= address < start + len(blob)):
        return None
    md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
    out = list(md.disasm(blob[address - start:address - start + 16], address))
    return None if not out else '%s %s' % (out[0].mnemonic, out[0].op_str)


def verdict(source, source_address, target, target_address, span):
    one = window(source, source_address, span)
    other = window(target, target_address, span)
    pairs = FIELDS.align(one, other)
    if not pairs:
        return {'first': None, 'pairs': 0, 'instructions': (len(one), len(other))}
    first = pairs[0]
    aligned = all(FIELDS.shape(one[i]) == FIELDS.shape(other[j]) for i, j in pairs)
    return {'first': first, 'pairs': len(pairs), 'shape': aligned,
            'instructions': (len(one), len(other))}


def report(source, source_address, target, target_address, span, quiet):
    result = verdict(source, source_address, target, target_address, span)
    ok = result['first'] == (0, 0) and result.get('shape', False)
    if not quiet or not ok:
        print('    %s -> %s  %-18s pairs=%d/%d  %s' %
              (hex(source_address), hex(target_address), 'ok' if ok else 'ENTRIES DO NOT ALIGN',
               result['pairs'], max(result['instructions']), first_instruction(target, target_address) or '?'))
        if result['first'] not in (None, (0, 0)):
            print('        first aligned pair: src#%d <-> tgt#%d (the target is %d instruction(s) in)'
                  % (result['first'][0], result['first'][1], result['first'][1]))
    return ok


def normalize(blob, at, span, base, higher):
    """The window's bytes with every byte of an in-image dword marked (the same rule
    th-twin-find uses as a prefilter; the alignment is what decides)."""
    window = blob[at:at + span]
    wild = [False] * len(window)
    for offset in range(len(window)):
        for start in range(max(0, offset - 3), min(offset + 1, len(window) - 3)):
            word = struct.unpack_from('<I', window, start)[0]
            if base <= word < higher:
                wild[offset] = True
    return window, wild


def search(source, source_address, target, span, min_run, top):
    """Every place in the target whose alignment with the source starts at BOTH entries.

    The window match is only a prefilter (th-twin-find already showed it cannot separate near
    copies that differ in a call displacement alone); the answer is ranked by how much of the
    stream pairs with the same operand shape, and only candidates whose first pair is the first
    instruction of each side are reported as entries.
    """
    source_start, source_blob = image(source)
    target_start, target_blob = image(target)
    source_window, wild = normalize(source_blob, source_address - source_start, span,
                                  source_start, source_start + len(source_blob))
    md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
    md.detail = True
    one = list(md.disasm(source_window, source_address))
    hits = []
    if '--prefilter' in sys.argv and sys.argv[sys.argv.index('--prefilter') + 1] == 'entries':
        # A window match cannot survive an inserted or deleted instruction between the copies
        # (measured on 0x456430: no window hit at all). Every function entry is a candidate
        # instead - the code after `cc` padding, after a `ret`, after a `jmp`, or aligned.
        for candidate in range(0, len(target_blob) - span):
            before = target_blob[candidate - 1]
            if before in (0xcc, 0xc3, 0xe9, 0xeb) or candidate % 16 == 0:
                hits.append(candidate)
    else:
        for candidate in range(0, len(target_blob) - span):
            run = best = 0
            for index, flag in enumerate(wild):
                if flag:
                    run = 0
                    continue
                if target_blob[candidate + index] == source_window[index]:
                    run += 1
                    best = max(best, run)
                else:
                    run = 0
            if best >= min_run:
                hits.append(candidate)
    scored = []
    for candidate in hits:
        address = target_start + candidate
        other = list(md.disasm(target_blob[candidate:candidate + span], address))
        pairs = FIELDS.align(one, other)
        if not pairs:
            continue
        shape = sum(1 for i, j in pairs if FIELDS.shape(one[i]) == FIELDS.shape(other[j]))
        scored.append((pairs[0] == (0, 0), pairs and max(pairs)[0] == 0,
                      len(pairs) / max(len(one), len(other)), shape / len(pairs),
                      address, one[0].mnemonic + ' ' + one[0].op_str, len(pairs)))
    scored.sort(key=lambda row: (not row[0], -row[2], -row[3], row[4]))
    return hits, scored[:top]


def main():
    args = sys.argv[1:]
    span = int(args[args.index('--span') + 1], 0) if '--span' in args else 0x40
    if '--search' in args:
        at = args.index('--search')
        source, source_address, target = args[at + 1], int(args[at + 2], 0), args[at + 3]
        min_run = int(args[args.index('--min-run') + 1], 0) if '--min-run' in args else 8
        hits, scored = search(source, source_address, target, span, min_run, 8)
        print('  %s 0x%x -> %s: %d prefilter hits, ranked by entry alignment (span 0x%x)'
              % (source.split('/')[-1], source_address, target.split('/')[-1], len(hits), span))
        for entries, _, paired, shape, address, text, pairs in scored:
            print('    %s 0x%08x  paired=%.3f shape=%.3f pairs=%d  %s'
                  % ('ENTRY' if entries else 'inside', address, paired, shape, pairs, text))
        return
    if '--calls' in args:
        at = args.index('--calls')
        directory, source, target = args[at + 1], args[at + 2], args[at + 3]
        table = args[args.index('--table') + 1] if '--table' in args else 'docs/porting/oracle-th11-th12.json'
        document = json.load(io.open(table, encoding='utf-8'))
        row_sources = {int(row['sourceAddress'], 16) for row in document['rows']}
        row_targets = {int(row['targetAddress'], 16) for row in document['rows'] if row.get('targetAddress')}
        sites = []
        for name in sorted(os.listdir(directory)):
            if not name.endswith('.mjs'):
                continue
            for number, line in enumerate(io.open(os.path.join(directory, name), encoding='utf-8'), 1):
                for kind, pattern in (('replace', r'm\.replace\((0x[0-9a-fA-F]+),'),
                                      ('call', r'm\.call\((0x[0-9a-fA-F]+)[,)]')):
                    for match in re.finditer(pattern, line):
                        sites.append((name, number, kind, int(match.group(1), 16)))
        buckets = {'target': [], 'source-needs-touch': [], 'unknown-aligned': [], 'unknown-differs': []}
        for name, number, kind, address in sites:
            if address in row_targets:
                buckets['target'].append((name, number, kind, address))
            elif address in row_sources:
                buckets['source-needs-touch'].append((name, number, kind, address))
            else:
                result = verdict(source, address, target, address, span)
                aligned = result['first'] == (0, 0) and result.get('shape', False)
                buckets['unknown-aligned' if aligned else 'unknown-differs'].append(
                    (name, number, kind, address))
        print('  %d literal sites in %s' % (len(sites), directory))
        for label, rows in buckets.items():
            print('    %-20s %4d' % (label, len(rows)))
        print('  the question mark: unknown namespace AND not the same code in the target')
        for name, number, kind, address in buckets['unknown-differs'][:24]:
            print('    %s:%d  %s 0x%x   th12 there: %s' %
                  (name, number, kind, address, first_instruction(target, address) or 'nothing'))
        return
    if '--verdict' in args:
        at = args.index('--verdict')
        path, address = args[at + 1], int(args[at + 2], 0)
        print('  %s 0x%x: decodes as %s' % (path.split('/')[-1], address,
                                            first_instruction(path, address) or 'NOTHING'))
        return
    if '--pair' in args:
        at = args.index('--pair')
        source, source_address = args[at + 1], int(args[at + 2], 0)
        target, target_address = args[at + 3], int(args[at + 4], 0)
        report(source, source_address, target, target_address, span, False)
        return
    table, source, target = args[0], args[1], args[2]
    quiet = '--quiet' in args
    document = json.load(io.open(table, encoding='utf-8'))
    rows = [row for row in document['rows'] if row.get('targetAddress')]
    bad = []
    print('  %s: %d rows with a target' % (table, len(rows)))
    for row in rows:
        if not report(source, int(row['sourceAddress'], 16), target,
                      int(row['targetAddress'], 16), span, quiet):
            bad.append(row)
    print('  rows whose target is not the twin entrance: %d of %d' % (len(bad), len(rows)))
    for row in bad:
        print('    %s -> %s  (%s)' % (row['sourceAddress'], row['targetAddress'], row.get('confidence')))


if __name__ == '__main__':
    main()
