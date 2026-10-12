"""Compare each title's sample table in its own executable with its archive, and with the port.

Two instruments per title, and they must agree:
  1. tools/th-sample-table.py    reads the original's consecutive u32 pointer run out of the image
  2. tools/th-archive-names.mjs  reads the same title's archive through the port's own decoder

The criterion is the wall of section 359: a name the table carries must be a name the archive holds.
Writes docs/porting/sample-tables.json.
"""
import io
import json
import os
import re
import subprocess
import sys

NODE = r'H:\code\thp\tools\emsdk\node\24.19.0_64bit\node.exe'
GENERATION = {12: 12, 13: 13, 14: 14, 16: 14, 17: 14, 18: 14}
WEB = 'runtimes/th12/th12_web/cpp/game'


def run(cmd):
    return subprocess.run(cmd, cwd=r'H:\code\thp', capture_output=True, text=True,
                          encoding='utf-8', errors='replace')


def mine(t):
    exe = 'H:/Games/th/%d/th%d.exe' % (t, t)
    out = run(['py', '-3', 'tools/th-sample-table.py', exe]).stdout
    at = json_start(out)
    if at < 0:
        return {'error': out.strip().splitlines()[-1:]}
    table = json.loads(out[at:])
    table['arrayVa'] = table.get('arrayVa')
    return table


def json_start(out):
    """The tool prints prose first, and its own pattern contains braces."""
    for i in range(len(out) - 1, -1, -1):
        if out[i] == '{' and (i == 0 or out[i - 1] == '\n'):
            return i
    return -1


def archive_names(t):
    out = run([NODE, 'tools/th-archive-names.mjs', str(t), str(GENERATION[t]), '.wav']).stdout
    at = json_start(out)
    if at < 0:
        return {'error': out.strip().splitlines()[:3]}
    data = json.loads(out[at:])
    return {'entries': data.get('entries'), 'matched': data.get('matched'),
            'names': (data.get('names') or [])}


def port_table(t):
    """The names the tree carries for a title, read from the source it compiles."""
    inline = {12: 'th12_sound_samples', 13: 'th13_sound_samples'}
    if t in inline:
        text = io.open(os.path.join(WEB, 'SoundEffects.cpp'), encoding='utf-8').read()
        at = text.find('const char* const %s[' % inline[t])
        if at < 0:
            return []
        end = text.find('};', at)
        return re.findall(r'"(se_[a-z0-9_]+\.wav)"', text[at:end])
    path = os.path.join(WEB, 'Th%dAudioTables.inc' % t)
    if not os.path.exists(path):
        return []
    return re.findall(r'"(se_[a-z0-9_]+\.wav)"',
                      io.open(path, encoding='utf-8').read())


rows = {}
mine_section = {}
for t in (12, 13, 14, 16, 17, 18):
    exe = mine(t)
    mine_section[t] = exe.get('section')
    arch = archive_names(t)
    names = exe.get('names') or []
    archive = arch.get('names') or []
    aset = set(archive)
    missing = [n for n in names if n not in aset]
    tree = port_table(t)
    rows['th%d' % t] = {
        'executable': 'H:/Games/th/%d/th%d.exe' % (t, t),
        'section': mine_section.get(t),
        'treeEntries': exe.get('entries'),
        'distinct': exe.get('distinct'), 'archiveEntries': arch.get('entries'),
        'namesNotInArchive': missing,
        'archiveOrderEqualsTable': names == archive,
        'treeTable': tree,
        'treeMatchesExecutable': tree == names,
        'arrayVa': exe.get('arrayVa'),
        'table': names,
        'archive': archive,
        'error': exe.get('error') or arch.get('error'),
    }

json.dump({'generation': GENERATION,
           'method': 'tools/th-sample-table.py (the image\'s pointer run) against '
                     'tools/th-archive-names.mjs (the archive through the port\'s decoder)',
           'titles': rows},
          io.open('docs/porting/sample-tables.json', 'w', encoding='utf-8', newline=''),
          ensure_ascii=False, indent=2)

for t in ('th12', 'th13', 'th14', 'th16', 'th17', 'th18'):
    r = rows[t]
    print('  %-5s va %-11s tree %-4s archive %-4s order==%s  notInArchive=%s' % (
        t, r['arrayVa'], r['treeEntries'], r['archiveEntries'],
        r['archiveOrderEqualsTable'], r['namesNotInArchive']))
