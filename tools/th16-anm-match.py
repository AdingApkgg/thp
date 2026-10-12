"""Match each measured TH16 handler to the port's canonical body by value, not by shape.

Sources, both already in the repository: artifacts/th16/anm-signatures.json (every dispatched handler of
the original, reduced to the slots it changed) and artifacts/th16/port-sweep/sweep.json (every
canonical body the port can reach under the same eight-case grid). The quantity vector is small on
purpose and every member of it is named and justified in section 302 and the probe headers:

    delta             the original's +0x28 less the code base, against the port's own difference
    flags             the original's +0x18  against the port's flags
    title flags       the original's +0x530 against the port's title flag word
    timer, fraction   the original's +0x544 and +0x548 against the port's timer and its fraction
                      (from the op 6 handler text: cvttss2si into +0x544, movss of the fraction
                       into +0x548)
    integer 0         the original's +0x4ac against the port's integers[0]

A handler and a body agree on a case when all six quantities agree. A row is written only when a body
agrees on all eight cases; the row's witness count is the number of cases that witness it.
"""
import io
import json

ROOT = 'docs/porting'
GRID = [[0, 0, 0], [0, 0, 1], [18, 0, 0], [18, 0, 1], [1, 1, 0], [1, 1, 1], [2, 0, 1], [0, 1, 1]]
RELOAD_NATIVE = 0x8FFFF000   # position zero less the code base: the class that reloads the pointer
RELOAD_PORT = 0xFFFFFFFF


def as_int(hex_text, default=0):
    # The probe and the sweep store slots as the four bytes in memory order: little-endian.
    return int.from_bytes(bytes.fromhex(hex_text), 'little') if isinstance(hex_text, str) else int(default)


def native_keys(row):
    keys = []
    for case in row['cases']:
        value = case['in'][0]
        variant = case['in'][1]
        flags = 7 | (0xc0009000 if variant else 0x40000000)
        slots = case['slots']
        delta = case['delta']
        if delta == RELOAD_NATIVE:
            delta = RELOAD_PORT
        keys.append((delta, as_int(slots.get('0x18'), flags), as_int(slots.get('0x530')),
                     as_int(slots.get('0x544')), as_int(slots.get('0x548')),
                     as_int(slots.get('0x4ac'), value & 0xffffffff)))
    return tuple(keys)


def step_back_one_frame(value, bits, declared):
    if value is None or bits is None:
        return value, bits
    if not declared:
        return value, bits
    timer = (value - 1) & 0xffffffff
    return timer, bits


def port_keys(row, frame=True):
    import struct as _struct
    keys = []
    for case in row['cases']:
        if case.get('fault'):
            return None
        named = case['namedAfter']
        value, bits = named['timer'] & 0xffffffff, named['fraction'] & 0xffffffff
        if frame:
            # the port's update ends by ticking the timer; the native run stops before that tick
            total = _struct.unpack('<f', _struct.pack('<I', bits))[0] - 1.0
            bits = _struct.unpack('<I', _struct.pack('<f', total))[0]
            value = (value - 1) & 0xffffffff
        keys.append((case['delta'] & 0xffffffff, named['flags'] & 0xffffffff,
                     named['title flags'] & 0xffffffff, value, bits,
                     named['integer 0'] & 0xffffffff))
    return tuple(keys)


def main():
    native = json.load(io.open('artifacts/th16/anm-signatures.json', encoding='utf-8'))
    sweep = json.load(io.open('artifacts/th16/port-sweep/sweep.json', encoding='utf-8'))
    assert native['grid'] == GRID, (native['grid'], GRID)

    # The target vocabulary: every canonical body the interpreter can reach, by its own number.
    bodies = {}
    for title, data in sweep['titles'].items():
        for op, row in data['table'].items():
            keys = port_keys(row)
            if keys is None:
                continue
            canonical = row['canonical']
            entry = bodies.setdefault(canonical, {'reachedBy': f'th{title}+0x{int(op):x}',
                                                 'keys': keys, 'duplicates': 0})
            if entry['keys'] == keys:
                entry['duplicates'] += 1

    matched, ties, close, unmatched = [], [], [], []
    for op in sorted(int(o) for o in native['table']):
        row = native['table'][str(op)]
        if row['isDefault']:
            continue
        want = native_keys(row)
        hits = sorted(c for c, body in bodies.items() if body['keys'] == want)
        if len(hits) == 1:
            matched.append({'op': op, 'canonical': hits[0], 'handler': row['handler'], 'witness': 8,
                           'reachedBy': bodies[hits[0]]['reachedBy']})
        elif len(hits) > 1:
            ties.append({'op': op, 'handler': row['handler'], 'candidates': hits,
                        'reachedBy': [bodies[c]['reachedBy'] for c in hits]})
        else:
            best, best_n = None, -1
            for canonical, body in bodies.items():
                n = sum(1 for a, b in zip(want, body['keys']) if a == b)
                if n > best_n:
                    best, best_n = canonical, n
            (close if best_n > 0 else unmatched).append(
                {'op': op, 'handler': row['handler'], 'bestCases': best_n, 'nearestCanonical': best})
    out = {'game': 'th16', 'grid': GRID,
           'scope': 'Value matches between this title\'s measured handlers and the port\'s canonical '
                    'bodies over eight grid cases. A row needs all eight; the checker over 1280 '
                    'cases is the referee and may disagree.',
           'keyVector': ['delta', 'flags', 'title flags', 'timer', 'fraction', 'integer 0'],
           'declaredFrameTransform': 'the port update ends with timer.tick(); the native run stops at '
                                    'the dispatch boundary, so the two timer values step back one frame',
           'matched': matched, 'ties': ties, 'close': close, 'unmatched': unmatched,
           'sources': ['artifacts/th16/anm-signatures.json', 'artifacts/th16/port-sweep/sweep.json'],
           'instrument': 'tools/th16-anm-match.py'}
    io.open(ROOT + '/th16-anm-matched-rows.json', 'w', encoding='utf-8', newline='').write(
        json.dumps(out, ensure_ascii=False, indent=2).replace('\n', '\r\n'))
    print('  bodies=%d  matched=%d  ties=%d  close=%d  unmatched=%d  (real handlers=%d)'
          % (len(bodies), len(matched), len(ties), len(close), len(unmatched),
             sum(1 for r in native['table'].values() if not r['isDefault'])))
    for entry in matched[:12]:
        print('    op %-4d -> canonical %-4d witness %d  (%s)' % (entry['op'], entry['canonical'],
                                                                 entry['witness'], entry['reachedBy']))
    for entry in close[:6]:
        print('    near: op %-4d best %d/8 cases on canonical %s' % (entry['op'], entry['bestCases'],
                                                                    entry['nearestCanonical']))


if __name__ == '__main__':
    main()
