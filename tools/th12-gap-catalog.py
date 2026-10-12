"""Catalog the twenty title 12 slots nothing in the port reproduces, so the mirror has a spec.

Section 351 split the 55 uncandidated slots with a whole-word pass and a bit pass, and the third
part - the 20 slots where not one changing native bit is reproduced by any port bit - is the layout
gap proper. A gap with a list of offsets is still not a spec; this reads each of the 20 with the
campaign's own field profiler (tools/anm-field-profile.py, which now carries title 12) and writes
down the writers, the delta each handler produces, whether the delta follows the argument, and a
family. The families are decided by rules stated here, not by eye.

Usage: py -3 tools/th12-gap-catalog.py
"""
import importlib, json, sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
PROFILE = importlib.import_module('anm-field-profile')

SLOTS = ['0x24', '0x28', '0x40', '0x44', '0x50', '0x54', '0x58', '0x5c', '0x68', '0x74',
         '0x78', '0xe0', '0x158', '0x208', '0x214', '0x218', '0x21c', '0x220', '0x3fc',
         '0x480']
POINTER_CONSTANTS = {0x4b2ed0}
TIMER_CONSTANTS = {0x2711, 0xffffd8ef}
COUNTER_DELTAS = {0xffffffff, 0x1}


SMALL_ARGUMENT_DELTAS = {0x1, 0x2, 0x3, 0x4, 0x8, 0xd, 0xf, 0x10, 0x80000000}


def family_of(deltas, arg_clean, pairs):
    """Stated rules, so the family of a slot can be argued with rather than believed."""
    if deltas & POINTER_CONSTANTS:
        return 'pointer constant: the handler installs an address'
    if deltas == {0x1}:
        return 'marker: the handler sets a single bit'
    if deltas <= SMALL_ARGUMENT_DELTAS:
        return 'argument bits: the delta is a bit of the argument'
    if any(d >= 0x1000 for d in deltas):
        return 'step or timer: a constant the handler adds'
    return 'mixed'


