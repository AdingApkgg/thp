"""Find where a title's decoded replay keeps the four selection words the port reads (stages,
character, shot type, difficulty). The control is TH12 and TH13, whose +0x58 is known: the
search must report it. Candidates are the offsets whose four words are in range on every demo the
title ships, ranked by whether the character actually varies between demos.

  py -3 tools/tmp/replay-selection-search.py [title...]
"""
import struct
import sys
from pathlib import Path

module = {}
src = Path('tools/th-replay-container.py').read_text(encoding='utf-8').partition('if __name__')[0]
exec(compile(src, 'th-replay-container', 'exec'), module)
fields, decode_with, demo_files = module['fields'], module['decode_with'], module['demo_files']
TH12 = ((0x5e, 0xe1, 0x800), (0x7d, 0x3a, 0x40))
GENERATION = ((0x5c, 0xe1, 0x400), (0x7d, 0x3a, 0x100))
RECORD_START = {12: 0x70, 13: 0x74, 14: 0x94, 16: 0xA0, 17: 0xA0, 18: 0xC8}


def candidates(title):
    pair = TH12 if title == 12 else GENERATION
    decoded = []
    for path in demo_files(title):
        data, packed, unpacked = fields(path)
        decoded.append(decode_with(data, packed, unpacked, pair))
    found = []
    for start in range(0x30, RECORD_START.get(title, 0xC8) - 0x0C, 4):
        words = [[struct.unpack_from('<I', d, start + 4 * i)[0] for i in range(4)] for d in decoded]
        counts = {w[0] for w in words}
        if len(counts) != 1 or not 1 <= words[0][0] <= 7:
            continue
        if max(w[1] for w in words) > 15 or max(w[2] for w in words) > 2 or max(w[3] for w in words) > 4:
            continue
        varied = len({w[1] for w in words}) > 1
        doubling = len(set(tuple(w) for w in words))
        found.append((start, doubling, varied, words))
    # the port's offset is the one where the tuple differs per demo; a constant tuple is noise
    found.sort(key=lambda item: (not item[2], item[1]))
    return decoded, found


for title in [int(a) for a in sys.argv[1:]] or [12, 13, 14, 16, 17, 18]:
    decoded, found = candidates(title)
    print('  th%-3d %d demo(s), %d candidate offset(s)' % (title, len(decoded), len(found)))
    for start, distinct, varied, words in found[:4]:
        print('      +0x%02x distinct=%d varied=%s  %s' % (start, distinct, varied,
              ' '.join('%s' % (w,) for w in words)))
