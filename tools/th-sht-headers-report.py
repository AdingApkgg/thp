"""The measured sheet headers, from each title's own archive.

tools/th-archive-dump.mjs writes entries out through the port's own decoder, so the bytes here are
the original's, not a guess at a layout. The first u16 of a .sht is the version the parser
compares, and the second is the group count.

  py -3 tools/th-sht-headers-report.py <dump-root> <out.json>
"""
import glob
import hashlib
import io
import json
import os
import struct
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
dump_root = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, 'artifacts', 'th12', 'sht-dump')
out_path = sys.argv[2] if len(sys.argv) > 2 else os.path.join(ROOT, 'docs', 'porting',
                                                             'sht-headers.json')

rows = {}
for t in (12, 13, 14, 16, 17, 18):
    files = sorted(glob.glob(os.path.join(dump_root, 'th%d' % t, '*.sht')))
    if not files:
        rows['th%d' % t] = {'dumped': 0}
        continue
    sample = []
    for path in files:
        blob = open(path, 'rb').read()
        sample.append({'file': os.path.basename(path), 'bytes': len(blob),
                      'version': struct.unpack_from('<H', blob, 0)[0],
                      'groups': struct.unpack_from('<H', blob, 2)[0],
                      'head': blob[:24].hex(' '),
                      'sha256_16': hashlib.sha256(blob).hexdigest()[:16]})
    versions = sorted(set(s['version'] for s in sample))
    rows['th%d' % t] = {'dumped': len(files), 'versions': versions, 'sheets': sample}

json.dump({'method': 'tools/th-archive-dump.mjs (the archive through the port\'s decoder), first '
                     'u16 of each .sht',
           'reading': 'the version the parser compares is per title, and is not 3 outside 12 and 13',
           'titles': rows},
          io.open(out_path, 'w', encoding='utf-8', newline=''), ensure_ascii=False, indent=2)
for t in (12, 13, 14, 16, 17, 18):
    r = rows['th%d' % t]
    if not r['dumped']:
        print('  th%-3d no sheets dumped' % t)
        continue
    s = r['sheets'][0]
    print('  th%-3d %2d sheets, versions %s, first %-14s %5d bytes  head %s' % (
        t, r['dumped'], r['versions'], s['file'], s['bytes'], s['head'][:32]))
