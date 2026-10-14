"""Read-only audit of already executed original/current resolution controls.

Never imports a fixture or starts Unicorn, WASI, a compiler, Native or a browser.
Writes only one new bounded metadata receipt; private traces/raw outputs stay put.
"""
import hashlib
import json
import math
from pathlib import Path
import struct

ROOT = Path(__file__).resolve().parents[1]
ORIGINAL = ROOT / 'artifacts/th14/screen-camera-resolution-original-prepared-oct15'
CURRENT = ROOT / 'artifacts/th14/startup-camera-resolution-control-prepared-oct15'
OUT = ROOT / 'docs/porting/th14-screen-camera-resolutions-observed-oct15.json'
ORIGINAL_REPORT_SHA = 'd79675d0d21bf0a856d3c217a9b426873d37b5177284f113d4474da735c5c580'
CURRENT_REPORT_SHA = 'be6390edd235a7fe53c9d22f5099a06b8f3591b03d0b367b388064ed3d770b4b'
BINDINGS = {}


def sha(data):
    return hashlib.sha256(data).hexdigest()


def read(path, digest=None, size=None):
    path = Path(path).resolve()
    data = path.read_bytes()
    if digest is not None:
        assert sha(data) == digest, path
    if size is not None:
        assert len(data) == size, path
    try:
        name = path.relative_to(ROOT).as_posix()
    except ValueError:
        name = path.as_posix()
    BINDINGS[name] = dict(path=name, bytes=len(data), sha256=sha(data))
    return data


def pinned(binding):
    return read(binding['path'], binding['sha256'], binding['bytes'])


def load(path, digest=None):
    return json.loads(read(path, digest))


def pe_image(data):
    pe = struct.unpack_from('<I', data, 0x3c)[0]
    assert data[:2] == b'MZ' and data[pe:pe+4] == b'PE\0\0'
    opt = pe+24
    assert struct.unpack_from('<H', data, opt)[0] == 0x10b
    base, size, headers = [struct.unpack_from('<I', data, opt+i)[0] for i in (28, 56, 60)]
    mapped = bytearray(size)
    mapped[:headers] = data[:headers]
    sections = opt+struct.unpack_from('<H', data, pe+20)[0]
    for i in range(struct.unpack_from('<H', data, pe+6)[0]):
        virtual, rva, count, raw = struct.unpack_from('<4I', data, sections+i*40+8)
        assert rva+max(virtual, count) <= size and raw+count <= len(data)
        mapped[rva:rva+count] = data[raw:raw+count]
    return base, bytes(mapped)


def u32_words(data, count):
    assert len(data) == count*4
    return list(struct.unpack('<'+str(count)+'I', data))


def raw_array(words, count):
    assert len(words) == count and all(type(x) is int and 0 <= x <= 0xffffffff for x in words)
    return struct.pack('<'+str(count)+'I', *words)


def wasm_abi(data):
    assert data[:8] == b'\0asm\1\0\0\0'
    def leb(at):
        value, shift = 0, 0
        while True:
            byte = data[at]
            at += 1
            value |= (byte & 127) << shift
            if not byte & 128:
                return value, at
            shift += 7
            assert shift <= 35
    def name(at):
        length, at = leb(at)
        return data[at:at+length].decode('utf-8'), at+length
    at, import_count, exports = 8, 0, []
    while at < len(data):
        kind = data[at]
        length, start = leb(at+1)
        end = start+length
        assert end <= len(data)
        if kind == 2:
            import_count, p = leb(start)
            assert import_count == 0, 'This actual module reports no imports'
            assert p == end
        if kind == 7:
            count, p = leb(start)
            for _ in range(count):
                text, p = name(p)
                export_kind = data[p]
                _, p = leb(p+1)
                exports.append(dict(name=text, kind=['function', 'table', 'memory', 'global', 'tag'][export_kind]))
            assert p == end
        at = end
    return dict(importCount=import_count, exports=exports)


