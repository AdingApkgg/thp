#!/usr/bin/env python3
"""The per-character portrait script index each title's message interpreter reads.

The port's MSG opcode 1 (`Dialogue.cpp`) read the table from TH12's image (`mov eax,[char]` at
0x0042013f, `mov ecx,[eax*4+0x4b2f84]` at 0x00420144) and from TH13's (0x00429298 /
`[edx*4+0x4c0aa0]`). The generation has a table of its own: with TH12's numbers, title 16 asks
its 27-slot player file for script 31.

The read is a scan of the image for the same two instructions - a load of the character global into
eax, followed by a scaled index into a table - and then a *control on the answer*: the entries have
to be the last script index of that title's own player files, which the exported set carries. TH12's
and TH13's known tables are the control for the scanner, and the ANM slot count comes from the
promoted reader (th-anm-script-slots.py), so the two sides are independent.

Usage: th-portrait-table.py [title...]
"""
import importlib
import importlib.util
import json
import os
import re
import struct
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'tools'))
Image = importlib.import_module('th12-pe').Image  # the shipped PE reader

# The two selection globals of each title, from ShotFiles.hpp's measured shot-array sites. The
# portrait reads the character of the pair; the scan tries both because the pair's order is a
# property of the site, not of the globals.
GLOBALS = {12: (0x4b0c90, 0x4b0c94), 13: (0x4be7b8, 0x4be7bc), 14: (0x4f5828, 0x4f582c),
           16: (0x4a57a8, 0x4a57a4), 17: (0x4b59f4, 0x4b59f8), 18: (0x4cccf8, 0x4cccf4)}
# The known answers the scanner has to reproduce (Dialogue.cpp's comment), and the table the port
# needs for each generation title.
KNOWN = {12: (0x4b2f84, [31, 30, 28]), 13: (0x4c0aa0, [29, 34, 30, 28])}
PLAYER_FILES = {12: ['pl00.anm', 'pl01.anm', 'pl02.anm'],
                13: ['pl00.anm', 'pl01.anm', 'pl02.anm', 'pl03.anm'],
                14: ['pl00.anm', 'pl01.anm', 'pl02.anm'],
                16: ['pl00.anm', 'pl02.anm', 'pl03.anm', 'pl01.anm'],
                17: ['pl00.anm', 'pl01.anm', 'pl02.anm'],
                18: ['pl00.anm', 'pl01.anm', 'pl02.anm', 'pl03.anm']}
DATA_DIRS = {12: 'runtimes/th12/th12_web/artifacts/cpp/th12-data',
            13: 'runtimes/th13/th13_web/artifacts/cpp/th13-data',
            14: 'runtimes/th14/th14_web/artifacts/cpp/th14-data',
            16: 'tools/tmp/anm16', 17: 'tools/tmp/anm17', 18: 'tools/tmp/anm18'}


def slot_reader():
    path = os.path.join(ROOT, 'tools', 'th-anm-script-slots.py')
    spec = importlib.util.spec_from_file_location('anm_slots', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def player_slot_counts(title, slots):
    """The exported player files' script counts, in the order the table indexes them."""
    directory = os.path.join(ROOT, DATA_DIRS[title].replace('/', os.sep))
    counts = []
    for name in PLAYER_FILES[title]:
        path = os.path.join(directory, name)
        if not os.path.exists(path):
            return None
        data = open(path, 'rb').read()
        counts.append(sum(1 for _, chunk in slots.chunks(data) for _ in slots.scripts(chunk)))
    return counts


def exe_of(title):
    folder = os.path.join(ROOT, 'runtimes', 'th%d' % title)
    target = os.path.join(folder, 'th12_web' if title == 12 else '', 'target.json')
    config = json.load(open(target, encoding='utf-8'))
    return os.path.join(os.path.dirname(target), config['executable'])


def scan(title):
    """Every `table[register*4]` read whose register was just loaded from a selection global."""
    img = Image(exe_of(title))
    data = img.data
    hits = []
    # `mov r32, [disp32]` for the registers a site can hold the selection in.
    loads = ((0, b'\xa1'), (0, b'\x8b\x05'), (1, b'\x8b\x0d'), (2, b'\x8b\x15'),
             (3, b'\x8b\x1d'), (6, b'\x8b\x35'), (7, b'\x8b\x3d'))
    index_read = re.compile(rb'\x8b[\x04\x0c\x14\x1c\x24\x2c\x34\x3c][\x85\x8d\x95\x9d\xa5\xad\xb5\xbd]')
    for global_va in GLOBALS[title]:
        for register, head in loads:
            load = head + struct.pack('<I', global_va)
            start = 0
            while True:
                at = data.find(load, start)
                if at < 0:
                    break
                start = at + 1
                for match in index_read.finditer(data, at + len(load), at + len(load) + 40):
                    if (match.group(0)[2] >> 3) & 7 != register:
                        continue
                    table = struct.unpack_from('<I', data, match.start() + 3)[0]
                    width = len(PLAYER_FILES[title])
                    entries = [img.u32(table + 4 * i) for i in range(width + 4)]
                    if any(v > 96 for v in entries[:width]):
                        continue
                    hits.append((global_va, img.va_of(at), table, entries))
    return hits


def entry_hits(title, hits):
    slots = slot_reader()
    counts = player_slot_counts(title, slots)
    wanted = [c - 1 for c in counts] if counts else None
    print('  th%d: player slots %s -> last index %s' % (title, counts, wanted))
    for global_va, va, table, entries in hits:
        verdict = 'candidate'
        if wanted and entries[:len(wanted)] == wanted:
            verdict = 'MATCH'
        if title in KNOWN and table == KNOWN[title][0]:
            verdict = 'MATCH (known %s)' % KNOWN[title][1]
            assert entries[:len(KNOWN[title][1])] == KNOWN[title][1], (table, entries)
        if verdict.startswith('MATCH') or entries[0] != 0:
            print('    from [0x%x] at 0x%x: table 0x%x %s  %s' %
                  (global_va, va, table, entries, verdict))
    if title in KNOWN:
        assert any(table == KNOWN[title][0] for _, _, table, _ in hits), 'the control table was not found'


for title in ([int(a) for a in sys.argv[1:]] or sorted(GLOBALS)):
    found = scan(title)
    print('  th%d: %d candidate sites' % (title, len(found)))
    entry_hits(title, found)
