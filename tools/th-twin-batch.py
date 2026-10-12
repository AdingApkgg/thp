#!/usr/bin/env python3
"""Measure twins for a whole list of source addresses in one pass.

The 487 untranslated literals section 78 counted are a queue, and per-address entry-candidate
searches cost minutes each because they align every function entry. This pass inverts the order:
load both images once, turn each source window into a regex whose in-image dwords are wildcards, and
scan the target text with it (C speed, one pass per address). Only the hits - a handful - are aligned
and scored, with the same rule as everything else in this stretch: the first aligned pair must be the
first instruction of each side, or the candidate is not a twin entrance.

Output is a JSON file of measurements plus a short summary on stdout (a batch must not flood the
round's transcript):

    tools/tmp/twin-batch-<round>.json  [ {source, target, paired, pairs, shape, first, candidates} ]

Usage:
  th-twin-batch.py <src.exe> <tgt.exe> <suite-dir> <out.json> [--span 0x60] [--min-paired 0.75]
                   [--table docs/porting/oracle-th11-th12.json] [--limit N]
"""
import io
import json
import os
import re
import sys
from importlib.machinery import SourceFileLoader

FIND = SourceFileLoader('twinfind', 'tools/th-twin-find.py').load_module()
ROWS = SourceFileLoader('twinrows', 'tools/th-twin-rows.py').load_module()
FIELDS = ROWS.FIELDS


def literals(directory):
    sites = {}
    for name in sorted(os.listdir(directory)):
        if not name.endswith('.mjs'):
            continue
        for line in io.open(os.path.join(directory, name), encoding='utf-8'):
            for pattern in (r'm\.call\((0x[0-9a-fA-F]+)[,)]', r'm\.replace\((0x[0-9a-fA-F]+),'):
                for match in re.finditer(pattern, line):
                    address = int(match.group(1), 16)
                    sites.setdefault(address, []).append(name)
    return sites


def pattern_and_wild(source_blob, at, span):
    window = source_blob[at:at + span]
    wild = [False] * len(window)
    for offset in range(len(window)):
        for start in range(max(0, offset - 3), min(offset + 1, len(window) - 3)):
            word = int.from_bytes(window[start:start + 4], 'little')
            if 0x10000 <= word < 0x08000000:
                wild[offset] = True
    return window, wild


def literal_runs(wild):
    runs, current = [], 0
    for flag in wild + [True]:
        if flag:
            runs.append(current)
            current = 0
        else:
            current += 1
    return max(runs) if runs else 0


def entry_bytes(blob):
    """Every function-entry candidate in an image, in one pass.

    The wildcard scan cannot match a window whose literal run is short, and section 80's relaxation
    only reached 31 more. The fallback inverts the cost: precompute the entry list once, then accept
    a candidate only when the source's *first instruction* agrees byte for byte outside the wildcard
    positions, and disassemble/align the survivors. Disassembling all 65k entries per address is
    minutes; comparing a handful of bytes is not."""
    return [index for index in range(1, len(blob) - 0x60)
            if blob[index - 1] in (0xcc, 0xc3, 0xe9, 0xeb) or index % 16 == 0]


def derive(source_blob, target_blob, source_start, target_start, bases, queue, md, span=0x60):
    """Derive rows for addresses INSIDE an already-anchored function.

    A row maps a function entry to its twin. An address inside that function - the stand-in's
    relocated block at 0x402551 is the standing example - is not a second function and cannot be
    found by a window scan, but it is the k-th instruction of a function whose k-th instruction is
    already measured. So: for each anchored row, align one 0x400-byte window pair, build the map from
    the source's instruction addresses to the target's, and hand back the derived target for every
    queued address that starts exactly on a source instruction. Each derivation is then verified on
    its own window by the same entry rule as everything else - a derivation is a measurement, and a
    measurement has to be checkable.
    """
    found = {}
    for base_source, base_target in bases:
        source_at, target_at = base_source - source_start, base_target - target_start
        one = list(md.disasm(source_blob[source_at:source_at + 0x400], base_source))
        other = list(md.disasm(target_blob[target_at:target_at + 0x400], base_target))
        if not one or not other:
            continue
        pairs = FIELDS.align(one, other)
        inside = {one[i].address: other[j].address for i, j in pairs
                  if i < len(one) and j < len(other)}
        for address in queue:
            if address not in inside:
                continue
            candidate = inside[address]
            window, wild = pattern_and_wild(source_blob, address - source_start, span)
            first = list(md.disasm(bytes(window), address))
            second = list(md.disasm(target_blob[candidate - target_start:
                                                candidate - target_start + span], candidate))
            pairs = FIELDS.align(first, second)
            if not pairs or pairs[0] != (0, 0):
                continue
            shape = sum(1 for i, j in pairs if FIELDS.shape(first[i]) == FIELDS.shape(second[j]))
            shape /= len(pairs)
            paired = len(pairs) / max(len(first), len(second))
            if shape < 0.999 or paired < 0.8:
                continue
            previous = found.get(address)
            if previous is None or paired > previous['paired']:
                found[address] = {'source': hex(address), 'target': hex(candidate),
                                  'paired': round(paired, 3), 'pairs': len(pairs),
                                  'instructions': [len(first), len(second)],
                                  'first': '%s %s' % (second[0].mnemonic, second[0].op_str),
                                  'from': hex(base_source), 'via': hex(base_target)}
    return found


