"""What one title's own archive says a stage file set is.

The port needs one row per title (`StageFiles.hpp`), and this is the measurement those rows must
come from, not TH12's names:

  * the `.std` set, and the message set per stage - the letters and the count;
  * which ANM a stage's own scene script names (that is the background), from the dumped `st01.std`;
  * which ANM a stage's own ECL names (that is the enemy set), from the dumped `st01.ecl`;
  * the logo and the .ecl trio the archive itself lists.

The counts are then checkable against the same title's shot table: a title's message set is one
file per index, and the index runs over characters x loadouts.

  py -3 tools/th-stage-rows.py 16 14
  py -3 tools/th-stage-rows.py 16 14 --dump     (dumps st01.std and st01.ecl first)
"""
import argparse
import glob
import io
import os
import re
import subprocess

NODE = os.environ.get('THP_NODE', r'H:\code\thp\tools\emsdk\node\24.19.0_64bit\node.exe')
REPO = os.path.dirname(os.path.abspath(__file__))


def archive_names(title, version):
    result = subprocess.run([NODE, os.path.join(REPO, 'th-archive-names.mjs'), str(title), str(version)],
                           capture_output=True, text=True, cwd=REPO, encoding='utf-8', errors='replace')
    names = []
    for line in (result.stdout or '').splitlines():
        match = re.search(r"""["']([^"']+)["']""", line)
        if match:
            names.append(match.group(1))
    return names


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('title', type=int)
    parser.add_argument('version', type=int)
    parser.add_argument('--dump', action='store_true')
    args = parser.parse_args()

    names = archive_names(args.title, args.version)
    if not names:
        raise SystemExit('  no names came back; is the archive readable?')
    stages = sorted({m.group(1) for n in names if (m := re.match(r'st(\d+)\.std$', n))})
    print('  th%d over %d archive entries' % (args.title, len(names)))
    print('      .std stages: %s' % ' '.join(stages))

    messages = [n for n in names if re.match(r'st\d+[a-z]\.msg$', n)]
    per_stage = {}
    for name in messages:
        match = re.match(r'st(\d+)([a-z])\.msg$', name)
        per_stage.setdefault(match.group(1), []).append(match.group(2))
    for stage in sorted(per_stage):
        letters = ''.join(sorted(per_stage[stage]))
        print('      stage %-3s messages %-12s count %d' % (stage, letters, len(letters)))

    for role, pattern in (('logo', r'st\d+logo\.anm$'), ('wall', r'st\d+(wl|bg)\.anm$'),
                          ('enemy', r'st\d+enm\.anm$'), ('timeline', r'st\d+\.ecl$'),
                          ('boss', r'st\d+bs\.ecl$'), ('midboss', r'st\d+mbs\.ecl$')):
        hits = sorted(n for n in names if re.match(pattern, n))
        print('      %-8s %2d  %s' % (role, len(hits), ' '.join(hits[:3])))

    dump = os.path.join(REPO, 'artifacts', 'th12', 'stage-dump', 'th%d' % args.title)
    if args.dump:
        for suffix in ('.std', '.ecl'):
            subprocess.run([NODE, os.path.join(REPO, 'th-archive-dump.mjs'), str(args.title),
                            str(args.version), suffix, dump], capture_output=True, text=True, cwd=REPO)
    for entry in sorted(glob.glob(dump + '/st01.std')) + sorted(glob.glob(dump + '/st01.ecl')):
        text = io.open(entry, 'rb').read().decode('latin-1')
        refs = sorted(set(re.findall(r'[A-Za-z0-9_]{3,18}\.(?:anm|ecl|msg)', text)))
        print('      %-10s names: %s' % (os.path.basename(entry), ' '.join(refs[:6]) or '(no dump; use --dump)'))


if __name__ == '__main__':
    main()
