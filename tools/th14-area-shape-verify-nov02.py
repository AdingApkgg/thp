import argparse
import collections
import gzip
import hashlib
import importlib.util
import json
import struct
from pathlib import Path

R = Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser(description='Compare retained original area/shot bytes with portable diagnostic samples')
parser.add_argument('--native',type=Path,required=True)
parser.add_argument('--model',type=Path,required=True)
parser.add_argument('--output',type=Path,required=True)
args=parser.parse_args()
assert not args.output.exists()
assert args.native.resolve().is_relative_to(R / 'artifacts/th14')
assert args.model.resolve().is_relative_to(R / 'artifacts/th14')
assert args.output.resolve().is_relative_to(R / 'artifacts/th14')
spec = importlib.util.spec_from_file_location('schema', R / 'tools/th14-combat-pool-readonly-v3-oct25.py')
schema = importlib.util.module_from_spec(spec)
spec.loader.exec_module(schema)
compressed = (args.native / 'area-shot-window.bin.gz').read_bytes()
raw = gzip.decompress(compressed)
stride = 8 + 256 * (0xa4 + 0xd0)
assert len(raw) == 801 * stride
native = {}
for i in range(801):
    base = i * stride
    callback, player = struct.unpack_from('<2I', raw, base)
    assert callback == 4000 + i
    families = {}
    for name, offset, size, fields, active_offset in [
        ('areas', 8, 0xa4, schema.AREA_FIELDS, 0x10),
        ('shots', 8 + 256 * 0xa4, 0xd0, schema.SHOT_FIELDS, 0x98),
    ]:
        rows = []
        for slot in range(256):
            begin = base + offset + slot * size
            value = struct.unpack_from('<I', raw, begin + active_offset)[0]
            active = bool(value & 1) if name == 'areas' else bool(value)
            if active:
                rows.append(schema.selected(raw[begin:begin + size], fields, slot))
        families[name] = rows
    native[callback] = families
portable = json.loads((args.model / 'area-shape-rows.json').read_bytes())
assert [row['callback'] for row in portable['rows']] == list(range(4400, 4801))
counts = collections.Counter()
first = {}
differences = []
for sample in portable['rows']:
    callback = sample['callback']
    for name, fields in [('areas', schema.AREA_FIELDS), ('shots', schema.SHOT_FIELDS)]:
        for rows in (native[callback][name], sample['rows'][name]):
            slots = [row[0] for row in rows]
            assert slots == sorted(set(slots)) and all(0 <= slot < 256 for slot in slots)
            assert all(len(row) == len(fields) for row in rows)
            assert all(isinstance(word, int) and 0 <= word < 2**32 for row in rows for word in row)
        n = {r[0]: r for r in native[callback][name]}
        p = {r[0]: r for r in sample['rows'][name]}
        for slot in sorted(n.keys() | p.keys()):
            values = [('presence', int(slot in n), int(slot in p))] if slot not in n or slot not in p else [
                (field, nv, pv) for (field, _), nv, pv in zip(fields, n[slot], p[slot], strict=True) if nv != pv]
            for field, nv, pv in values:
                key = name + '.' + field
                row = dict(callback=callback, family=name, slot=slot, field=field, native=nv, portable=pv)
                counts[key] += 1
                first.setdefault(key, row)
                differences.append(row)
report = dict(nativeCompressedSha256=hashlib.sha256(compressed).hexdigest(),
              nativeRawSha256=hashlib.sha256(raw).hexdigest(), nativeRows=801,
              portableRows=len(portable['rows']), comparedWindow=[4400, 4800],
              differenceCounts=counts, firstDifferences=first,
              firstDifference=differences[0] if differences else None,
              differences=differences, originalRawBytesRetained=True,
              nativeValuesProvidedToEngine=False, completeGame=False, nativeEquivalent=False)
report['allCapturedActiveAreaAndShotWordsEqual']=not differences
report['nativeRawAbiSchemaToolSha256']=hashlib.sha256((R/'tools/th14-combat-pool-readonly-v3-oct25.py').read_bytes()).hexdigest()
report['verifierSha256']=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
report['modelPayloadSha256']=hashlib.sha256((args.model/'area-shape-rows.json').read_bytes()).hexdigest()
out = args.output
assert not out.exists()
out.write_text(json.dumps(report, indent=2) + '\n', encoding='utf8')
print(json.dumps({k: v for k, v in report.items() if k != 'differences'}))