def derive_by_entry(source_blob, target_blob, source_start, target_start, source_entries,
                    rows_by_source, queue, md, span=0x60, reach=0x300, tries=8):
    """Derive every queued address from the entry of the function it lives in.

    The first derivation aligned each anchored pair once and read a global instruction map, which only
    covers as far as the aligner keeps pairing. This one goes the other way per address: find the
    function entry the address sits in (the entry table is precomputed), take that entry's row, align
    the two functions from their starts, and read the same-index instruction. Several candidate
    entries are tried, because an aligned candidate that is not really an entry has no row and cannot
    contribute. Every derivation is verified on its own window.
    """
    import bisect
    found = {}
    for address in queue:
        at = bisect.bisect_right(source_entries, address)
        candidates = [source_entries[i] for i in range(max(0, at - tries), at)]
        best = None
        for base_source in reversed(candidates):
            if address - base_source >= reach:
                continue
            base_target = rows_by_source.get(base_source)
            if base_target is None:
                continue
            source_at, target_at = base_source - source_start, base_target - target_start
            one = list(md.disasm(source_blob[source_at:source_at + reach], base_source))
            other = list(md.disasm(target_blob[target_at:target_at + reach], base_target))
            if not one or not other:
                continue
            pairs = FIELDS.align(one, other)
            derived = None
            for i, j in pairs:
                if i < len(one) and j < len(other) and one[i].address == address:
                    derived = other[j].address
                    break
            if derived is None:
                continue
            window, wild = pattern_and_wild(source_blob, address - source_start, span)
            first = list(md.disasm(bytes(window), address))
            second = list(md.disasm(target_blob[derived - target_start:
                                                derived - target_start + span], derived))
            check = FIELDS.align(first, second)
            if not check or check[0] != (0, 0):
                continue
            shape = sum(1 for i, j in check if FIELDS.shape(first[i]) == FIELDS.shape(second[j]))
            shape /= len(check)
            paired = len(check) / max(len(first), len(second))
            if shape < 0.999 or paired < 0.8:
                continue
            if best is None or paired > best['paired']:
                best = {'source': hex(address), 'target': hex(derived), 'paired': round(paired, 3),
                        'pairs': len(check), 'instructions': [len(first), len(second)],
                        'first': '%s %s' % (second[0].mnemonic, second[0].op_str),
                        'from': hex(base_source), 'via': hex(base_target)}
        if best is not None:
            found[address] = best
    return found


def immediate_calls(md, blob, start, span):
    """Every direct call in a window, as address -> address (the call's resolved target)."""
    found = []
    for insn in md.disasm(blob[start:start + span], start):
        if insn.mnemonic != 'call' or not insn.operands:
            continue
        operand = insn.operands[0]
        if operand.type == ROWS.capstone.CS_OP_IMM:
            found.append((insn.address, operand.imm))
    return found


def call_targets(md, blob, base, step=0x4000):
    """The real function entries of an image: every direct `call rel32` target, plus padding entries.

    `entry_bytes` accepts any 16-aligned address, which is why the first container pass measured only
    nine of 127 of them: the "entry" it handed back was usually a 16-aligned address INSIDE a
    function, and a mid-function window has no reason to agree with a function start in the target
    image. A function that is called is a function; an address that merely aligns is a guess.
    """
    found = set()
    for start in range(0, len(blob) - 0x20, step):
        end = min(len(blob), start + step + 0x10)
        # Disassembly must not be cut mid-instruction at the seam: start the next block on an
        # instruction boundary by carrying the tail, which is what the padding check below is for.
        for insn in md.disasm(blob[start:end], base + start):
            if insn.mnemonic == 'call' and insn.operands:
                operand = insn.operands[0]
                if operand.type == ROWS.capstone.CS_OP_IMM:
                    found.add(operand.imm)
    for index in range(1, len(blob) - 0x60):
        if blob[index - 1] in (0xcc, 0xc3, 0xe9, 0xeb):
            found.add(base + index)
    return sorted(found)


