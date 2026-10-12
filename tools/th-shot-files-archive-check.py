"""The membership check, done on the full entry list instead of on a suffix filter."""
import json
import os
import re
import subprocess

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NODE = r'H:\code\thp\tools\emsdk\node\24.19.0_64bit\node.exe'
GEN = {12: 12, 13: 13, 14: 14, 16: 14, 17: 14, 18: 14}
T = json.load(open(os.path.join(ROOT, 'docs', 'porting', 'shot-files.json'), encoding='utf-8'))
rows = {}
for t in (12, 13, 14, 16, 17, 18):
    out = subprocess.run([NODE, 'tools/th-archive-names.mjs', str(t), str(GEN[t])], cwd=ROOT,
                         capture_output=True, text=True, encoding='utf-8', errors='replace').stdout
    # with no flags the tool prints the JSON alone; with prose it starts on its own line.
    at = out.find('\n{')
    data = json.loads(out[at if at >= 0 else out.find('{'):])
    names = set(data['names'])
    row = T['titles']['th%d' % t]
    shot = row['shot']['names'] or []
    player = row['player']['names'] or []
    raw = open('H:/Games/th/%d/th%d.exe' % (t, t), 'rb').read()
    strings = sorted(set(m.decode() for m in re.findall(rb'pl[0-9]{2}[a-z]?\.(?:sht|anm)', raw)))
    rows['th%d' % t] = {'entries': data['entries'],
                        'shotNotInArchive': [n for n in shot if n not in names],
                        'playerNotInArchive': [n for n in player if n not in names],
                        'exePlStrings': strings}
    print('  th%-3d archive %-4d  shot %-2d/%-2d in archive  player %-2d/%-2d in archive' % (
        t, data['entries'], len(shot) - len(rows['th%d' % t]['shotNotInArchive']), len(shot),
        len(player) - len(rows['th%d' % t]['playerNotInArchive']), len(player)))
    print('        pl*.sht/anm strings in the exe: %d %s' % (len(strings), strings[:6]))

json.dump(rows, open(os.path.join(ROOT, 'docs', 'porting', 'shot-files-archive.json'), 'w',
                    encoding='utf-8'), ensure_ascii=False, indent=2)
