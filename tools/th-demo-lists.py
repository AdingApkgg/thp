"""Each title's own attract-demo playlist, read out of its own executable and its own demo files.

An attract demo is chosen, not formatted: the title screen's code indexes a list of replay names that
lives in the executable (a run of consecutive pointers into the string pool, in .data for th12/13/14
and .rdata for th16/17/18), copies that name into a buffer, and loads it. So the playlist of a
title is data the title ships, and this prints it next to the demos the title ships on disk, with the
stage each of those demos records.

    py -3 tools/th-demo-lists.py [title...]      default: 12 13 14 16 17 18

The demo files are the title's own `demo*.rpy`, decoded by tools/th-replay-parse.py (the port's
Replay.hpp rows plus tools/th-replay-container.py's per-title parameters), and the names come from the
title's executable through a PE walk with no disassembler: the pool, then the pointer run.
"""
import re
import struct
import subprocess
import sys

ROOT = 'H:/Games/th'


def sections(image):
    pe = struct.unpack_from('<I', image, 0x3C)[0]
    count = struct.unpack_from('<H', image, pe + 6)[0]
    option = struct.unpack_from('<H', image, pe + 20)[0]
    base = struct.unpack_from('<I', image, pe + 24 + 28)[0]
    out = []
    for index in range(count):
        at = pe + 24 + option + index * 40
        name = image[at:at + 8].split(b'\x00')[0].decode('ascii', 'replace')
        vsize, rva, rawsize, raw = struct.unpack_from('<IIII', image, at + 8)
        out.append((name, base + rva, raw, max(vsize, rawsize)))
    return out


def shipped_stages(title):
    """The demos on disk and the stage each one records, from the parse that mirrors the port."""
    try:
        text = subprocess.check_output([sys.executable, 'tools/th-replay-parse.py', str(title)],
                                     text=True, stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as error:
        return {}, error.output
    stages = {}
    for line in text.splitlines():
        match = re.match(r'\s*(\S+\.rpy)\s+count=\d+ .*?(\d+):[0-9.]+k/\d+', line)
        if match:
            stages[match.group(1)] = int(match.group(2))
    return stages, text


def executable_playlist(title):
    """The title's own list of demo names, in the order its image stores them."""
    profile, status = shipped_stages(title)
    image = open('%s/%d/th%d.exe' % (ROOT, title, title), 'rb').read()
    table = sections(image)
    pool = []
    for match in re.finditer(rb'demo/demo\d\.rpy', image):
        for name, va, raw, size in table:
            if raw <= match.start() < raw + size:
                pool.append((match.group().decode(), va + (match.start() - raw)))
    # the list: dwords that point into the pool, consecutive in the image and sorted by address
    playlist = []
    for label, va in pool:
        needle = struct.pack('<I', va)
        at = image.find(needle)
        while at >= 0:
            for name, section_va, raw, size in table:
                if raw <= at < raw + size:
                    playlist.append((section_va + (at - raw), label))
                    break
            at = image.find(needle, at + 1)
    playlist.sort()
    return profile, status, pool, playlist


TITLES = [int(a) for a in sys.argv[1:]] or [12, 13, 14, 16, 17, 18]
for title in TITLES:
    profile, status, pool, playlist = executable_playlist(title)
    print('  th%d' % title)
    print('    ships: %s' % (' '.join('%s=%s' % (name, profile.get(name, '?'))
                                      for name in sorted(profile))
                             or '(none parsed: %s)' % status.strip().splitlines()[-1][:90]))
    print('    image names: %s' % ' '.join('%s@0x%x' % (label, va) for label, va in pool))
    print('    image list (in address order): %s'
          % ' '.join('%s@0x%x' % (label, addr) for addr, label in playlist))
    if not profile:
        print('    (parse: %s)' % status.strip().splitlines()[-1][:100])
