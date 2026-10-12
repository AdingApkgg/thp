#!/usr/bin/env python3
"""Re-measure the globals table with two structural guards, and write only what they settle.

Section 90's row for th11 0x4c3808 was a candidate whose "twin site" disassembled as int3 padding: the
tool matched a 8-byte window and read the counterpart's address out of noise. Two guards remove that
whole class of answer:

  * ALIGNMENT - a reference site counts only if it lies inside a real instruction, and the twin site it
    points at must lie inside a real instruction too. Both are established by linear disassembly from
    the enclosing function entry (the entry index is every direct call target plus padding entries, the
    same index the batch tool derives interiors from), so "inside an instruction" is a fact about the
    image rather than a guess about the bytes.
  * SHAPE - the instruction at the source site and the instruction at the twin site must have the same
    mask after every in-image dword is replaced, because the same engine instruction in another title
    differs only in which global it names. A padding site cannot satisfy this.

A row is written as ready only when at least two alignment-and-shape-checked sites agree on the same
counterpart, which is the property the old table recorded but nobody enforced.

Usage: th-twin-globals-table.py [--table docs/porting/oracle-globals-th11-th12.json]
        [--from H:/Games/th/11/th11.exe] [--to H:/Games/th/12/th12.exe] [--only-unsettled]
        [--min-sites 2] [--write] [--report N]
"""
import importlib.util
import io
import json
import os
import re
import struct
import sys
from collections import Counter

_HERE = os.path.dirname(os.path.abspath(__file__))


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


twinfind = load('twinfind', os.path.join(_HERE, 'th-twin-find.py'))
batch = load('twinbatch', os.path.join(_HERE, 'th-twin-batch.py'))
import capstone

MD = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
MD.detail = True  # call_targets reads instruction operands, which capstone only decodes with detail
ADDRESS = re.compile(r'0x[0-9a-f]{5,8}')


class Aligned:
    """Whether an address lies inside an instruction, decided from its function entry."""

    def __init__(self, blob, base, entries):
        self.blob, self.base, self.entries = blob, base, sorted(entries)
        self.cache = {}

    def instruction(self, address):
        offset = address - self.base
        if offset < 0 or offset >= len(self.blob):
            return None
        entry = None
        for candidate in self.entries:
            if candidate <= address:
                entry = candidate
            else:
                break
        if entry is None or address - entry > 0x2000:
            return None
        key = entry
        if key not in self.cache:
            span = min(len(self.blob) - (entry - self.base), 0x2000)
            found = []
            for insn in MD.disasm(self.blob[entry - self.base:entry - self.base + span], entry):
                found.append(insn)
            self.cache[key] = found
        for insn in self.cache[key]:
            if insn.address == address:
                return insn
            if insn.address < address < insn.address + insn.size:
                # the address is inside this instruction's bytes: the operand, not the start
                return insn
        return None


def shape(insn):
    text = '%s %s' % (insn.mnemonic.lower(), insn.op_str.lower())
    return ADDRESS.sub('#', text)


def in_image_positions(blob, low=0x00401000, high=0x01000000):
    """Every byte offset at which a dword currently holds something that could be an in-image address.

    The twin window must carry the counterpart at the same offset the source carried its global, and a
    counterpart is an address inside the target image. That is a cheap necessary condition, and it turns
    the per-site scan over the whole .text into a scan over the few thousand places that could possibly
    hold one - the first version of this tool scored a 600 KiB window for every reference site, which
    made a 25-row table take longer than the round had.
    """
    positions = []
    for at in range(0, len(blob) - 4):
        value = struct.unpack_from('<I', blob, at)[0]
        if low <= value < high:
            positions.append(at)
    return positions


def measure(source, target, value, source_aligned, target_aligned, target_positions,
            span=28, min_run=12):
    from_va, from_blob, from_base, _ = twinfind.image_text(source)
    to_va, to_blob, to_base, to_ceiling = twinfind.image_text(target)
    packed = struct.pack('<I', value)
    offsets, at = [], from_blob.find(packed)
    while at >= 0:
        offsets.append(at)
        at = from_blob.find(packed, at + 1)
    detail, candidates, checked = [], Counter(), 0
    for where in offsets:
        site = from_base + where
        insn = source_aligned.instruction(site)
        if insn is None or insn.mnemonic in ('int3', 'nop'):
            detail.append((site, None, 'not in an instruction'))
            continue
        start = max(0, where - 4)
        if start + span > len(from_blob):
            continue
        signature = twinfind.normalize(from_blob[start:start + span], from_base, 0x10000000, span)
        held = where - start
        best = None
        for position in target_positions:
            candidate = position - held
            if candidate < 0 or candidate + span > len(to_blob):
                continue
            run, _, _ = twinfind.score(signature, to_blob, candidate)
            if run >= min_run and (best is None or run > best[0]):
                best = (run, candidate)
        if best is None:
            detail.append((site, None, 'no twin window'))
            continue
        run, candidate = best
        twin_site = to_base + candidate + held
        twin = target_aligned.instruction(twin_site)
        if twin is None or twin.mnemonic in ('int3', 'nop'):
            detail.append((site, twin_site, 'twin site is not in an instruction'))
            continue
        if shape(insn) != shape(twin):
            detail.append((site, twin_site, 'shape differs: %s vs %s' % (shape(insn), shape(twin))))
            continue
        found = struct.unpack_from('<I', to_blob, candidate + held)[0]
        checked += 1
        candidates[found] += 1
        detail.append((site, twin_site, '0x%08x' % found))
    return from_va, offsets, detail, candidates, checked


