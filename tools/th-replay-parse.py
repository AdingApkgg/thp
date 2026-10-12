"""Walk a title's attract demos the way the port walks them, using the port's own constants.

This reads `replay_file_header`, `replay_stage_header` and `replay_selection` out of Replay.hpp
and the title's character/loadout counts out of ShotFiles.hpp, then runs every check the load path
runs: the selection words must be in range, the `n` records must tile the decoded length exactly,
each record's stage number must be 1..7, and the frame rate must fit inside the payload. It is a
dry run of `Replay::open` for a title that has not been booted yet, and it is allowed to fail:
if a per-title row is wrong, one of the demos says so.

  py -3 tools/th-replay-parse.py [title...]
"""
import io
import re
import struct
import sys
from pathlib import Path

CPP = Path('runtimes/th12/th12_web/cpp/game')

# The title's own shot table. Two rows, read out of the file the same way the port reads them;
# the assertion is on the row being there, so a signature change cannot pass silently.
SHOT_TEXT = io.open(CPP / 'ShotFiles.hpp', encoding='utf-8').read()
assert re.search(r'shot_file_count\s*=\s*kPortTitle==13\?4u', SHOT_TEXT), 'shot_file_count row moved'
assert re.search(r'shot_loadout_count\s*=\s*kPortTitle==17\?3u', SHOT_TEXT), 'shot_loadout_count row moved'
SHOT_COUNT = {13: 4, 14: 6, 16: 4, 17: 9, 18: 4, 12: 6}
LOADOUT = {17: 3, 13: 1, 16: 1, 18: 1, 12: 2, 14: 2}

module = {}
src = Path('tools/th-replay-container.py').read_text(encoding='utf-8').partition('if __name__')[0]
exec(compile(src, 'th-replay-container', 'exec'), module)
fields, decode_with, demo_files = module['fields'], module['decode_with'], module['demo_files']
TH12_PAIR = ((0x5e, 0xe1, 0x800), (0x7d, 0x3a, 0x40))


def read_constant(name):
    """title -> value, out of the ternary chain the header carries."""
    text = io.open(CPP / 'Replay.hpp', encoding='utf-8').read()
    match = re.search(r'inline constexpr u32 ' + name + r'\s*=\s*(.*?);', text, re.S)
    if not match:
        raise SystemExit('  %s not found in Replay.hpp' % name)
    body = ' '.join(match.group(1).split())
    rows = {int(condition): int(value, 16)
            for condition, value in re.findall(r'kPortTitle==(\d+)\?0x([0-9A-Fa-f]+)u', body)}
    fallback = re.search(r':0x([0-9A-Fa-f]+)u\s*$', body)
    for title in (12, 13):
        rows.setdefault(title, int(fallback.group(1), 16))
    return rows


selection = read_constant('replay_selection')
file_header = read_constant('replay_file_header')
stage_header = read_constant('replay_stage_header')


def parse(title, path):
    data, packed, unpacked = fields(path)
    decoded = decode_with(data, packed, unpacked, TH12_PAIR if title == 12 else module['GENERATION']
                         if 'GENERATION' in module else ((0x5c, 0xe1, 0x400), (0x7d, 0x3a, 0x100)))
    if len(decoded) != unpacked:
        return 'decompress wrote %d of %d' % (len(decoded), unpacked)
    if decoded[:3] != b'ZUN':
        return 'decoded body does not start with ZUN'
    character_max = SHOT_COUNT[title] // LOADOUT[title] - 1
    subtype_max = LOADOUT[title] - 1
    at = selection[title]
    count, character, subtype, difficulty = struct.unpack_from('<IIII', decoded, at)
    if not 1 <= count <= 7:
        return 'stage count %d' % count
    if character > character_max:
        return 'character %d > %d' % (character, character_max)
    if subtype > subtype_max:
        return 'shot type %d > %d' % (subtype, subtype_max)
    if difficulty > 4:
        return 'difficulty %d' % difficulty
    offset = file_header[title]
    shift = stage_header[title]
    records = []
    for index in range(count):
        if offset + shift > len(decoded):
            return 'record %d reaches %d of %d' % (index, offset + shift, len(decoded))
        # the record's own layout: stage word at +0, frame count at +4, payload at +8 (the
        # record's fixed scalars fill the rest of `shift`). One unpack per field, since a
        # single struct format would silently place the u32 fields at +2 and +6.
        stage_number = struct.unpack_from('<H', decoded, offset)[0]
        frames = struct.unpack_from('<I', decoded, offset + 4)[0]
        payload = struct.unpack_from('<I', decoded, offset + 8)[0]
        if not 1 <= stage_number <= 7:
            return 'record %d stage number %d' % (index, stage_number)
        records.append('%d:%.1fk/%d' % (stage_number, frames / 1000.0, payload))
        offset += shift + payload
    if offset != len(decoded):
        return 'the walk ends at %d of %d' % (offset, len(decoded))
    return 'count=%d char=%d shot=%d diff=%d  %s' % (count, character, subtype, difficulty,
                                                   ' '.join(records))


for title in [int(a) for a in sys.argv[1:]] or [12, 13, 14, 16, 17, 18]:
    print('  th%-3d selection +0x%02x, file header 0x%x, fixed part 0x%x'
          % (title, selection[title], file_header[title], stage_header[title]))
    for path in demo_files(title):
        try:
            print('      %-10s %s' % (path.name, parse(title, path)))
        except Exception as error:
            print('      %-10s %s: %s' % (path.name, type(error).__name__, error))
