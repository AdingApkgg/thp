"""Generalised solve: a replay is a header plus `n` records of equal stride, where each record
carries a stage number and a payload. For each (record start, payload field offset, number of
stages) that makes the strides tile the decoded length exactly, print the shape - and require the
same shape for every demo a title ships.

Validated first on TH12 and TH13, where the answer is already known (0x70/0xA0 for one record,
0x74/0xC4).

  py -3 tools/tmp/replay-shape-solve.py
"""
import struct
from pathlib import Path

module = {}
src = Path('tools/th-replay-container.py').read_text(encoding='utf-8').partition('if __name__')[0]
exec(compile(src, 'replay-keys-search', 'exec'), module)
fields, decode_with, demo_files = module['fields'], module['decode_with'], module['demo_files']
TH12 = ((0x5e, 0xe1, 0x800), (0x7d, 0x3a, 0x40))
GENERATION = ((0x5c, 0xe1, 0x400), (0x7d, 0x3a, 0x100))
PAYLOAD_OFFSETS = (6, 8, 10, 12, 16)


def shapes(decoded):
    """Every (start, payload field, stride, payload, sh) that tiles the buffer exactly."""
    total = len(decoded)
    found = set()
    for start in range(0x40, 0x140, 2):
        for payload_at in PAYLOAD_OFFSETS:
            for count in range(1, 8):
                span = total - start
                if span % count:
                    continue
                stride = span // count
                if stride < 0x40 or stride > total:
                    continue
                stages, ok, payload = [], True, 0
                for index in range(count):
                    record = start + index * stride
                    stage = struct.unpack_from('<H', decoded, record)[0]
                    if not 1 <= stage <= 7 or stage in stages:
                        ok = False
                        break
                    stages.append(stage)
                    payload = struct.unpack_from('<I', decoded, record + payload_at)[0]
                    if payload <= 0 or payload + 0x40 > stride:
                        ok = False
                        break
                if ok:
                    found.add((start, payload_at, count, stride, payload, stride - payload))
    return found


for title in (12, 13, 14, 16, 17, 18):
    pair = TH12 if title == 12 else GENERATION
    per_demo = []
    for path in demo_files(title):
        data, packed, unpacked = fields(path)
        per_demo.append((path.name, shapes(decode_with(data, packed, unpacked, pair))))
    shapes_of_columns = [{(s, p, c, sh) for (s, p, c, stride, payload, sh) in found}
                        for _, found in per_demo]
    common = set.intersection(*shapes_of_columns) if shapes_of_columns else set()
    print('  th%d: %d demo(s), %d common shape(s)' % (title, len(per_demo), len(common)))
    for start, payload_at, count, sh in sorted(common):
        for name, found in per_demo:
            hit = [f for f in found if (f[0], f[1], f[2], f[5]) == (start, payload_at, count, sh)]
            stride, payload = hit[0][3], hit[0][4]
            print('       %-10s start 0x%x payload at +%d count %d stride 0x%x payload %d fixed 0x%x'
                  % (name, start, payload_at, count, stride, payload, sh))
