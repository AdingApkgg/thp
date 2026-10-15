"""Stored-only audit of the TH14 continuous loader and ECL upload correction."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SHA = lambda data: hashlib.sha256(data).hexdigest()
bindings = {}


def read(name, expected=None):
    raw = (ROOT / name).read_bytes()
    digest = SHA(raw)
    assert expected is None or digest == expected, name
    bindings[name] = dict(bytes=len(raw), sha256=digest)
    return raw


def load(name):
    return json.loads(read(name))


def main():
    background = load('artifacts/th14/worker-background-decoded-stored-audit-oct15/receipt.json')
    assert background['storedOnlyVerified'] and background['comparedFullBytes'] == 1688960
    assert background['allByteEquality'] and background['differentBytes'] == 0
    read('artifacts/th14/worker-background-continuation-06-oct15/run/decoded-2.bin', background['sha256'])
    ecl = load('artifacts/th14/worker-timeline-ecl-stored-audit-oct15/receipt.json')
    assert ecl['comparedFullBytes'] == 21244 and ecl['differentBytes'] == 0
    read('artifacts/th14/worker-timeline-file-slot-observed-oct15/run/decoded-0.bin', ecl['sha256'])
    pump = load('artifacts/th14/background-main-pump-prepared-oct15/receipt.json')
    assert len(pump['helperReturns']) == 6
    assert [item['pending'] for item in pump['helperReturns']] == [2, 3, 4, 5, 6, 0]
    assert [item['value'] for item in pump['fileSyncStores']] == [2, 3, 4, 5, 6, 0]
    assert [item['pc'] for item in pump['fileSyncStores']] == ['0x47d2bd'] * 5 + ['0x47d402']
    assert len(pump['cpuTextureEvents']) == 30 and all(item['resultIsDeclaredModelInput'] for item in pump['cpuTextureEvents'])
    assert pump['cpuTextureResultsAreDeclared'] and not pump['physicalTextureOrImageEqualityVerified']
    assert not pump['workerResumed'] and not pump['originalMainFrameResumed']
    core = load('artifacts/th14/background-current-core-comparison-oct15/receipt.json')
    assert core['passed'] and core['comparedWords'] == 531 and core['differences'] == []
    assert (core['templates'], core['sprites'], core['chunks']) == (8, 7, 6)
    assert core['currentGameSourcesBound'] == 267 and core['currentObjectsBound'] == 141
    read('artifacts/th14/background-current-core-comparison-oct15/check.mjs', core['toolSha256'])
    read('artifacts/th14/background-current-core-comparison-oct15/check.wasm', core['wasmSha256'])
    native = load('artifacts/th14/worker-timeline-file-slot-observed-oct15/run/receipt.json')
    request = native['originalAnmLoadRequests']
    assert len(request) == 1 and (request[0]['pc'], request[0]['caller'], request[0]['fileId'], request[0]['name']) == (
        '0x47cff0', '0x42256a', 10, 'enemy.anm')
    assert native['worker']['stop']['requestNotServiced'] and native['originalCompletionFieldsAtStop'] == [0, 1]
    inputs = load('artifacts/th14/stage-timeline-native-queue-oct15/inputs.json')
    assert inputs['expectedAnmNames'] == ['enemy.anm', 'st02enm.anm']
    assert inputs['expectedFileIds'] == [10, 11] and inputs['fileId11DerivedFromOriginalLoopNotYetExecuted']
    assert [row['chunks'] for row in inputs['assets']] == [3, 16]
    queue = load('artifacts/th14/stage-timeline-native-queue-oct15/receipt.json')
    assert queue['passed'] and queue['results'][0]['resultWords'] == [36, 35, 16, 0]
    assert queue['results'][1]['resultWords'] == [0, 19, 0, 0]
    current_header = read('runtimes/th12/th12_web/cpp/sdl/StageUploadsTh14.hpp', queue['results'][1]['headerSha256'])
    assert b'next[count++]={&stage.enemies,9}' not in current_header
    unit = load('artifacts/th14/stage-timeline-anm-queue-check-oct15/receipt.json')
    assert unit['passed'] and unit['resultWords'] == [0, 43, 0, 7]
    read('tools/th14-stage-timeline-anm-queue-check-oct15.mjs', unit['toolSha256'])
    for name, digest in unit['sourceHashes'].items():
        read('runtimes/th12/th12_web/' + name, digest)
    build = load('artifacts/th14/stage-timeline-anm-sdl-build-oct15/build.json')
    assert build['compiled'] and build['exportsUnchanged'] and build['importsUnchanged']
    assert build['adjacentGraphicsTitlesCompiled'] == [13, 16]
    for name, digest in {**build['sourceHashes'], **build['headerHashes']}.items():
        read('runtimes/th12/' + name, digest)
    read('artifacts/th14/stage-timeline-anm-sdl-build-oct15/th11.wasm', build['wasmSha256'])
    report = dict(storedEvidenceVerified=True, productionTimelineDuplicateUploadRemoved=True,
        completeGame=False, nativeEquivalent=False, backgroundDecodedBytesCompared=1688960,
        backgroundDecodedByteDifferences=0, eclDecodedBytesCompared=21244, eclDecodedByteDifferences=0,
        declaredMainHelperPendingProgress=[1, 2, 3, 4, 5, 6, 0], backgroundTemplates=8,
        currentCoreComparedWords=531, currentCoreWordDifferences=0, currentCoreSourcesBound=267,
        currentCoreObjectsBound=141, exactRateAndRngInputs=core['nativeInputs'],
        observedFirstEclAnm=dict(fileId=10, name='enemy.anm', caller='0x42256a'),
        eclAnmNames=['enemy.anm', 'st02enm.anm'], derivedFileIds=[10, 11],
        secondFileIdDerivedNotYetExecuted=True, oldQueue=dict(chunks=35, legacyChunks=16, mismatches=36),
        correctedQueue=dict(chunks=19, legacyChunks=0, mismatches=0), queueAndTextureChecks=43,
        newSdlWasmBytes=build['wasmBytes'], newSdlWasmSha256=build['wasmSha256'],
        releaseImportsAndExportsUnchanged=True, adjacentGraphicsTitlesCompiled=[13, 16],
        precedingCpuTextureSuccessIsDeclared=True, actualGraphicsUploadVerified=False,
        originalOrdinaryMainFramesResumed=False, actualOsThreadCreated=False, actualAudioPlayed=False,
        completeResourceWorkerOrStageTransition=False, sourceHashes=unit['sourceHashes'],
        bindings=bindings, toolSha256=SHA(Path(__file__).read_bytes()),
        scope='Stored-only audit; no producer, compiler, emulator, GPU, audio or network execution. Original continuous resource code decoded background/ECL data and, under a declared CPU texture API model, six explicit main helpers initialized eight templates. Current production core matches 531 selected template/sprite/RNG words with the exact stored rate and RNG inputs; pointers are normalized only in the declared descriptor field. Original ECL loader actually requested ANIM[0] as file10; file11 follows its original10+i loop and has not yet been executed. Exact old/new SDL queues are compiled against the real ANIM names/chunk counts: removing the legacy duplicate reduces35 chunks to19. This is not actual GPU success, ordinary-frame async timing, full worker completion, complete browser later-stage playback, audio or whole-game equivalence.')
    path = ROOT / 'docs/porting/th14-stage-timeline-anm-queue-observed-oct15.json'
    with path.open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(report, stream, indent=2)
        stream.write('\n')
    print(json.dumps({key: report[key] for key in ['storedEvidenceVerified', 'currentCoreComparedWords',
        'currentCoreWordDifferences', 'oldQueue', 'correctedQueue', 'newSdlWasmSha256', 'completeGame']}))


if __name__ == '__main__':
    main()
