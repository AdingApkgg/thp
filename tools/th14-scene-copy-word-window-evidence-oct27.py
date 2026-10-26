"""Verify every directly observed REP iteration in one bounded Stage4 window.

Actual copied words remain evidence only; they are never model inputs.
"""
from pathlib import Path
import argparse
import hashlib
import json
import struct

ROOT = Path(__file__).resolve().parents[1]
SHA = lambda raw: hashlib.sha256(raw).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--home', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--check', action='store_true')
    parser.add_argument('--budget-stop-diagnostic', action='store_true', help='Verify retained observations from a failed capacity-stopped capture; never report the planned run as completed')
    args = parser.parse_args()
    home = args.home.resolve()
    assert home.is_relative_to(ROOT / 'artifacts/th14')
    bindings = {}

    def read(path):
        raw = path.read_bytes()
        bindings[path.relative_to(ROOT).as_posix()] = dict(bytes=len(raw), sha256=SHA(raw))
        return raw

    def load(path):
        return json.loads(read(path))

    def lines(path):
        return [json.loads(line) for line in read(path).splitlines() if line]

    plan = load(home / 'plan.json')
    native = (ROOT / plan['output']).resolve()
    build = (ROOT / plan['observer']).parent
    assert native.is_relative_to(ROOT / 'artifacts/th14') and build.is_relative_to(ROOT / 'artifacts/th14')
    prepared = load(build / 'prepared.json')
    report = load(native / 'report.json')
    planned_count = plan['maximumCallbacks']
    count = report['callbacks']
    assert planned_count == 52000 and plan['maximumWallSeconds'] == 1200
    assert plan['minimumFreeGiB'] == 100 and plan['maximumCaptureGiB'] == 0.125
    assert plan['freeGiBBefore'] - plan['maximumCaptureGiB'] >= 100.1
    assert not plan['automaticNextCase'] and plan['originalCopyTrapFlagStepping']
    assert report['childExited'] and not report['debugErrors']
    if args.budget_stop_diagnostic:
        assert 0 < count < planned_count and report['diagnosticStopReason'] == 'errorOrBudget'
        assert report['error'] == "RuntimeError('TH14 capture storage budget exceeded; preserve disk reserve and retained observations')"
        limit = load(native / 'storage-limit.json')
        assert limit['storageBudgetExceeded'] and limit['minimumFreeBytes'] == 100 * 1024**3
        assert limit['maximumCaseBytes'] == 128 * 1024**2 and not limit['originalGameInputsOrCodeChanged']
        assert limit['freeBytes'] < limit['minimumFreeBytes'] or limit['caseObservationBytes'] > limit['maximumCaseBytes']
    else:
        assert count == planned_count and not report['error'] and report['diagnosticStopReason'] == 'maximumCallbacks'
    assert report['callbacks'] == count and report['diagnosticPrefixOnly'] and not report['fullReplayAccepted']
    assert report['observerTerminationRequested']
    opts = report['observerOptions']
    assert [opts['character'], opts['subtype'], opts['difficulty']] == plan['selection'] == [2, 1, 0]
    assert opts['maximum_callbacks'] == planned_count and opts['max_seconds'] == plan['maximumWallSeconds']
    assert opts['minimum_free_gib'] == plan['minimumFreeGiB'] and opts['maximum_capture_gib'] == plan['maximumCaptureGiB']
    assert opts['scene_copy_word_events'] and opts['scene_camera_events'] and opts['controller_phase_events']
    assert [int(x) for x in opts['live_callbacks'].split(',')] == plan['declaredLiveCallbacks']
    assert report['instructionBytesPatched'] == report['rngOrCounterWrites'] == 0 and not report['inputInjected']
    assert report['gameStateWordWrites'] == 1 and report['caseInitialization']['attractBitClearOnly']
    assert report['hardwareDebugRegistersAndTrapFlagOnly'] and not report['ordinaryMenuReplayInitialization']
    assert report['configuredMusicAndSoundVolumeZero'] and not report['actualAudioPcmMeasured']
    assert not report['observedForcedReplayEndMenu']
    assert report['sourceFullReplaySha256'] == plan['intactReplaySha256'] == 'e98fc11baae2d58c9cdaee6a5f8f94e0504340eba6685c7187550168a415624f'
    frozen = read(native / 'observer-source.py')
    assert SHA(frozen) == report['sourceSha256'] == prepared['generatedObserverSha256'] == plan['observerSha256']
    assert frozen == read(build / 'observer.py')
    assert prepared['baseObserverSha256'] == SHA(read(ROOT / prepared['baseObserverPath']))
    assert prepared['preparerSha256'] == SHA(read(ROOT / 'tools/th14-prepare-scene-copy-word-observer-oct26.py'))
    assert report['storageHelperSha256'] == plan['storageHelperSha256'] == SHA(read(ROOT / 'tools/th14-test-storage.py'))
    assert report['executableSha256'] == 'f08e885e28d2e0fc8c579e88034dd7de8f2a648d8f08ce781cf08eadc9ffe353'
    camera = read(native / 'world-camera.raw')
    selected = read(native / 'selected-state.u32')
    assert len(camera) == count * 0x124 and SHA(camera) == report['worldCameraSha256']
    assert len(selected) == count * 128 and SHA(selected) == report['selectedSha256']
    stages = sorted({struct.unpack_from('<I', selected, index * 128 + 120)[0] for index in range(count)})
    assert stages == [1, 2, 3, 4]
    modules = load(native / 'scene-copy-modules.json')
    assert modules == report['sceneCopyWordModules'] and len(modules) == 1
    assert modules[0]['name'] == 'd3dx9_43.dll' and modules[0]['sha256'] == '0b28546be22c71834501f7d7185ede5d79742457331c7ee09efc14490dd64f5f'
    copies = lines(native / 'scene-camera-copy-events.jsonl')
    steps = lines(native / 'scene-camera-copy-step-events.jsonl')
    words = lines(native / 'scene-camera-word-copy-events.jsonl')
    assert SHA(read(native / 'scene-camera-word-copy-events.jsonl')) == report['sceneCopyWordEventsSha256']
    assert len(words) == report['sceneCopyWordEvents'] == 9 and report['sceneCopyWordObserversRemaining'] == 0
    assert len(copies) == 6 and len(steps) == 234
    observations = []
    for case, stage in enumerate([2, 3, 4]):
        before, after = copies[case * 2:case * 2 + 2]
        segment = steps[case * 78:case * 78 + 78]
        lanes = words[case * 3:case * 3 + 3]
        assert before['event'] == 'scene-camera-copy-before' and after['event'] == 'scene-camera-copy-after'
        assert before['stage'] == after['stage'] == stage and before['scene'] == after['scene']
        assert before['pc'] == 0x40d435 and after['pc'] == 0x40d447 and before['threadId'] == after['threadId']
        assert after['threeDestinationWordsObservedDirectly'] and after['originalRepCopiedWords'] == 75
        assert after['originalCopyStepEvents'] == len(segment) == 78
        times = [before['hostMonotonicNs'], *[row['hostMonotonicNs'] for row in segment], after['hostMonotonicNs']]
        assert all(a <= b for a, b in zip(times, times[1:]))
        assert [row['workerPc'] for row in segment[:3]] == [0x40d43a, 0x40d43f, 0x40d445]
        assert [row['workerPc'] for row in segment[3:]] == [0x40d445] * 74 + [0x40d447]
        for index, row in enumerate(segment):
            dr = row['debugRegisters']
            regs = row['workerRegisters']
            assert row['readOnly'] and row['threadId'] == before['threadId'] and row['scene'] == before['scene']
            assert dr['dr6'] & 0x4000 and (dr['dr7'] & ~0x400) == 0x0ddd0055
            assert [dr['dr0'], dr['dr1'], dr['dr2'], dr['dr3']] == [before['scene'] + 0x42a4 + 4 * lane for lane in range(3)] + [0x40d447]
            if index >= 2:
                copied = index - 2
                assert regs['ecx'] == 75 - copied and regs['esi'] == 0x4d9514 + 4 * copied
                assert regs['edi'] == before['scene'] + 0x4274 + 4 * copied
                assert row['previousCopiedWords'] == max(0, copied - 1)
        assert [row['word'] for row in lanes] == [0, 1, 2]
        for lane, row in enumerate(lanes):
            step = segment[15 + lane]
            assert row['workerRegisters'] == step['workerRegisters'] and row['debugRegisters'] == step['debugRegisters']
            assert row['mainThreadRegisters'] == step['mainThreadRegisters']
            assert row['exactTrapFlagStep'] and row['actualOriginalRepIterationObserved'] and row['readOnly']
            assert not row['nativeValuesProvidedToEngine'] and row['stage'] == stage
            assert row['copiedWordHex'] == after['copiedRightHex'][lane * 8:lane * 8 + 8]
            assert before['hostMonotonicNs'] < row['hostMonotonicNs'] < after['hostMonotonicNs']
            module = row['mainModule']
            if module is not None:
                assert module == modules[0] and row['mainModuleRva'] == row['mainThreadRegisters']['eip'] - module['base']
        observations.append(dict(stage=stage, precedingPlayerCallbacks=before['precedingPlayerCallbacks'],
            stoppedMainPcs=[row['mainThreadRegisters']['eip'] for row in lanes],
            lastCameraBoundaryEvents=[row['lastMainCameraBoundary']['event'] if row['lastMainCameraBoundary'] else None for row in lanes],
            exactOriginalRepIterations=75, rightWordsObserved=3))
    result = dict(verifiedFiniteOriginalSceneCopyObservation=True, diagnosticPrefixOnly=True, callbacks=count, stagesObserved=stages,
        plannedMaximumCallbacks=planned_count, captureReachedDeclaredMaximum=count == planned_count,
        originalCaptureSucceeded=not bool(report['error']), captureBudgetStopped=bool(args.budget_stop_diagnostic),
        originalCaptureTerminalErrorRetained=report['error'],
        sceneCopiesObserved=3, exactCopyStepEvents=234, actualOriginalRepIterations=225, actualRightWordObservations=9,
        observations=observations, originalInstructionsUnmodified=True, configuredSilent=True, physicalPcmMeasured=False,
        debuggerPausesAffectTiming=True, mainThreadPcIsStoppedObservationNotSimultaneousCopyTimestamp=True,
        oldCameraFailureClosed=False, nativeValuesProvidedToEngine=False, automaticNextCase=False,
        originalOrdinaryMenuEquivalence=False, browserAcceptance=False, completeGame=False, nativeEquivalent=False,
        observerSha256=report['sourceSha256'], verifierSha256=SHA(Path(__file__).read_bytes()), bindings=bindings,
        scope='Retained terminal diagnostic window throughStage4, bounded by a52000-callback maximum. The actual callback count and any capacity failure remain explicit; a failed capture is not reclassified as a completed run. Every retained original REP iteration and copied right word is checked directly. MainPC is sampled after debugging stops threads; no simultaneous-read-time or old-schedule claim. No campaign/UI/GPU/audio/browser acceptance.')
    output = args.output.resolve()
    assert output.is_relative_to(ROOT / 'artifacts/th14') or output.is_relative_to(ROOT / 'docs/porting')
    if args.check:
        assert json.loads(output.read_bytes()) == result
    else:
        output.write_text(json.dumps(result, indent=2) + '\n', encoding='utf8')
    print(json.dumps({key: result[key] for key in ['verifiedFiniteOriginalSceneCopyObservation', 'callbacks', 'actualOriginalRepIterations', 'actualRightWordObservations', 'oldCameraFailureClosed']}))


if __name__ == '__main__':
    main()
