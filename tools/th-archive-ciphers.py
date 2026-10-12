"""Emit reference/archive-ciphers.json from the single table the Runtime carries.

The archive suite needs TH11's eight cipher rows to drive the ORIGINAL cipher routine and compare its
output with the Runtime's. Two facts decide where the rows come from:

  * searching the whole th11.exe - the packed row layout, the eight key bytes, and both generations -
    finds nothing, so the executable does not carry the table as constants; the keys are derived at
    run time there, and a search that found nothing is the evidence for saying so;
  * the Runtime already carries the rows, crediting thtk's `thdat95.c` (the community's extraction),
    and resolves version 11 to the TH95 set.

So the JSON is not a new transcription: it is an EXPORT of the table the Runtime uses, parsed out of
ResourceCrypt.cpp rather than copied, so the constants live in exactly one place. What the suite then
measures is whether that table, fed to the original's own routine, reproduces the Runtime's unpacking.
"""
import io
import json
import re

SOURCE = 'runtimes/th12/th12_web/cpp/game/ResourceCrypt.cpp'
OUT = 'runtimes/th12/th12_web/reference/archive-ciphers.json'


def main():
    text = io.open(SOURCE, encoding='utf-8').read()
    rows = {}
    for name, body in re.findall(r'const CryptParams (archive_crypt_\w+)\[8\]=\{(.*?)\};',
                                 text, re.S):
        parsed = []
        for match in re.finditer(r'\{([^}]*)\}', body):
            values = [int(value, 0) for value in match.group(1).split(',')]
            parsed.append({'key': values[0], 'step': values[1], 'block': values[2],
                           'limit': values[3]})
        rows[name] = parsed
    print('  tables parsed: %s' % {name: len(value) for name, value in rows.items()})

    mapping = {}
    for case in re.finditer(r'case ([\d:case ]+): return (archive_crypt_\w+);', text):
        table = case.group(2)
        for version in re.findall(r'\d+', case.group(1)):
            mapping[int(version)] = table
    print('  version map: %s' % mapping)

    table = mapping.get(11)
    entries = rows[table]
    document = {
        'instrument': 'tools/th-archive-ciphers.py',
        'method': ('the eight cipher rows of the TH95/TH11 generation, exported from the table the '
                   'Runtime uses (cpp/game/ResourceCrypt.cpp) instead of being copied, so the '
                   'constants exist in one place; the runtime resolves archive version 11 to this set '
                   'and the suite drives the ORIGINAL cipher routine at th11 0x4581c0 with these keys '
                   'and compares the result with the Runtime unpacking the same archive'),
        'provenance': {
            'runtimeTable': table,
            'runtimeSource': SOURCE,
            'upstream': "thtk's thdat95.c carries the same eight rows per generation (quoted in the "
                        "source comment)",
            'executableSearch': ('the whole th11.exe was searched for the rows packed as four dwords, '
                                 'for the eight key bytes, and for both the th95 and th12 variants: '
                                 'found none, so the executable does not hold the table as constants '
                                 'and the keys are derived at run time there'),
        },
        'entries': entries,
    }
    io.open(OUT, 'w', encoding='utf-8', newline='').write(
        json.dumps(document, ensure_ascii=False, indent=2).replace('\n', '\r\n'))
    keys = [row['key'] for row in entries]
    print('  wrote %s with %d rows; keys %s' % (OUT, len(entries), [hex(k) for k in keys]))


main()
