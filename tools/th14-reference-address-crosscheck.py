"""Cross-check external TH14 annotations as data, without executing that code."""
import ast
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FOLDER = ROOT / 'artifacts/th14/reference-projects'
sources = json.loads((FOLDER / 'sources.json').read_text(encoding='utf-8'))
for source in sources:
    data = (ROOT / source['file']).read_bytes()
    assert len(data) == source['bytes']
    assert hashlib.sha256(data).hexdigest() == source['sha256']

tree = ast.parse((FOLDER / 'parakit-offsets.py').read_bytes())
entry = next(value for node in ast.walk(tree) if isinstance(node, ast.Dict)
             for key, value in zip(node.keys, node.values)
             if isinstance(key, ast.Constant) and key.value == 'th14.exe')
fields = {}
for group in entry.keywords:
    if group.arg in ('statics', 'environment', 'player', 'bullets', 'enemies'):
        fields[group.arg] = {k.arg: ast.literal_eval(k.value)
                             for k in group.value.keywords
                             if isinstance(k.value, ast.Constant)}

expected = {
    0x4011d0: 'register__on_draw',
    0x4013b0: 'UpdateFuncRegistry::run_all_on_draw',
    0x40e2f0: 'Stage::on_draw_03',
    0x40e790: 'Stage::on_draw_06',
    0x40eb80: 'Stage::on_draw_03__stub',
    0x40eb90: 'Stage::on_draw_06__stub',
    0x475e60: 'AnmManager::reset_vertex_buffers',
    0x478f60: 'AnmManager::draw_vm',
    0x479900: 'AnmManager::draw_vm__ins_607__drawRectShadow',
}
selected = {}
for row in json.loads((FOLDER / 'th-re-data-th14-funcs.json').read_text(encoding='utf-8')):
    address = int(row['addr'], 16)
    if address in expected:
        assert row['name'] == expected[address], (hex(address), row['name'])
        selected[hex(address)] = row['name']
assert len(selected) == len(expected)
assert fields['statics']['game_speed'] + 0x400000 == 0x4d8f58
assert fields['environment']['stage'] + 0x400000 == 0x4f58a4
assert fields['statics']['visual_rng'] + 0x400000 == 0x4db508
assert fields['statics']['replay_rng'] + 0x400000 == 0x4db510
report = {
    'passed': True,
    'sourceFiles': sources,
    'functions': selected,
    'relativeOffsets': fields,
    'toolSha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    'scope': 'External reference data parsed as AST constants/JSON only, never executed. '
             'TH14 function labels and stage/rate/visual/replay RNG globals cross-checked '
             'against independently recovered native entry addresses. Annotation agreement '
             'is not an original execution or gameplay equivalence proof.',
}
(ROOT / 'docs/porting/th14-reference-address-crosscheck-oct12.json').write_text(
    json.dumps(report, indent=2) + '\n', encoding='utf-8')
print(json.dumps({'passed': True, 'functions': len(selected), 'groups': len(fields)}))
