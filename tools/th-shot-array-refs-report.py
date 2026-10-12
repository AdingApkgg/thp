"""Every title's shot-array indexing site, in one file, for the record.

The formula and the two globals are read out of .text (tools/th-array-refs.py), and the array
addresses come from docs/porting/shot-files.json, so a table is a row only when the original's
own expression has been read.
"""
import io
import json
import os
import re
import subprocess

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TABLES = json.load(io.open(os.path.join(ROOT, 'docs', 'porting', 'shot-files.json'),
                           encoding='utf-8'))

OUT = os.path.join(ROOT, 'docs', 'porting', 'shot-array-refs.txt')
lines = []
summary = {}
for t in (12, 13, 14, 16, 17, 18):
    row = TABLES['titles']['th%d' % t]
    va = (row.get('shot') or {}).get('arrayVa')
    lines.append('=== th%d  shot array %s  %s' % (t, va or 'none', (row.get('shot') or {}).get('names')))
    if not va:
        continue
    out = subprocess.run(['py', '-3', os.path.join(ROOT, 'tools', 'th-array-refs.py'),
                         'H:/Games/th/%d/th%d.exe' % (t, t), va, '--window', '40'],
                        cwd=ROOT, capture_output=True, text=True, encoding='utf-8',
                        errors='replace').stdout
    keep = [ln for ln in out.splitlines()
            if re.search(r'mov|add|lea|shl|imul|push|\*4 \+|references:', ln)]
    lines.extend('  ' + ln.strip() for ln in keep[:14])
    globals_ = sorted(set(re.findall(r'0x4[a-f0-9]{5}', out)))
    indexed = [ln for ln in keep if '*4 +' in ln or (ln.strip().startswith('0x') and 'add' in ln)
               or 'imul' in ln or 'shl' in ln]
    summary['th%d' % t] = {'va': va, 'globals': globals_, 'expression': indexed[-3:]}
    lines.append('')

io.open(OUT, 'w', encoding='utf-8', newline='').write('\n'.join(lines) + '\n')
json.dump(summary, io.open(os.path.join(ROOT, 'docs', 'porting', 'shot-array-refs.json'), 'w',
                           encoding='utf-8', newline=''), ensure_ascii=False, indent=2)
for t in sorted(summary, key=lambda k: int(k[2:])):
    print('  %-5s globals=%s' % (t, ','.join(summary[t]['globals'][:6])))
    for ln in summary[t]['expression']:
        print('        ' + ln.strip()[:100])
