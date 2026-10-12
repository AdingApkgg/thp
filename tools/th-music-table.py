#!/usr/bin/env python3
"""Emit a title's music cue table from the files the title ships.

`thbgm.fmt` is a run of 52-byte records whose first 16 bytes are the file name; `musiccmt.txt` is
the music room's comment file, whose `@bgm/*.wav` lines name the tracks the room shows, in order.
For TH12 the two agree record for record (17 comments, 18 records - the last is a leftover), which
is how the runtime's cue table is derived. This prints the same rows for the title asked for, so
the table stays a reading of the title's own files.

Usage: th-music-table.py <data-dir> [--cpp]
"""
import glob
import os
import re
import sys


def main(directory, emit_cpp):
    layouts = glob.glob(os.path.join(directory, 'thbgm.fmt'))
    if not layouts:
        print('  no thbgm.fmt in %s' % directory)
        return
    data = open(layouts[0], 'rb').read()
    records = [data[n:n + 16].split(b'\0')[0].decode('ascii', 'replace')
               for n in range(0, len(data) - 51, 52)]
    comments = []
    for path in glob.glob(os.path.join(directory, 'musiccmt.txt')):
        raw = open(path, 'rb').read()
        # TH12 writes `@bgm/th12_01.wav`; TH13 writes `@bgm/th13_00`, no extension. Both name the
        # record the room plays for that entry, so the marker is the whole name and the suffix
        # is optional - reading only the suffixed form made TH13 look like it had no comments.
        comments = re.findall(rb'@bgm/([A-Za-z0-9_]+)', raw)
        comments = [(c.decode() if c.endswith(b'.wav') else c.decode() + '.wav') for c in comments]
    print('  %s: %d layout records of 52 bytes, %d bgm comments' %
          (os.path.basename(os.path.dirname(directory)), len(records), len(comments)))
    print('    layout:   %s' % ' '.join(records))
    if comments:
        print('    comments: %s' % ' '.join(comments))
        agrees = [n for n, r in enumerate(records) if n < len(comments) and comments[n] == r]
        first = next((n for n, r in enumerate(records)
                      if n < len(comments) and comments[n] != r), None)
        print('    comment n names record n: %d of %d%s' %
              (len(agrees), len(comments), '' if first is None else ', first differs at n=%d' % first))
        print('    the room order, which is the cue table the runtime needs:')
        stems = [c[:-4] for c in comments]
        for n, stem in enumerate(stems):
            print('      {%d,"%s"}%s' % (n, stem, ',' if n + 1 < len(stems) else ''))
    if emit_cpp:
        stems = [r[:-4] if r.endswith('.wav') else r for r in records]
        for n, stem in enumerate(stems):
            end = ',\n' if (n + 1) % 5 == 0 else ','
            print(' {%d,"%s"}%s' % (n, stem, end if n + 1 < len(stems) else ''))


if __name__ == '__main__':
    main(sys.argv[1], '--cpp' in sys.argv)