def derive_calls(source_blob, target_blob, source_start, target_start, bases, queue, md,
                 span=0x1000):
    """Derive a queued address from a CALL inside an already-anchored function.

    This is how the namespace is actually recovered: a function in the table calls functions that are
    not, and the call's own displacement says which target function each one is - no guessing, because
    the pair of instructions is aligned by the region around it. The measured claim is then the same
    as everywhere else: align the derived pair on its own window and require the entry rule to hold.
    """
    queue_set = set(queue)
    found = {}
    for base_source, base_target in bases:
        source_at, target_at = base_source - source_start, base_target - target_start
        if source_at < 0 or target_at < 0:
            continue
        one = list(md.disasm(source_blob[source_at:source_at + span], base_source))
        other = list(md.disasm(target_blob[target_at:target_at + span], base_target))
        if not one or not other:
            continue
        pairs = FIELDS.align(one, other)
        by_source = {one[i].address: other[j].address for i, j in pairs if j < len(other)}
        for insn in one:
            if insn.mnemonic != 'call' or not insn.operands:
                continue
            operand = insn.operands[0]
            if operand.type != ROWS.capstone.CS_OP_IMM:
                continue
            if operand.imm not in queue_set:
                continue
            if insn.address not in by_source:
                continue
            window = list(md.disasm(source_blob[operand.imm - source_start:
                                                operand.imm - source_start + 0x60], operand.imm))
            if not window:
                continue
            # The target of the call can be recovered exactly: the aligned partner instruction has its
            # own resolved displacement, and reconstructing it from the bytes is the whole point.
            partner = by_source[insn.address]
            target_bytes = target_blob[partner - target_start:partner - target_start + 16]
            calls = immediate_calls(md, target_blob, partner - target_start, 16)
            if not calls:
                continue
            derived = calls[0][1]
            second = list(md.disasm(target_blob[derived - target_start:
                                               derived - target_start + 0x60], derived))
            check = FIELDS.align(window, second)
            if not check or check[0] != (0, 0):
                continue
            shape = sum(1 for i, j in check if FIELDS.shape(window[i]) == FIELDS.shape(second[j]))
            shape /= len(check)
            paired = len(check) / max(len(window), len(second))
            if shape < 0.999 or paired < 0.8:
                continue
            previous = found.get(operand.imm)
            if previous is None or paired > previous['paired']:
                found[operand.imm] = {'source': hex(operand.imm), 'target': hex(derived),
                                       'paired': round(paired, 3), 'pairs': len(check),
                                       'instructions': [len(window), len(second)],
                                       'first': '%s %s' % (second[0].mnemonic, second[0].op_str),
                                       'from': hex(base_source), 'via': 'call at ' + hex(insn.address)}
    return found


