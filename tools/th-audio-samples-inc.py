#!/usr/bin/env python3
"""Write a title's sample-name array into an .inc the engine can include.

The table is not guessed: docs/porting/sample-tables.json is the pointer run read out of that
title's own executable (tools/th-sample-table.py) and checked, name by name and in order, against
the archive read through the port's own decoder (tools/th-archive-names.mjs). The .inc carries the
provenance in its header so a later reader can re-derive rather than trust it.

  py -3 tools/th-audio-samples-inc.py            writes the titles that have a mined table
  py -3 tools/th-audio-samples-inc.py --check    compares the files on disk with what it would write
"""
import io
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TABLE = os.path.join(ROOT, 'docs', 'porting', 'sample-tables.json')
OUT = os.path.join(ROOT, 'runtimes', 'th12', 'th12_web', 'cpp', 'game')
# 12, 13 and 14 carry tables the tree already had; the ones mined here are the titles that did not.
TITLES = (16, 17, 18)


def wrapper(names, width=5):
    rows = []
    for i in range(0, len(names), width):
        rows.append('\t' + ','.join('"%s"' % n for n in names[i:i + width]))
    return ',\n'.join(rows)


def render(title, row):
    lines = []
    lines.append('// Generated from TH%d %s by tools/th-audio-samples-inc.py: the pointer run at' % (
        title, row.get('version', '')))
    lines.append('// %s %s read out of that title\'s own executable, in its archive\'s order,' % (
        row.get('section'), row.get('arrayVa')))
    lines.append('// and checked name by name against the archive (docs/porting/sample-tables.json).')
    lines.append('namespace {')
    lines.append('const char* const th%d_sound_samples[%d]={' % (title, len(row['table'])))
    lines.append(wrapper(row['table']))
    lines.append('};')
    lines.append('}')
    return '\n'.join(lines) + '\n'


def main():
    data = json.load(io.open(TABLE, encoding='utf-8'))
    check = '--check' in sys.argv
    bad = 0
    for title in TITLES:
        key = 'th%d' % title
        row = dict(data['titles'][key])
        if not row['table']:
            print('  %s has no mined table' % key)
            bad = 1
            continue
        target = os.path.join(ROOT, 'runtimes', 'th%d' % title, 'target.json')
        row['version'] = json.load(io.open(target, encoding='utf-8')).get('version', '')
        text = render(title, row)
        path = os.path.join(OUT, 'Th%dAudioTables.inc' % title)
        if check:
            current = io.open(path, encoding='utf-8', newline='').read() if os.path.exists(path) else ''
            same = current.replace('\r\n', '\n') == text
            print('  %-38s %s' % (os.path.relpath(path, ROOT),
                                  'matches' if same else 'DIFFERS (%d vs %d bytes)' % (
                                      len(current), len(text))))
            bad |= 0 if same else 1
        else:
            io.open(path, 'w', encoding='utf-8', newline='\n').write(text)
            print('  %-38s %3d entries  %s %s' % (
                os.path.relpath(path, ROOT), len(row['table']), row.get('section'),
                row.get('arrayVa')))
    return bad


if __name__ == '__main__':
    sys.exit(main())
