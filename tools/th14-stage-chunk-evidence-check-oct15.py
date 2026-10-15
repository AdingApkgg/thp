"""Audit stored worker/main-helper evidence and current SDL chunk correction.

Does not re-run the game, emulator, compiler, GPU, audio, or network requests.
"""
import hashlib
import importlib
import json
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SHA = lambda raw: hashlib.sha256(raw).hexdigest()
bindings = {}


def bind(name, expected=None):
    path = ROOT / name
    raw = path.read_bytes()
    digest = SHA(raw)
    assert expected is None or digest == expected, name
    bindings[name] = dict(bytes=len(raw), sha256=digest)
    return raw


def main():
    checkpoint = 'artifacts/th14/worker-anm-wait-checkpoint-oct15/run/checkpoint/'
    state = json.loads(bind(checkpoint + 'manifest.json', 'bb905088944f0bf3eeae1e7202b008516dc864362eadfc04f45400e48f60d975'))
    def memory(at, count):
        row = next(r for r in state['regions'] if r['base'] <= at and at + count <= r['base'] + r['bytes'])
        raw = bind(checkpoint + row['path'], row['sha256'])
        return raw[at - row['base']:at - row['base'] + count]
    sys.path.insert(0, str(ROOT / 'tools'))
    image = importlib.import_module('th12-pe').Image('H:/Games/th/14/th14.exe')
    assert SHA(image.data) == 'f08e885e28d2e0fc8c579e88034dd7de8f2a648d8f08ce781cf08eadc9ffe353'
    for low, high in [(0x47d230, 0x47d719), (0x47d720, 0x47d7a7), (0x4448cd, 0x4448dd)]:
        assert memory(low, high - low) == image.read(low, high - low)
    assert struct.unpack('<I', memory(0x0cfb9430 + 0x128, 4))[0] == 1
    prefix = 'artifacts/th14/anm-main-pump-cpu-textures-oct15/'
    plan = json.loads(bind(prefix + 'plan.json'))
    bind(prefix + 'slice.py', plan['sourceSha256'])
    bind('tools/th14-anm-cpu-texture-model-oct15.py', plan['cpuTextureModelSha256'])
    receipt = json.loads(bind(prefix + 'receipt.json'))
    assert receipt['checkpointManifestSha256'] == bindings[checkpoint + 'manifest.json']['sha256']
    assert receipt['planSha256'] == bindings[prefix + 'plan.json']['sha256']
    assert receipt['observations'] == 25281 and receipt['stopped']['kind'] == 'HELPER_RETURNED'
    assert [r['pending'] for r in receipt['helperReturns']] == [2, 0]
    assert all(r['returnedEax'] == 0x0cfb9430 and r['registers']['ESP'] == 0x6300ff08 for r in receipt['helperReturns'])
    assert receipt['fileSyncStores'] == [
        dict(pc='0x47d2bd', address='0xcfb9558', bytes=4, value=2),
        dict(pc='0x47d402', address='0xcfb9558', bytes=4, value=0)]
    templates = bind(prefix + 'templates.bin', receipt['templateSha256'])
    assert len(templates) == 7 * 0x5cc == receipt['templateBytes']
    events = receipt['cpuTextureEvents']
    assert len(events) == 10
    for chunk in range(2):
        group = events[chunk * 5:chunk * 5 + 5]
        assert [r['kind'] for r in group] == ['DECLARED_CPU_CREATE_TEXTURE', 'DECLARED_CPU_GET_SURFACE_LEVEL',
                'DECLARED_CPU_UPLOAD_REQUEST', 'DECLARED_CPU_SURFACE_RELEASE', 'DECLARED_CPU_GET_LEVEL_DESC']
        assert all(r['chunk'] == chunk and r['resultIsDeclaredModelInput'] and not r['actualDeviceInvoked'] for r in group)
        assert not group[2]['pixelsFiltered'] and not group[2]['pixelsUploaded']
    assert receipt['hostApiResultsSynthesized'] and receipt['cpuTextureResultsAreDeclared']
    assert not any(receipt[k] for k in ['originalMainFrameResumed', 'workerResumed', 'actualAudioPlayed',
                                      'completeGame', 'nativeEquivalent', 'physicalTextureOrImageEqualityVerified'])
    check = json.loads(bind('artifacts/th14/stage-chunk-upload-check-oct15/receipt.json'))
    assert check['passed'] and check['resultWords'] == [0, 41, 0, 8]
    bind('tools/th14-stage-chunk-upload-check-oct15.mjs', check['toolSha256'])
    build = json.loads(bind('artifacts/th14/stage-chunk-sdl-build-oct15/build.json'))
    assert build['compiled'] and build['releaseProfile'] and build['adjacentGraphicsTitlesCompiled'] == [13, 16]
    assert build['importsUnchanged'] and build['exportsUnchanged'] and not build['runtimeExecuted']
    bind('artifacts/th14/stage-chunk-sdl-build-oct15/th11.wasm', build['wasmSha256'])
    bind('artifacts/th14/stage-chunk-sdl-build-oct15/th11.mjs', build['loaderSha256'])
    for name, digest in check['sourceHashes'].items():
        bind('runtimes/th12/th12_web/' + name, digest)
    for name, digest in {**build['sourceHashes'], **build['headerHashes']}.items():
        bind('runtimes/th12/' + name, digest)
    report = dict(storedEvidenceVerified=True, productionChunkQueueCorrected=True, completeGame=False,
                  nativeEquivalent=False, originalMainHelperObservations=receipt['observations'],
                  originalPendingProgress=[1, 2, 0], originalPendingStorePCs=['0x47d2bd', '0x47d402'],
                  originalHelperCodeMatchesExecutable=True, mainFrameOrWorkerResumed=False,
                  cpuTextureSuccessExplicitlyDeclared=True, actualGraphicsUploadVerified=False,
                  templatesInitialized=7, rawTemplateBytes=len(templates), rawTemplateSha256=SHA(templates),
                  queueAndTextureChecks=41, failures=0, adjacentGraphicsTitlesCompiled=[13, 16],
                  newSdlWasmBytes=build['wasmBytes'], newSdlWasmSha256=build['wasmSha256'],
                  releaseImportsAndExportsUnchanged=True, browserRenderingVerified=False,
                  actualAudioPlayed=False, sourceHashes=check['sourceHashes'], bindings=bindings,
                  toolSha256=SHA(Path(__file__).read_bytes()),
                  scope='Stored proof only. Two explicitly called original main helpers use saved main CPU/FS and a declared CPU texture API model; these are not ordinary main frames or physical D3D success. Native original code writes progress 1->2->0 and initializes seven templates. Production later-stage SDL queue now prepares one chunk per tick and retains resource ownership until its final chunk. Boot/core uploads remain unchanged. Real texture conversion with recording upload backend passes 41 checks; the release build and adjacent TH13/TH16 graphics branches compile. Browser rendering, matching Native async timing, visual RNG, audio and whole-game equivalence remain separate.')
    path = ROOT / 'docs/porting/th14-stage-chunk-upload-observed-oct15.json'
    with path.open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(report, stream, indent=2)
        stream.write('\n')
    print(json.dumps({k: report[k] for k in ['storedEvidenceVerified', 'originalPendingProgress',
                    'queueAndTextureChecks', 'failures', 'newSdlWasmSha256', 'completeGame']}))


if __name__ == '__main__':
    main()