def main():
    args = sys.argv[1:]
    source, target, directory, out = args[0], args[1], args[2], args[3]
    span = int(args[args.index('--span') + 1], 0) if '--span' in args else 0x60
    floor = float(args[args.index('--min-paired') + 1]) if '--min-paired' in args else 0.75
    table = args[args.index('--table') + 1] if '--table' in args else 'docs/porting/oracle-th11-th12.json'
    limit = int(args[args.index('--limit') + 1], 0) if '--limit' in args else 0
    min_run = int(args[args.index('--min-run') + 1], 0) if '--min-run' in args else 8

    document = json.load(io.open(table, encoding='utf-8'))
    known = {int(row['sourceAddress'], 16) for row in document['rows'] if row.get('targetAddress')}
    target_addresses = {int(row['targetAddress'], 16) for row in document['rows'] if row.get('targetAddress')}
    source_start, source_blob, _, _ = FIND.image_text(source)
    target_start, target_blob, _, _ = FIND.image_text(target)
    md = ROWS.capstone.Cs(ROWS.capstone.CS_ARCH_X86, ROWS.capstone.CS_MODE_32)
    md.detail = True

    sites = literals(directory)
    if '--addresses' in args:
        # An explicit list, so a measuring pass can be aimed at addresses the suite literals do not
        # name - e.g. the enclosing function entries of a queue of unresolved mid-function addresses.
        listed = json.load(io.open(args[args.index('--addresses') + 1], encoding='utf-8'))
        sites = {int(entry, 16) if isinstance(entry, str) else int(entry): ['<listed>']
                 for entry in listed}
    queue = [a for a in sorted(sites) if a not in known and a not in target_addresses]
    if limit:
        queue = queue[:limit]
    if '--containers' in args:
        # The first stage of the two-stage pipeline: for every queued address, the real entry of the
        # function that contains it. Deduplicated and written out, so the entries can be measured
        # and the addresses derived from them afterwards.
        import bisect
        source_entries = call_targets(md, source_blob, source_start)
        reach = int(args[args.index('--reach') + 1], 0) if '--reach' in args else 0x800
        containers, without = {}, []
        for address in queue:
            at = bisect.bisect_right(source_entries, address)
            if at == 0 or address - source_entries[at - 1] >= reach:
                without.append(address)
                continue
            containers.setdefault(source_entries[at - 1], []).append(address)
        out = args[args.index('--containers') + 1]
        io.open(out, 'w', encoding='utf-8', newline='').write(
            json.dumps(['0x%x' % entry for entry in sorted(containers)], indent=1).replace('\n', '\r\n'))
        print('  %d queued addresses -> %d real enclosing entries from %d call-top targets '
              '(%d without an entry within 0x%x) -> %s' %
              (len(queue), len(containers), len(source_entries), len(without), reach, out))
        print('  first entries: %s' % ', '.join('0x%x' % a for a in sorted(containers)[:8]))
        return
    if '--derive-calls' in args:
        bases = [(int(row['sourceAddress'], 16), int(row['targetAddress'], 16))
                 for row in document['rows']
                 if row.get('targetAddress') and row.get('confidence') in ('anchored', 'measured')]
        found = derive_calls(source_blob, target_blob, source_start, target_start, bases, queue, md)
        derived = sorted(found.values(), key=lambda row: -row['paired'])
        io.open(out, 'w', encoding='utf-8', newline='').write(
            json.dumps({'queue': len(queue), 'bases': len(bases), 'measured': derived,
                        'unresolved': [{'source': hex(a)} for a in queue if a not in found]},
                       ensure_ascii=False, indent=2).replace('\n', '\r\n'))
        print('  queue %d over %d anchored bases: derived %d from call displacements, unresolved %d -> %s'
              % (len(queue), len(bases), len(derived), len(queue) - len(derived), out))
        for row in derived[:18]:
            print('    %s -> %s  paired=%.3f pairs=%d  %s via %s' %
                  (row['source'], row['target'], row['paired'], row['pairs'], row['first'], row['via']))
        return
    if '--derive-entry' in args:
        rows_by_source = {int(row['sourceAddress'], 16): int(row['targetAddress'], 16)
                          for row in document['rows'] if row.get('targetAddress')}
        # entry_bytes returns offsets inside the blob; the queue is absolute addresses. Section 297's
        # checker self-check exists because that mistake produced a page of NOT A BOUNDARY verdicts,
        # and the first version of this mode produced zero derivations for the same reason.
        #
        # The source side uses the CALL-TARGET entry index: a 16-aligned address inside a function is
        # not a container, and treating it as one is why the first container pass measured nine of 127.
        source_entries = call_targets(md, source_blob, source_start)
        found = derive_by_entry(source_blob, target_blob, source_start, target_start,
                               source_entries, rows_by_source, queue, md)
        derived = sorted(found.values(), key=lambda row: -row['paired'])
        io.open(out, 'w', encoding='utf-8', newline='').write(
            json.dumps({'queue': len(queue), 'sourceEntries': len(source_entries),
                        'measured': derived,
                        'unresolved': [{'source': hex(address)} for address in queue
                                       if address not in found]},
                       ensure_ascii=False, indent=2).replace('\n', '\r\n'))
        print('  queue %d over %d source entries: derived %d, still unresolved %d -> %s' %
              (len(queue), len(source_entries), len(derived), len(queue) - len(derived), out))
        for row in derived[:18]:
            print('    %s -> %s  paired=%.3f pairs=%d  via %s->%s' %
                  (row['source'], row['target'], row['paired'], row['pairs'], row['from'], row['via']))
        return
    measurements, unresolved = [], []
    if '--derive' in args:
        bases = [(int(row['sourceAddress'], 16), int(row['targetAddress'], 16))
                 for row in document['rows']
                 if row.get('targetAddress') and row.get('confidence') in ('anchored', 'measured')]
        found = derive(source_blob, target_blob, source_start, target_start, bases, queue, md)
        derived = sorted(found.values(), key=lambda row: -row['paired'])
        io.open(out, 'w', encoding='utf-8', newline='').write(
            json.dumps({'queue': len(queue), 'bases': len(bases), 'measured': derived,
                        'unresolved': [{'source': hex(address)} for address in queue
                                       if address not in found]},
                       ensure_ascii=False, indent=2).replace('\n', '\r\n'))
        print('  queue %d over %d anchored bases: derived %d, still unresolved %d -> %s' %
              (len(queue), len(bases), len(derived), len(queue) - len(derived), out))
        for row in derived[:18]:
            print('    %s -> %s  paired=%.3f pairs=%d  via %s->%s' %
                  (row['source'], row['target'], row['paired'], row['pairs'], row['from'], row['via']))
        return
    # The candidate list must be REAL entries, in both images: `entry_bytes` accepts any 16-aligned
    # address, and after the container pass that produced eight measurements of which several were a
    # first instruction like `add byte ptr [eax], al` a few bytes past a call - a guess that merely
    # aligns. A function that is called is a function.
    entries = ([address - target_start for address in call_targets(md, target_blob, target_start)
                if 0 < address - target_start < len(target_blob) - span]
               if '--fallback' in args else None)
    for address in queue:
        window, wild = pattern_and_wild(source_blob, address - source_start, span)
        run = literal_runs(wild)
        if run < min_run:
            unresolved.append({'source': hex(address),
                               'why': 'window has no literal run of %d (longest %d)' % (min_run, run)})
            continue
        pattern = b''.join(b'.' if flag else re.escape(bytes([byte]))
                           for byte, flag in zip(window, wild))
        if entries is None:
            hits = [target_start + match.start() for match in re.finditer(pattern, target_blob, re.DOTALL)]
        else:
            first = next(iter(md.disasm(bytes(window), address)), None)
            ohits = []
            if first is not None:
                literal = [(index, window[index]) for index in range(len(first.bytes))
                           if not wild[index]]
                for candidate in entries:
                    if all(target_blob[candidate + index] == byte for index, byte in literal):
                        ohits.append(target_start + candidate)
            hits = ohits
        one = list(md.disasm(bytes(window), address))
        best = None
        for hit in hits[:64]:
            off = hit - target_start + span
            other = list(md.disasm(target_blob[hit - target_start:off], hit))
            pairs = FIELDS.align(one, other)
            if not pairs or pairs[0] != (0, 0):
                continue
            shape = sum(1 for i, j in pairs if FIELDS.shape(one[i]) == FIELDS.shape(other[j])) / len(pairs)
            paired = len(pairs) / max(len(one), len(other))
            if shape < 0.999:
                continue
            if best is None or paired > best['paired']:
                best = {'source': hex(address), 'target': hex(hit), 'paired': round(paired, 3),
                        'pairs': len(pairs), 'instructions': [len(one), len(other)],
                        'first': '%s %s' % (other[0].mnemonic, other[0].op_str) if other else '',
                        'uses': sorted(set(sites[address]))[:4], 'hits': len(hits)}
        if best and best['paired'] >= floor:
            measurements.append(best)
        else:
            unresolved.append({'source': hex(address), 'why': 'no entrance-aligned hit',
                               'best': best, 'uses': sorted(set(sites[address]))[:4]})
    measurements.sort(key=lambda row: -row['paired'])
    io.open(out, 'w', encoding='utf-8', newline='').write(
        json.dumps({'queue': len(queue), 'measured': measurements, 'unresolved': unresolved},
                   ensure_ascii=False, indent=2).replace('\n', '\r\n'))
    print('  queue %d, measured %d at paired >= %.2f, unresolved %d -> %s' %
          (len(queue), len(measurements), floor, len(unresolved), out))
    for row in measurements[:15]:
        print('    %s -> %s  paired=%.3f pairs=%d/%d  %s' %
              (row['source'], row['target'], row['paired'], row['pairs'], max(row['instructions']),
               row['first']))


if __name__ == '__main__':
    main()