def main():
    corpus = PROFILE.corpus_of(12)
    cases = json.loads(corpus.read_text(encoding='utf-8'))['cases']
    catalog = []
    for slot in SLOTS:
        offset = int(slot, 16)
        code = PROFILE.code_side(12, slot)
        by_op, values, variants = defaultdict(set), defaultdict(set), defaultdict(set)
        moved = 0
        for case in cases:
            if case.get('fault') or 'before' not in case:
                continue
            a, b = bytes.fromhex(case['before']), bytes.fromhex(case['context'])
            delta = int.from_bytes(a[offset:offset + 4], 'little') ^ int.from_bytes(
                b[offset:offset + 4], 'little')
            if not delta:
                continue
            moved += 1
            by_op[case['op']].add(delta)
            values[(case['op'], delta)].add(str(case.get('value')))
            variants[(case['op'], delta)].add(case.get('variant'))
        deltas = {d for per in by_op.values() for d in per}
        arg_clean = sum(1 for v in values.values() if len(v) == 1)
        var_clean = sum(1 for v in variants.values() if len(v) == 1)
        catalog.append({
            'nativeSlot': slot,
            'casesThatChangeIt': moved,
            'writers': sorted(by_op),
            'deltas': ['0x%x' % d for d in sorted(deltas)][:8],
            'deltaDeterminedByArgument': [arg_clean, len(values)],
            'deltaDeterminedByVariant': [var_clean, len(variants)],
            'codeSideWriters': sorted({op for op, _ in code}),
            'family': family_of(deltas, arg_clean, len(values)),
        })
    families = defaultdict(list)
    for row in catalog:
        families[row['family']].append(row['nativeSlot'])
    out = ROOT / 'docs/porting/anm-gap-12.json'
    gap = json.loads((ROOT / 'docs/porting/th12-anm-verified.json').read_text(encoding='utf-8'))
    bit = gap['bitPassOverUnmappedSlots']['summary']
    # The port now reports where its own named members sit, so a candidate bit can be described by
    # the name of the field that carries it - and by how far into that field it lies, because the
    # port's representation of a title's field is a bit of a word of the port's own.
    named = sorted(((r['offset'], r['name']) for r in gap['namedMemberOffsets']),
                  key=lambda pair: pair[0])
    def describe(offset):
        holder = None
        for at, name in named:
            if at <= offset:
                holder = (at, name)
            else:
                break
        at, name = holder if holder else (0, 'before every named member')
        within = offset - at
        return name if within == 0 else '%s+0x%x' % (name, within)
    candidates = defaultdict(lambda: defaultdict(int))
    for row in gap['bitPassOverUnmappedSlots']['rows']:
        for key in row['closeMatch']:
            offset, bitIndex = (int(x) for x in key.split(':'))
            candidates[row['nativeSlot']][(offset, bitIndex)] += 1
    for row in catalog:
        seen = candidates.get(row['nativeSlot'], {})
        byName = defaultdict(set)
        for (offset, bitIndex) in sorted(seen):
            byName[describe(offset)].add(bitIndex)
        row['portNames'] = {name: sorted(bits) for name, bits in sorted(byName.items())}
    # The catalogue is the twenty with no reproduced bit, and its portNames are empty by
    # construction. The naming is the point for the rest of the gap: those slots are the seed
    # and edge class of section 351, and now each carries the name of the port field that
    # reproduces its changes.
    namedSlots = [r['nativeSlot'] for r in catalog if r['portNames']]
    UNCATALOGUED = sorted((d['nativeSlot'] for d in gap['unmappedSlots']
                          if d['nativeSlot'] not in {r['nativeSlot'] for r in catalog}),
                         key=lambda x: int(x, 16))
    elsewhere = []
    for slot in UNCATALOGUED:
        byName = defaultdict(set)
        for (offset, bitIndex) in sorted(candidates.get(slot, {})):
            byName[describe(offset)].add(bitIndex)
        elsewhere.append({'nativeSlot': slot,
                         'portNames': {name: sorted(bits) for name, bits in
                                       sorted(byName.items())}})
    report = {
        'title': 12,
        'portMemberOffsets': [{'name': r['name'], 'offset': '0x%x' % r['offset']}
                             for r in gap['namedMemberOffsets']],
        'namedCandidates': {'slots': namedSlots, 'of': len(catalog)},
        'namedElsewhere': {'slots': len(elsewhere), 'of': len(UNCATALOGUED),
                          'why': 'the rest of the gap: these reproduce their changes through the '
                                 'port fields named beside them, which is what makes them a seed '
                                 'or an edge matter rather than a layout gap',
                          'rows': elsewhere},
        'whyTheTwenty': 'section 351: %d of %d changing native bits of the 55 uncandidated slots are '
                       'reproduced by some port bit, over %d slots; the slots with none of their '
                       'bits reproduced are the layout gap proper' % (
                           bit['matchedExactly'], bit['nativeChangingBits'],
                           bit['slotsWhollyOrPartlyMatched']),
        'wholeWordDeltaPass': gap['deltaSummary'],
        'slots': catalog,
        'families': {name: slots for name, slots in sorted(families.items())},
        'specReading': 'a mirror for these slots has to place the title\'s own word at the '
                      'original\'s offset and have the named handler write the named delta shape; '
                      'the argument-determined rows say the value is a function of the '
                      'instruction the case carries',
        'provenance': {'reader': 'tools/anm-field-profile.py, corpus map now carries title 12',
                       'corpus': 'artifacts/th12/anm-native.json',
                       'corpusSha256': PROFILE.__dict__.get('CORPUS') and None},
    }
    out.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print('  %d slots catalogued into %s' % (len(catalog), out.relative_to(ROOT)))
    for name, slots in sorted(families.items()):
        print('    %-58s %d  %s' % (name, len(slots), ' '.join(slots)))
    for row in catalog:
        print('    %-6s %-52s %-22s %s' % (row['nativeSlot'], row['family'],
              'arg %d/%d' % tuple(row['deltaDeterminedByArgument']),
              ' '.join(row['deltas'][:4])))


main()
