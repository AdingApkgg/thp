"""Verify actual Application viewport rounding against independent D3D9.

Every color byte is retained. Native component controls do not accept a browser
or an ordinary original Application, and backend differences remain failures.
"""
from pathlib import Path
import argparse
import hashlib
import json

ROOT = Path(__file__).resolve().parents[1]
SHA = lambda raw: hashlib.sha256(raw).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--home', type=Path, default=ROOT/'artifacts/th14/application-render-trace-oct27')
    parser.add_argument('--output', type=Path, default=ROOT/'docs/porting/th14-viewport-rounding-verified-oct27.json')
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args(); home = args.home.resolve(); bindings = {}
    assert home.is_relative_to(ROOT/'artifacts/th14')
    def read(path):
        raw = path.read_bytes()
        bindings[path.relative_to(ROOT).as_posix()] = dict(bytes=len(raw), sha256=SHA(raw))
        return raw
    def load(path): return json.loads(read(path))
    def different(a, b):
        assert len(a) == len(b)
        indexes = [i for i, (x, y) in enumerate(zip(a, b)) if x != y]
        return dict(bytes=len(indexes), pixels=len({i//4 for i in indexes}))
    for name in ['Shaders.hpp', 'Th14WebGpu.wgsl']:
        read(ROOT/'runtimes/th12/portable/sdl'/name)
    for name in ['th14-prepare-application-trace-oct27.py', 'th14-application-trace-hal-oct27.py',
                 'th14-native-webgpu-context.py', 'th14-build-native-application.py', 'th14-native-application.py',
                 'th14-application-render-pair-check.py']:
        read(ROOT/'tools'/name)
    trace = load(home/'webgpu-v2/render-trace.json')
    assert trace['frame'] == 2264 and trace['semanticInputsObservedBeforeBackend'] and not trace['nativeValuesProvidedToEngine']
    assert trace['initialDepthContentsNotCaptured'] and len(trace['events']) == 1249
    blobs = {}
    def check_blob(row):
        if row['sha256'] in blobs: assert row == blobs[row['sha256']]; return
        path = (home/'webgpu-v2'/row['file']).resolve(); assert path.is_relative_to(home/'webgpu-v2')
        raw = path.read_bytes(); assert len(raw) == row['bytes'] and SHA(raw) == row['sha256']
        blobs[row['sha256']] = row
    for row in trace['initial']['resources']: check_blob(row['pixels'])
    for row in trace['events']:
        if 'blob' in row: check_blob(row['blob'])
    assert sum(row['bytes'] for row in blobs.values()) == trace['uniqueBlobBytes'] == 47336648
    old_gpu = read(home/'webgpu-v2/demo-1-ready.bgra')
    assert old_gpu == read(ROOT/'artifacts/th14/application-attract-oct27/webgpu-after-storage/demo-1-ready.bgra')
    native = read(home/'hal-second/frame.bgra'); assert len(native) == 640*480*4
    for folder in ['hal-second', 'hal-probes', 'hal-process-vertices', 'hal-float-sources', 'hal-uv-unfogged', 'production-viewport-final']:
        report = load(home/folder/'report.json')
        assert report['completed'] and not report['error'] and report['actualHalDraws'] == 416 and report['actualClears'] == 7
        assert report['toolSha256'] == SHA(read(home/folder/'run-tool.py'))
        assert report['frameSha256'] == SHA(native) and read(home/folder/'frame.bgra') == native
        assert report['initialColorContentsFromObservedGpu'] and report['unknownInitialDepthNeverUsed']
        assert not report['originalProcessLaunched'] and not report['browserAcceptance'] and not report['nativeEquivalent']
    before = load(home/'hal-probes/first-target-9-state.json')
    assert before['step']['completedDraws'] == 192 and before['step']['differentBytes'] == 51 and before['step']['beforeBuffersEqual']
    assert read(home/'hal-probes/first-target-9-before-native.bgra') == read(home/'hal-probes/first-target-9-before-webgpu.bgra')
    critical = load(home/'hal-probes/first-critical-9-state.json')
    assert critical['step']['completedDraws'] == 230 and critical['stateWords'][3] == before['stateWords'][3] == 97
    assert next(r for r in trace['events'] if r['kind'] == 4 and r['words'][0] == 97)['words'][3] == 1  # BGRA8
    for folder, kind in [('hal-float-sources', 'source'), ('hal-uv-unfogged', 'uv')]:
        rows = load(home/folder/'float-sources.json'); assert [r['draw'] for r in rows] == [192,230]
        for row in rows:
            for backend in ['native', 'webgpu']:
                raw = read(home/folder/f"draw-{row['draw']}-{kind}-{backend}.rgba32f")
                assert len(raw) == 640*480*16 and SHA(raw) == row[backend+'Sha256']
            assert row['probes'][0 if row['draw'] == 192 else 1]['native'] != row['probes'][0 if row['draw'] == 192 else 1]['webgpu']
    current_gpu = read(home/'production-viewport-final/webgpu-frame.bgra')
    assert current_gpu == native and different(old_gpu,native) == dict(bytes=15,pixels=15)
    gate = load(home/'production-viewport-final/draw-comparisons.json')
    assert gate['shaderVariant'] == 'baseline' and gate['nativeDifferentBytes'] == gate['nativeDifferentPixels'] == 0
    assert not gate['webgpuReplayBaselineExact']  # The repaired image must change.
    for name in ['Th14WebGpu.wgsl','Th14WebGpuResample.wgsl']:
        assert read(home/'production-viewport-final/frozen-host'/name) == read(ROOT/'runtimes/th12/portable/sdl'/name)
    assert read(home/'production-viewport-final/frozen-host/context.py') == read(ROOT/'tools/th14-native-webgpu-context.py')
    stage = load(home/'stage-final/report.json'); build = load(home/'stage-build/build.json')
    assert stage['actualCppRenderer'] and stage['actualEmscriptenAsyncify'] and stage['actualJavascriptWebgpuHost']
    assert stage['frames'] == stage['exactFrames'] == 21 and stage['differentBytes'] == 0
    for path,row in build['sourceBindings'].items(): assert SHA(read(ROOT/path)) == row['sha256']
    assert SHA(read(home/'stage-build/component.wasm')) == build['wasmSha256'] == stage['wasmSha256']
    assert SHA(read(home/'stage-build/build.json')) == stage['buildSha256']
    reference = ROOT/'artifacts/th14/stage-gpu-stream-replay'
    original = read(reference/'native.bgra'); original_report = load(reference/'native.json')
    assert SHA(original) == original_report['pixelsSha256'] == stage['nativePixelsSha256']
    for row, expected in zip(stage['rows'],original_report['frames']):
        assert (row['stage'],row['frame']) == (expected['stage'],expected['frame'])
        raw = read(home/f"stage-final/stage{row['stage']}-frame{row['frame']}.bgra")
        assert raw == original[expected['offset']:expected['offset']+expected['bytes']]
    gles_stage = load(home/'stage-gles-final/comparison.json')
    assert gles_stage['frames'] == 21 and gles_stage['exactFrames'] == 20 and gles_stage['differentChannels'] == 1
    gles_stage_differences = []
    for row, expected in zip(gles_stage['rows'],original_report['frames']):
        raw = read(home/f"stage-gles-final/stage{row['stage']}-frame{row['frame']}.bgra")
        changes = different(raw,original[expected['offset']:expected['offset']+expected['bytes']])
        if changes['bytes']: gles_stage_differences.append(dict(stage=row['stage'],frame=row['frame'],**changes))
    assert gles_stage_differences == [dict(stage=3,frame=1199,bytes=1,pixels=1)]
    runs = {}
    for backend in ['gles','webgpu']:
        runs[backend] = run = load(home/f'current-flow-{backend}/report.json')
        build = load(home/f'current-build-{backend}/build.json')
        assert run['completed'] and not run['error'] and run['frames'] == 17545 and len(run['checks']) == 30
        assert len(run['actions']) == 13 and run['backend'] == build['backend'] == backend
        assert run['buildReportSha256'] == SHA(read(home/f'current-build-{backend}/build.json'))
        assert run['wasmSha256'] == build['wasmSha256'] == SHA(read(home/f'current-build-{backend}/application.wasm'))
        for path,row in build['sourceBindings'].items(): assert SHA(read(ROOT/path)) == row['sha256']
        assert run['actualProductionApplicationAndDevices'] and run['physicalAudioDevicesOpened'] == 0
    pair = load(home/'current-flow-pair.json')
    assert pair['completedRuns'] == ['gles','webgpu'] and pair['framesPerBackend'] == 17545
    assert pair['pairedImages'] == 7 and pair['assertionsPerBackend'] == 30 and pair['pairedJournalRows'] == 4243
    assert pair['allSharedActionStatesEqual'] and not pair['stateDifferences']
    assert pair['verifierSha256'] == SHA(read(ROOT/'tools/th14-application-render-pair-check.py'))
    journal = pair['journalComparison']; assert not journal['allRowsEqual'] and journal['rowCounts'] == dict(webgpu=4243,gles=4239)
    first = journal['firstIndexedDifference']; assert first['index'] == 2707
    assert first['webgpu']['frame'] == 11210 and first['gles']['frame'] == 11211
    assert runs['gles']['pcmFrames'] == runs['webgpu']['pcmFrames'] == 12681216
    assert runs['gles']['pcmSha256'] != runs['webgpu']['pcmSha256']
    assert pair['silentPcmSinkComparison']['reportedHashes'] == {k:runs[k]['pcmSha256']for k in ['webgpu','gles']}
    regression = load(home/'pair-positive-regression.json')
    assert regression['verifierSha256'] == pair['verifierSha256']
    assert regression['framesPerBackend'] == 123412 and regression['pairedImages'] == 8
    assert regression['allPairedCapturedBuffersEqual'] and regression['journalComparison']['allRowsEqual']
    assert regression['silentPcmSinkComparison']['reportedHashEqual']
    for row in runs['webgpu']['captures']:
        path=home/'current-flow-webgpu'/row['file']; assert SHA(read(path)) == row['sha256']
        if row['label'] == 'demo-1-ready': assert read(path) == native
    gles_image = read(home/'current-flow-gles/demo-1-ready.bgra')
    assert different(gles_image,native) == dict(bytes=10,pixels=8)
    compressed = load(home/'compression-verified.json')
    assert compressed['files'] == 225 and compressed['logicalBytes'] == 351879168
    assert compressed['allocatedBefore'] == 351879168 and compressed['allocatedAfter'] == 134782976
    assert compressed['allContentsPathsSizesMtimesUnchanged'] and compressed['noDeletion'] and compressed['onlyTerminalOwnBuffers']
    for row in compressed['rows']:
        path=Path(row['path']).resolve(strict=True);assert path.is_relative_to(home)
        assert path.stat().st_size == row['bytes'] and path.stat().st_mtime_ns == row['mtimeNs']
        assert SHA(path.read_bytes()) == row['sha256']
    result = dict(verifiedActualViewportRepair=True, traceFrame=2264, traceEvents=1249, traceBlobBytes=47336648,
        nativeActualDraws=416, nativeClears=7, actualFrameBytes=1228800, nativeReferenceUsesObservedInitialColor=True,
        firstBackendDifferenceDraw=192, firstOriginalDisputedPixelDraw=230, sourceTextureFormat='BGRA8',
        originalWebgpuVsNative=different(old_gpu,native), currentWebgpuVsNative=different(current_gpu,native),
        currentGlesVsNative=different(gles_image,native), currentStageFrames=21, currentStageComparedBytes=25804800,
        currentGlesStageExactFrames=20, currentGlesStageDifferences=gles_stage_differences,
        fullAttractFramesPerBackend=17545, assertionsPerBackend=30, journalRowsPerBackend=journal['rowCounts'], actionsPerBackend=13,
        currentFullFlowAccepted=False, journalAllRowsEqual=False,firstJournalIndexedDifference=first,
        updatedPairCheckerPositiveRegressionImages=8, updatedPairCheckerKeepsPixelStateAndPcmFailureGates=True,
        pairedImages=7, pairedImageEqualityPassed=pair['allPairedCapturedBuffersEqual'],
        compressedTerminalOwnBuffers=225, compressedLogicalBytes=351879168,compressedAllocatedBytes=134782976,
        compressionContentsPathsSizesMtimesUnchanged=True,
        imageDifferences=pair['pairs'], pcmFramesPerBackend=12681216, silentPcmSinkHashesEqual=False,
        silentPcmHashes=pair['silentPcmSinkComparison']['reportedHashes'],
        productionGraphicsChanged=True, productionGameplayChanged=False, physicalAudioDevicesOpened=0,
        browserAcceptance=False, originalOrdinaryApplicationAccepted=False, completeGame=False,nativeEquivalent=False,
        verifierSha256=SHA(Path(__file__).read_bytes()), bindings=bindings,
        limitations=['Independent D3D9 replay uses observed C++ semantic inputs and initial GPU colors; not an ordinary original whole-Application capture.',
            'Default GLES retains 8 pixels/10 color bytes in this actual image; no channel exclusion or tolerance.',
            'Both current flows complete 17545 frames/30 assertions but journal states and PCM hashes diverge in the second demo; full regression fails and no cause is assumed.',
            'ProcessVertices and native-only vertex storage observations are diagnostic controls, not browser acceptance.',
            'Incompatible ps_3_0/fixed-function probes, a rejected ps_2_0 assembly and fogged UV observations are preserved and excluded from UV conclusions.',
            'Mode coverage, camera/effect149, ordinary original workflows, browser storage/input/audio and other remaining acceptance items stay open.'])
    output=args.output.resolve();assert output.is_relative_to(ROOT/'docs/porting')or output.is_relative_to(ROOT/'artifacts/th14')
    if args.check: assert json.loads(output.read_bytes()) == result
    else: output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:result[k]for k in ['verifiedActualViewportRepair','originalWebgpuVsNative','currentWebgpuVsNative','currentGlesVsNative','currentStageFrames','pairedImageEqualityPassed']}))


if __name__ == '__main__': main()