def main():
    table_path = ('docs/porting/oracle-globals-th11-th12.json')
    source, target = 'H:/Games/th/11/th11.exe', 'H:/Games/th/12/th12.exe'
    args = sys.argv[1:]
    for flag, default in (('--table', table_path), ('--from', source), ('--to', target)):
        if flag in args:
            if flag == '--table':
                table_path = args[args.index(flag) + 1]
            elif flag == '--from':
                source = args[args.index(flag) + 1]
            else:
                target = args[args.index(flag) + 1]
    min_sites = int(args[args.index('--min-sites') + 1]) if '--min-sites' in args else 2
    only_unsettled = '--only-unsettled' in args
    write = '--write' in args

    from_va, from_blob, from_base, _ = twinfind.image_text(source)
    to_va, to_blob, to_base, _ = twinfind.image_text(target)
    source_aligned = Aligned(from_blob, from_base, batch.call_targets(MD, from_blob, from_base))
    target_aligned = Aligned(to_blob, to_base, batch.call_targets(MD, to_blob, to_base))
    target_positions = in_image_positions(to_blob)
    print('  target image: %d byte offsets hold a possible in-image address' % len(target_positions))

    document = json.load(io.open(table_path, encoding='utf-8'))
    settled = 0
    for row in document['rows']:
        if row.get('target') != 'th12' or 'sourceAddress' not in row:
            continue
        if only_unsettled and row.get('ready') is True:
            continue
        value = int(row['sourceAddress'], 16)
        _, offsets, detail, candidates, checked = measure(
            source, target, value, source_aligned, target_aligned, target_positions)
        top = candidates.most_common(3)
        ready = bool(top) and top[0][1] >= min_sites
        row['checkedSites'] = checked
        row['candidates'] = [{'address': '0x%08x' % address, 'sites': count, 'of': checked}
                             for address, count in top]
        if ready:
            row['targetAddress'] = top[0][0].to_bytes(4, 'little').hex()
            row['targetAddress'] = '0x%08x' % top[0][0]
            row['agreeingSites'] = top[0][1]
            row['ready'] = True
            row.pop('withdrawn', None)
            settled += 1
        print('  %s refs %3d aligned+shaped %2d  %-28s %s'
              % (row['sourceAddress'], len(offsets), checked,
                 (' '.join('0x%x:%d' % (a, c) for a, c in top)) or 'none',
                 'READY' if ready else 'candidate'))
        for site, twin, note in detail[:2]:
            print('      0x%08x -> %s %s'
                  % (site, ('0x%08x' % twin) if twin else '---', note))
    print('  rows settled by the guards: %d' % settled)

    # A third route, for a global whose own reference sites do not survive the guards. The data block
    # it lives in moved between titles as a whole, so if two settled neighbours inside a short window
    # share one shift, that shift is measured - and the derived address carries its derivation with it,
    # which is the difference between this and the guess section 90 removed.
    derived = 0
    if '--derive-block' in args:
        window = int(args[args.index('--window') + 1], 0) if '--window' in args else 0x800
        known = [r for r in document['rows']
                 if r.get('ready') and r.get('targetAddress') and r.get('derivedFrom') is None]
        for row in document['rows']:
            if row.get('ready') or 'sourceAddress' not in row or row.get('target') != 'th12':
                continue
            source = int(row['sourceAddress'], 16)
            neighbours = [(n, int(n['targetAddress'], 16) - int(n['sourceAddress'], 16))
                          for n in known
                          if 0 < abs(int(n['sourceAddress'], 16) - source) <= window]
            shifts = {shift for _, shift in neighbours}
            if len(shifts) != 1:
                continue
            shift = shifts.pop()
            if len(neighbours) < 2:
                continue
            address = source + shift
            if not (0x00401000 <= address < 0x01000000):
                continue
            row['targetAddress'] = '0x%08x' % address
            row['ready'] = True
            row['agreeingSites'] = 0
            row['checkedSites'] = 0
            row['derivedFrom'] = sorted('0x%08x' % int(n['sourceAddress'], 16) for n, _ in neighbours)
            row['derivation'] = ('block shift 0x%+x measured on %d settled neighbour(s) inside 0x%x; '
                                 'the row has no instruction-aligned, shape-matching site of its own'
                                 % (shift, len(neighbours), window))
            row.pop('withdrawn', None)
            derived += 1
            print('  %s derived -> 0x%08x by shift 0x%+x from %s'
                  % (row['sourceAddress'], address, shift, ','.join(row['derivedFrom'])))
        print('  rows derived from a measured block shift: %d' % derived)
    if write:
        io.open(table_path, 'w', encoding='utf-8', newline='').write(
            json.dumps(document, ensure_ascii=False, indent=2).replace('\n', '\r\n'))
        print('  wrote %s' % table_path)


main()
