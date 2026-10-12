"""Read each title's shot-file and player-file tables out of its own executable.

The same instrument as section 360, with the pattern the file's own comment names:
tools/th-sample-table.py --pattern. Two arrays per title: the .sht table (which shot file a
character/subtype pair loads) and the .anm table (which player file carries it).

  py -3 tools/th-shot-files-report.py           writes docs/porting/shot-files.json
"""
import io
import json
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TITLES = (12, 13, 14, 16, 17, 18)
PATTERNS = {'shot': r'pl[0-9]{2}[a-z]?\.sht', 'player': r'pl[0-9]{2}\.anm'}


def mine(exe, pattern, minimum):
    out = subprocess.run(['py', '-3', os.path.join(ROOT, 'tools', 'th-sample-table.py'), exe,
                         '--pattern', pattern, '--min', str(minimum)],
                        cwd=ROOT, capture_output=True, text=True, encoding='utf-8',
                        errors='replace').stdout
    for i in range(len(out) - 1, -1, -1):
        if out[i] == '{' and out[i - 1] == '\n':
            return json.loads(out[i:])
    return {}


rows = {}
for t in TITLES:
    exe = 'H:/Games/th/%d/th%d.exe' % (t, t)
    row = {}
    for kind, pattern in PATTERNS.items():
        # a title may carry one pointer per file, so the run can be as short as its table
        data = mine(exe, pattern, 3)
        row[kind] = {'section': data.get('section'), 'arrayVa': data.get('arrayVa'),
                     'entries': data.get('entries'), 'names': data.get('names') or [],
                     'distinct': data.get('distinct')}
    rows['th%d' % t] = row
    print('  th%-3d shot  %-7s %-11s %s' % (t, row['shot']['section'], row['shot']['arrayVa'],
                                           row['shot']['names']))
    print('        player %-7s %-11s %s' % (row['player']['section'], row['player']['arrayVa'],
                                            row['player']['names']))

json.dump({'method': "tools/th-sample-table.py --pattern, the same reader as docs/porting/"
                     'sample-tables.json',
           'patterns': PATTERNS, 'titles': rows},
          io.open(os.path.join(ROOT, 'docs', 'porting', 'shot-files.json'), 'w',
                  encoding='utf-8', newline=''), ensure_ascii=False, indent=2)
