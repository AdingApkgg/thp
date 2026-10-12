#!/usr/bin/env python3
"""The payload every MSG command carries in each title's own messages.

The port's command rows are per title, and the titles differ in which numbers they use: TH12's
messages contain no 28 and no 29 at all, TH13's do (823 and 185 of them), and from 13 on the
sizes are the same everywhere while the numbers a command writes are what decides how to read it.
This prints, per title, every opcode's payload sizes and - for the two commands the port reads as a
pair of floats and as a style - the number of payloads and the shape of their values, so the
reading can be checked instead of assumed.

Usage: th-msg-payloads.py [title...]
"""
import collections
import glob
import math
import os
import struct
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIRS = {title: [os.path.join(ROOT, 'runtimes', 'th%d' % title, 'th%d_web' % title, 'artifacts',
                              'cpp', 'th%d-data' % title),
                os.path.join(ROOT, 'tools', 'tmp', 'msg%d' % title)]
        for title in (12, 13, 14, 16, 17, 18)}


def commands(path):
    data = open(path, 'rb').read()
    if len(data) < 4:
        return
    count = struct.unpack_from('<I', data, 0)[0]
    if count > 0x1000:
        return
    offsets = [struct.unpack_from('<I', data, 4 + 8 * i)[0] for i in range(count)]
    for index, offset in enumerate(offsets):
        stop = offsets[index + 1] if index + 1 < len(offsets) else len(data)
        at = offset
        while at + 4 <= min(stop, len(data)):
            length = data[at + 3]
            if at + 4 + length > len(data):
                break
            yield data[at + 2], data[at + 4:at + 4 + length]
            at += 4 + length


def measure(title):
    files = []
    for directory in DIRS[title]:
        files += sorted(glob.glob(os.path.join(directory, '*.msg')))
    sizes = collections.defaultdict(collections.Counter)
    payloads = collections.defaultdict(list)
    for path in files:
        for opcode, payload in commands(path):
            sizes[opcode][len(payload)] += 1
            payloads[opcode].append(payload)
    return files, sizes, payloads


for title in ([int(a) for a in sys.argv[1:]] or sorted(DIRS)):
    files, sizes, payloads = measure(title)
    print('  th%-2d %3d file(s), %3d command(s)' %
          (title, len(files), sum(sum(counter.values()) for counter in sizes.values())))
    if not files:
        print('        (messages not exported here; dump them with tools/th-archive-dump.mjs)')
        continue
    pairs = [struct.unpack('<ff', payload) for payload in payloads[28] if len(payload) == 8]
    finite = [pair for pair in pairs if all(math.isfinite(value) and abs(value) <= 4096 for value in pair)]
    styles = [struct.unpack('<I', payload)[0] for payload in payloads[29] if len(payload) == 4]
    print('        28: %d payload(s), sizes %s | decoded as two floats, %d of %d within +-4096'
          % (len(payloads[28]), dict(sizes[28]), len(finite), len(pairs)))
    if pairs:
        print('            first three %s' % ' '.join('(%.3g,%.3g)' % pair for pair in pairs[:3]))
    print('        29: %d payload(s), sizes %s | values %s, distinct low four bits %d'
          % (len(payloads[29]), dict(sizes[29]),
             (min(styles), max(styles)) if styles else '-', len({value & 0xf for value in styles})))
