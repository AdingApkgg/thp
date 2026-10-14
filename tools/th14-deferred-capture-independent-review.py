"""Independent read-only custody, source and complete-buffer review.

Does not run original code, a Native child, compiler, browser or GPU.  The
source-only receipt remains separate from the later physical candidate receipt.
"""
import argparse
import hashlib
import json
import struct
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'artifacts/th14/deferred-capture-pixels-oct14'
CAND = ROOT / 'artifacts/th14/deferred-capture-success-dirty-oct14'
OUT = ROOT / 'artifacts/th14/deferred-capture-independent-review-oct14'


def digest(data):
    return hashlib.sha256(data).hexdigest()


def load(path):
    return json.loads(path.read_bytes())


def binding(path):
    data = path.read_bytes()
    return dict(path=str(path), bytes=len(data), sha256=digest(data))


def check_binding(row):
    path = Path(row['path'])
    if not path.is_absolute():
        path = ROOT / path
    actual = binding(path)
    assert actual['bytes'] == row['bytes'] and actual['sha256'] == row['sha256'], str(path)
    return actual


def original_bytes(data, address, count):
    pe = struct.unpack_from('<I', data, 0x3c)[0]
    optional = pe + 24
    assert struct.unpack_from('<H', data, optional)[0] == 0x10b
    base = struct.unpack_from('<I', data, optional + 28)[0]
    start = optional + struct.unpack_from('<H', data, pe + 20)[0]
    rva = address - base
    for index in range(struct.unpack_from('<H', data, pe + 6)[0]):
        _, section_rva, raw_size, raw = struct.unpack_from('<4I', data, start + index * 40 + 8)
        if section_rva <= rva and rva + count <= section_rva + raw_size:
            return data[raw + rva - section_rva:raw + rva - section_rva + count]
    raise AssertionError('Original instruction outside image')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--source-only', action='store_true')
    args = parser.parse_args()
    report_path = OUT / ('source-review.json' if args.source_only else 'candidate-complete-review.json')
    assert not report_path.exists(), 'Completed independent review is immutable'
    baseline_path = ROOT / 'docs/porting/th14-deferred-capture-pixels-observed-oct14.json'
    baseline = load(baseline_path)
    assert digest(baseline_path.read_bytes()) == 'a16d0fe540103cf0b28511b7f5cc73de63a70bcf925e4b7618e97772fd174f95'
    baseline_custody = [check_binding(row) for row in baseline['bindings']]
    native = load(BASE / 'native.json')
    before = load(BASE / 'webgl-capture/report.json')
    oldbuild = load(BASE / 'webgl-build.json')
    build = load(CAND / 'webgl-build.json')
    native_custody = [check_binding(row) for row in native['bindings'] + native['sourceModuleBindings']]
    assert len(native['cases']) == len(before['reports']) == before['frames'] == 8
    assert native['filter'] == 2 and native['colorKey'] == 0
    assert native['actualSourceDescription'] == [21, 1, 1, 0, 0, 0, 640, 480]
    executable = Path('H:/Games/th/14/th14.exe')
    image = executable.read_bytes()
    assert digest(image) == native['retailExecutableSha256']
    for instruction in native['nativeCode']:
        expected = bytes.fromhex(instruction['bytes'])
        assert original_bytes(image, int(instruction['address'], 16), len(expected)) == expected
    assert original_bytes(image, 0x4691a3, 4).hex() == '85c07521'
    assert original_bytes(image, 0x4691d1, 7).hex() == 'c746f8ffffffff'
    output = (BASE / 'native-output.bin').read_bytes()
    assert struct.unpack_from('<I', output, 8)[0] == 8
    assert list(struct.unpack_from('<8I', output, 12)) == native['actualSourceDescription']
    source = (BASE / 'source.bgra').read_bytes()
    assert output[44:44 + len(source)] == source == (BASE / 'native-source.bgra').read_bytes()
    cursor = 44 + len(source)
    buffers = []
    for index in range(8):
        n = native['cases'][index]
        w = before['reports'][index]
        prior = baseline['comparisons'][index]
        assert n['index'] == w['index'] == index and n['name'] == w['name'] == prior['name']
        assert list(struct.unpack_from('<3i', output, cursor)) == [n['getSurfaceResult'], n['copyResult'], n['dirtyResult']]
        assert list(struct.unpack_from('<8I', output, cursor + 12)) == n['surfaceDescription']
        cursor += 44
        original = (BASE / n['pixelFile']).read_bytes()
        portable = (BASE / 'webgl-capture' / f'portable-{index:03d}.pixels').read_bytes()
        assert output[cursor:cursor + n['bytes']] == original == portable
        assert len(original) == n['bytes'] and digest(original) == n['pixelSha256'] == w['portableSha256'] == prior['nativeSha256'] == prior['portableSha256']
        cursor += n['bytes']
        buffers.append(dict(index=index, name=n['name'], bytes=len(original), sha256=digest(original), independentNativeBeforeEqual=True))
    assert cursor == len(output) and sum(row['bytes'] for row in buffers) == 5242880
    assert len(build['bindings']) == len(oldbuild['bindings']) == 137
    changes = []
    candidate_source_bindings = []
    for index in range(137):
        row = build['bindings'][index]
        old = oldbuild['bindings'][index]
        assert row['snapshot'] == old['snapshot'] and row['beforeSha256'] == old['sha256']
        current = binding(CAND / row['snapshot'])
        prior = binding(BASE / old['snapshot'])
        assert current['sha256'] == row['sha256'] and prior['sha256'] == old['sha256']
        candidate_source_bindings.append(current)
        if current['sha256'] != prior['sha256']:
            changes.append(row['snapshot'])
    assert changes == ['private/cpp/sdl/ApplicationCaptureTh14.hpp']
    assert [f for f in build['flags'] if not f.startswith('-I')] == [f for f in oldbuild['flags'] if not f.startswith('-I')]
    before_helper = (CAND / 'ApplicationCaptureTh14.before.hpp').read_bytes()
    after_helper = (CAND / 'ApplicationCaptureTh14.candidate.hpp').read_bytes()
    newline = b'\r\n' if b'\r\n' in before_helper else b'\n'
    old_text = b'  graphics.backend.resample(Graphics::screen,from,target,to,nullptr,0,0);\n  graphics.changed(target);renderer.invalidate();'.replace(b'\n', newline)
    new_text = b'  if(graphics.backend.resample(Graphics::screen,from,target,to,nullptr,0,0))graphics.changed(target);\n  // Material-cache invalidation is separate from the successful target write.\n  renderer.invalidate();'.replace(b'\n', newline)
    assert before_helper.count(old_text) == 1 and before_helper.replace(old_text, new_text) == after_helper
    assert digest(after_helper) == build['captureConsumerSha256'] == 'ef546985ec5786f78a869575cc1e70a41463cd8061ca645139cfe9c3bf1ffebd'
    for name, key in [('capture.wasm', 'wasmSha256'), ('capture.mjs', 'loaderSha256'), ('success-dirty.patch', 'patchSha256')]:
        assert digest((CAND / name).read_bytes()) == build[key]
    state_custody = []
    for row in build['stateBindings']:
        actual = binding(CAND / row['snapshot'])
        assert actual['sha256'] == row['sha256']
        state_custody.append(actual)
    renderer = (CAND / 'private/portable/sdl/Renderer.cpp').read_text()
    assert renderer.index('if(src==dst)return false;') < renderer.index('flush();auto& input=surface(src)')
    assert renderer.index('if(!im[0]||!om[0])return false;') < renderer.index('flush();auto& input=surface(src)')
    assert 'void AnmRenderer::invalidate(){flush();texture_handle=blend_mode=filter=~0u;uv_sprite=nullptr;}' in (CAND / 'state-source/AnmRenderer.cpp').read_text()
    assert 'backend.flush();++it->second.revision;' in (CAND / 'state-source/GraphicsDevice.hpp').read_text()
    candidate_physical = None
    physical_bindings = []
    if not args.source_only:
        candidate_path = ROOT / 'docs/porting/th14-deferred-capture-success-dirty-verified-oct14.json'
        candidate = load(candidate_path)
        web = load(CAND / 'webgl-capture/report.json')
        assert candidate['privateSuccessDirtyCandidateVerified'] and not candidate['productionChanged'] and not candidate['completeGame'] and not candidate['nativeEquivalent']
        assert len(web['reports']) == web['frames'] == len(candidate['comparisons']) == 8
        assert candidate['toolSha256'] == digest((ROOT / 'tools/th14-deferred-capture-success-dirty-evidence-check.py').read_bytes())
        rows = []
        for index in range(8):
            n, w, receipt = native['cases'][index], web['reports'][index], candidate['comparisons'][index]
            data = (CAND / 'webgl-capture' / f'portable-{index:03d}.pixels').read_bytes()
            original = (BASE / n['pixelFile']).read_bytes()
            assert n['index'] == w['index'] == index and data == original
            assert digest(data) == w['portableSha256'] == receipt['candidateSha256'] == n['pixelSha256']
            assert w['words'] == [-1, 1, 1, 1, 1, 1, 0, 1, 2, 1]
            rows.append(dict(index=index, bytes=len(data), sha256=digest(data), actualNativeAndBeforeEqual=True))
        assert [row['mode'] for row in web['controls']] == [0, 1, 2]
        assert web['controls'][0]['words'] == web['controls'][1]['words'] == [-1, 0, 0, 0, 0, 0, 0, 1, 2, 0]
        assert web['controls'][2]['words'] == [-1, 0, 1, 1, 1, 0, 0, 1, 2, 0]
        assert before['controls'][2]['words'] == [-1, 1, 1, 1, 1, 0, 0, 1, 2, 0]
        candidate_physical = dict(cases=8, comparedRawBytes=sum(row['bytes'] for row in rows), differentBytes=0, rows=rows, controls=web['controls'])
        physical_bindings = [binding(candidate_path), binding(CAND / 'webgl-capture/report.json')]
    report = dict(independentSourceReviewPassed=True, candidatePhysicalReviewPassed=not args.source_only, productionChanged=False, completeGame=False, nativeEquivalent=False,
                  actualIssues=[], baselineCustody=baseline_custody, originalModulesAndCaptureCustody=native_custody,
                  originalExecutable=binding(executable), originalInstructionsChecked=len(native['nativeCode']), originalRetireInstruction=dict(address='0x4691d1', bytes='c746f8ffffffff'),
                  baselineFullBufferComparison=buffers, baselineFullBufferBytes=5242880, candidateSourceBindings=candidate_source_bindings, stateBindings=state_custody,
                  changedFiles=changes, originalDirtyAndRetirementControls=baseline['originalDirtyAndRetirementControls'], candidatePhysical=candidate_physical,
                  sourceAudit=dict(successOnlyDirty=True, unconditionalMaterialInvalidate=True, queueRetirementUnchanged=True,
                                   reason='Target revision reports a successful accepted backend copy; ANM invalidate separately flushes and clears its material cache. Native result==0 alone calls dirty and the original record retires for every declared result.',
                                   falseReturnLimit='Current Renderer refuses same source/destination and unsupported formats before GL mutation; true does not check an actual GL error. Controlled false adapter does not establish universal HRESULT mapping.'),
                  referenceDomain='Independent original32 system D3D9 HAL/D3DX on explicit synthetic 640x480 BGRA source, real text52 512x512 RGB565 target/request plus seven declared rectangle/ARGB8 controls. Filter 2 POINT, colorKey 0, no dither. Full output was independently decomposed and checked. No retail child, compositor, complete game/frame, actual GL failure mapping or all-format guarantee.',
                  bindings=[binding(p) for p in [baseline_path, CAND / 'webgl-build.json', CAND / 'capture.wasm', CAND / 'capture.mjs', CAND / 'ApplicationCaptureTh14.before.hpp', CAND / 'ApplicationCaptureTh14.candidate.hpp', CAND / 'success-dirty.patch', ROOT / 'tools/th14-deferred-capture-success-dirty-evidence-check.py', ROOT / 'tools/th14-deferred-capture-success-dirty-build.py']] + physical_bindings,
                  officialReferences=baseline['officialReferences'], toolSha256=digest(Path(__file__).read_bytes()))
    OUT.mkdir(parents=True, exist_ok=True)
    report_path.write_bytes((json.dumps(report, indent=2) + '\n').encode())
    print(json.dumps(dict(report=binding(report_path), sourcePassed=True, candidatePhysicalPassed=not args.source_only, baselineFullBuffers=8, baselineFullBytes=5242880)))


if __name__ == '__main__':
    main()