def main():
    assert not OUT.exists(), 'Preserve immutable observation receipts'
    read(__file__)
    original = load(ORIGINAL/'run-oct15/report.json', ORIGINAL_REPORT_SHA)
    current = load(CURRENT/'run-oct15/report.json', CURRENT_REPORT_SHA)
    inputs = load(ORIGINAL/'inputs.json', original['inputsSha256'])
    original_plan = load(ORIGINAL/'plan.json')
    source = read(ORIGINAL/'fixture.py', original['sourceSha256'])
    assert source == pinned(original_plan['source'])
    assert pinned(original_plan['inputs']) == read(ORIGINAL/'inputs.json')
    for binding in inputs['bindings']:
        pinned(binding)
    assert original['bindings'] == inputs['bindings']
    assert original['originalCodeSpans'] == inputs['originalCodeSpans']
    images = [pe_image(pinned(inputs['executable'])), pe_image(pinned(inputs['d3dx']))]
    def original_bytes(address, count):
        for base, data in images:
            if base <= address and address+count <= base+len(data):
                return data[address-base:address-base+count]
        raise AssertionError('Unbound original address')
    for span in inputs['originalCodeSpans']:
        data = original_bytes(span['address'], span['bytes'])
        assert data.hex() == span['hex'] and sha(data) == span['sha256']
    assert original['bothProfilesCompleted'] is True
    assert original['declaredFpuState'] == dict(fpcw=0x37f, mxcsr=0x1f80, nativeMeasured=False)
    for key in ['nativeCpuMeasured', 'nativeSnapshotUsed', 'originalCodePatched', 'productionChanged', 'completeColdStart', 'nativeEquivalent', 'completeGame']:
        assert original[key] is False
    plan = json.loads(pinned(current['plan']))
    portable_inputs = json.loads(pinned(current['inputs']))
    assert pinned(current['originalReport']) == read(ORIGINAL/'run-oct15/report.json')
    assert portable_inputs['originalReport'] == current['originalReport']
    for binding in plan['requiredBindings']:
        pinned(binding)
    assert current['sourceFiles'] == plan['sourceFiles'] and len(current['sourceFiles']) == 15
    current_sources = []
    for binding in current['sourceFiles']:
        frozen = pinned(binding)
        production_path = ROOT/'runtimes/th12/th12_web/cpp/game'/Path(binding['path']).name
        actual = read(production_path, binding['sha256'], binding['bytes'])
        assert actual == frozen
        current_sources.append(BINDINGS[production_path.relative_to(ROOT).as_posix()])
    assert pinned(current['fixture']) == pinned(plan['fixture'])
    pinned(current['runner'])
    assert '-O2' in plan['compilerArguments'] and '-ffp-contract=off' in plan['compilerArguments']
    assert '-DPORT_TITLE=14' in plan['compilerArguments']
    abi = wasm_abi(pinned(current['wasm']))
    assert current['imports'] == [] and abi['importCount'] == 0
    assert current['exports'] == abi['exports']
    assert sorted(x['name'] for x in abi['exports']) == sorted(plan['exports'])
    assert current['executionCounts'] == dict(compiles=1, wasiInstances=1, screenCalls=8,
        mathCalls=16, originalX86=0, nativeProcesses=0, browser=0, audio=0)
    assert current['productionChanged'] is False and current['productionObjectsRebuilt'] == 0
    assert current['nativeEquivalent'] is False and current['completeGame'] is False
    assert len(original['profiles']) == len(current['results']) == len(portable_inputs['profiles']) == 2
    phases = [('d3dx-dispatch-initializer', 0x101bc521, 0),
              ('original-supervisor-ctor', 0x447a40, 0x4d8f60),
              ('original-viewport-dimensions', 0x46ae40, 0x4f5a18),
              ('original-screen-camera-reset', 0x4465e0, 0x4d8f60)]
    camera_contract = [('full', 0x4d93e8, 2), ('play', 0x4d9190, 0),
                       ('scaled', 0x4d92bc, 1), ('world', 0x4d9514, 3)]
    profiles = []
    for i, (label, config, width, height, scale) in enumerate([
            ('960', 16, 960, 720, 0x3fc00000), ('1280', 20, 1280, 960, 0x40000000)]):
        p, q, portable_input = original['profiles'][i], current['results'][i], portable_inputs['profiles'][i]
        assert p['label'] == q['label'] == portable_input['label'] == label
        assert p['declaredConfigWord'] == portable_input['configWord'] == config
        dimensions = dict(width=width, height=height, scaleWord=scale)
        assert p['generatedDimensions'] == portable_input['generatedDimensions'] == dimensions
        assert p['hostConfigurationWrite'] == dict(address=0x4f7a54, beforeWord=0, afterWord=config, kind='declared-configuration-input')
        assert p['completed'] and p['allEightMathOutputsFinite'] and p['executionError'] is None
        assert p['stop']['reason'] == 'original-function-returned'
        assert p['declaredFpuState'] == original['declaredFpuState'] == portable_input['declaredFpuState']
        assert p['finalFpuState'] == dict(fpcw=0x37f, mxcsr=0x1f80)
        assert len(p['phaseResults']) == 4 and len(p['originalD3dxMathCalls']) == 8 and not p['pendingD3dxMathCalls']
        assert len(p['cameras']) == 4
        assert len(p['originalInstructions']) == p['codeHookObservations'] < 10000
        assert [x['index'] for x in p['originalInstructions']] == list(range(1, p['codeHookObservations']+1))
        assert sum(x['codeHookObservations'] for x in p['phaseResults']) == p['codeHookObservations']
        for row, contract in zip(p['phaseResults'], phases):
            assert (row['phase'], row['entry'], row['owner']) == contract
            assert row['originalReturnVerified'] and row['stop']['reason'] == 'original-function-returned'
            assert row['initialRegisters']['esp'] == 0x7001ff00 and row['returnedRegisters']['esp'] == 0x7001ff04
            assert row['returnedRegisters']['eip'] == 0x20000000
            phase_trace = [x for x in p['originalInstructions'] if x['phase'] == row['phase']]
            assert phase_trace[0]['address'] == row['entry'] and len(phase_trace) == row['codeHookObservations']
        for row in p['originalInstructions']:
            data = bytes.fromhex(row['bytes'])
            assert original_bytes(row['address'], len(data)) == data
        actual_dimension_writes = [(x['pc'], x['address'], x['bytes'], x['value']) for x in p['nonStackOriginalMemoryWrites']
                                  if x['address'] in (0x4f7a64, 0x4f7a68, 0x4f7a6c)]
        assert actual_dimension_writes == [(0x46ae89, 0x4f7a6c, 4, scale),
                                          (0x46aea8, 0x4f7a68, 4, height), (0x46aeb5, 0x4f7a64, 4, width)]
        assert p['originalRngMemoryUnchanged'] and p['initialRngHex'] == p['finalRngHex'] == '00'*16
        rng_writes = [x for x in p['nonStackOriginalMemoryWrites'] if x['address'] < 0x4db518 and x['address']+x['bytes'] > 0x4db508]
        assert not rng_writes
        for key in ['hostMathResultWrites', 'hostRngStateWrites', 'hostGeneratedDimensionsWrites', 'realOsApisCalled',
                    'realThreadsCreated', 'audioPlayed', 'retailProcessesStarted', 'originalGameFilesWritten']:
            assert p[key] == 0
        expected_parameters, expected_matrices, camera_inputs = [], [], []
        for ci, (camera, contract) in enumerate(zip(p['cameras'], camera_contract)):
            assert (camera['name'], camera['owner'], camera['modeWord']) == contract
            look, projection = p['originalD3dxMathCalls'][2*ci:2*ci+2]
            owner = camera['owner']
            assert camera['fovWord'] == 0x3f060a92
            assert camera['parametersRaw13Words'] == camera['positionWords']+[camera['fovWord']]+camera['viewportWords']+[camera['modeWord']]+camera['offsetWords']
            for call, function, pc, slot, offset, argc in [
                    (look, 'D3DXMatrixLookAtLH', 0x446377, 0x4b12ec, 0x60, 4),
                    (projection, 'D3DXMatrixPerspectiveFovLH', 0x4463e7, 0x4b12e8, 0xa0, 5)]:
                assert (call['function'], call['callAddress'], call['iat']) == (function, pc, slot)
                assert call['returnTarget'] == pc+6 and call['outputPointer'] == call['arguments'][0] == owner+offset
                assert len(call['arguments']) == argc and call['outputBytes'] == 64
                assert call['originalReturnVerified'] and call['returnVerified'] and call['hostMathResultWrites'] == 0
                assert call['returnedRegisters']['eax'] == call['outputPointer']
                assert call['returnedRegisters']['esp'] == call['expectedEsp']
                assert call['returnedRegisters']['eip'] == call['returnTarget']
                assert len(call['afterWords']) == 16
                assert all(math.isfinite(x) for x in struct.unpack('<16f', raw_array(call['afterWords'], 16)))
            assert look['afterWords'] == camera['viewWords'] and projection['afterWords'] == camera['projectionWords']
            assert len(look['inputVectorWords']) == 3 and all(len(v) == 3 for v in look['inputVectorWords'])
            assert projection['arguments'][1] == camera['fovWord']
            expected_parameters.extend(x for v in look['inputVectorWords'] for x in v)
            expected_parameters.extend(projection['arguments'][1:])
            expected_matrices.extend(look['afterWords']+projection['afterWords'])
            camera_inputs.extend(camera['viewportWords']+[camera['fovWord'], camera['modeWord']])
        assert camera_inputs == portable_input['inputWords']
        assert len(camera_inputs) == 32 and len(expected_parameters) == 52 and len(expected_matrices) == 128
        assert expected_parameters == portable_input['parameterWords'] and expected_matrices == portable_input['matrixWords']
        parameters = u32_words(pinned(q['parameterOutput']), 52)
        matrices = u32_words(pinned(q['matrixOutput']), 128)
        assert parameters == q['parameters'] and matrices == q['matrices']
        parameter_differences = [dict(camera=k//13, word=k%13, portWord=a, originalWord=b)
                                 for k, (a, b) in enumerate(zip(parameters, expected_parameters)) if a != b]
        matrix_differences = [dict(camera=k//32, matrix='view' if k%32 < 16 else 'projection', word=k%16, portWord=a, originalWord=b)
                              for k, (a, b) in enumerate(zip(matrices, expected_matrices)) if a != b]
        assert parameter_differences == q['parameterDifferences'] and matrix_differences == q['matrixDifferences']
        assert len(parameter_differences) == q['parameterDifferenceCount'] and len(matrix_differences) == q['matrixDifferenceCount']
        profiles.append(dict(label=label, declaredConfigWord=config, generatedDimensions=dimensions,
            originalCodeHookObservations=p['codeHookObservations'], phaseCodeHookObservations=[x['codeHookObservations'] for x in p['phaseResults']],
            originalMathCalls=8, originalMathReturnsVerified=8, originalMatricesFinite=True,
            originalRngMemoryUnchanged=True, originalRngWritesObserved=0,
            cameraCount=4, cameraInputWords=32, comparedParameterWords=52, comparedMatrixWords=128,
            parameterDifferences=parameter_differences, matrixDifferences=matrix_differences,
            parameterDifferenceCount=len(parameter_differences), matrixDifferenceCount=len(matrix_differences),
            parameterBytes=208, parameterSha256=sha(raw_array(parameters, 52)),
            matrixBytes=512, matrixSha256=sha(raw_array(matrices, 128))))
    assert current['comparedParameterWords'] == 104 and current['comparedMatrixWords'] == 256
    passed = all(not p['parameterDifferences'] and not p['matrixDifferences'] for p in profiles)
    assert current['comparisonPassed'] == passed
    report = dict(schema='th14-screen-camera-resolution-observation-v1',
        evidenceVerified=True, comparisonPassed=passed, originalEntryOrder=[hex(x[1]) for x in phases],
        originalThisOrder=[hex(x[2]) for x in phases], declaredConfigurationAddress='0x4f7a54',
        declaredFpuState=original['declaredFpuState'], profiles=profiles, cameraCount=8,
        comparedParameterWords=104, comparedMatrixWords=256,
        parameterWordMeaning='Forwarded math call boundaries: Eye3,At3,Up3 and Perspective FOV/aspect/near/far4 per camera. These13 are distinct from original camera position/FOV/viewport/mode/offset metadata13.',
        sourceBindings=current_sources, currentFrozenSourceByteIdentical=True,
        compilerFlags=['-O2', '-ffp-contract=off', '-DPORT_TITLE=14'], moduleAbi=abi,
        producerRecordedExecutionCounts=dict(originalProfiles=2, portableCompiles=1, portableWasiInstances=1,
                                           portableScreenCalls=8, portableMathCalls=16),
        reviewerExecutionCounts=dict(originalX86=0, unicorn=0, wasi=0, compiler=0, nativeProcesses=0, browser=0, audio=0),
        bindings=sorted(BINDINGS.values(), key=lambda b:b['path']),
        productionChanged=False, nativeCpuMeasured=False, nativeEquivalent=False,
        gpuPixelsVerified=False, allResolutionsVerified=False, allCameraModesVerified=False,
        completeColdStart=False, completeGame=False,
        scope='Independent readonly bytes/hash/ABI and complete raw word comparisons of two already executed supported-resolution controls. Original PE/D3DX pure functions execute in Unicorn with declared configuration and FPCW037f/MXCSR1f80, pinned dispatch baseline and controlled frames; this is not a Native CPU/process/cold-start measurement. Current source-identical SceneCamera.screen and GraphicsMath were compiled once into a tiny forwarding-observer reactor and called for four cameras per profile in one WASI instance. Physical208-byte parameter and512-byte matrix outputs per profile were checked word-for-word against genuine original D3DX return records. No original/current fixture is reexecuted by this verifier. No640 verdict, production engine screen execution, Renderer/GPU pixels, UI at960/1280, arbitrary camera inputs, all modes/resolutions or whole-game1:1 is inherited or established.')
    with OUT.open('x', encoding='utf-8', newline='\n') as output:
        json.dump(report, output, indent=2)
        output.write('\n')
    data = OUT.read_bytes()
    print(json.dumps(dict(path=OUT.relative_to(ROOT).as_posix(), bytes=len(data), sha256=sha(data),
                          comparisonPassed=passed, profiles=[dict(label=p['label'], parameterDifferences=p['parameterDifferenceCount'],
                                                                matrixDifferences=p['matrixDifferenceCount']) for p in profiles], bindings=len(BINDINGS))))


if __name__ == '__main__':
    main()
