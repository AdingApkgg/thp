"""Verify one intact browser recording against its natural original playback.

This is one finite replay case using the declared private attract harness, not
ordinary original replay-menu acceptance or independent host timing acceptance.
Raw native state, timing, replay bytes and screenshots remain private.
"""
from pathlib import Path
import hashlib
import json
import struct
import subprocess
import sys
import time

R = Path(__file__).resolve().parents[1]
H = R / 'artifacts/th14/browser-recording-native-nov05'
D = H / 'natural'
N = D / 'native'
M = D / 'comparison'
SHA = lambda data: hashlib.sha256(data).hexdigest()


def main():
    assert not M.exists() and not (D / 'verified.json').exists()
    load = lambda path: json.loads(path.read_bytes())
    end = load(D / 'process-end.json')
    native = load(N / 'report.json')
    prep = load(H / 'observer/prepared.json')
    preflight = load(H / 'preflight/verified.json')
    assert preflight['verifiedNativePreflight']
    assert end['exitCode'] == 0 and end['guardStop'] is None
    assert native['childExited'] and not native['error'] and not native['debugErrors']
    assert native['observedForcedReplayEndMenu'] and not native['diagnosticPrefixOnly']
    assert native['sourceSha256'] == prep['observerSha256'] == preflight['observerSha256']
    assert SHA((N / 'observer-source.py').read_bytes()) == prep['observerSha256']
    assert native['configuredMusicAndSoundVolumeZero']
    assert native['gameStateWordWrites'] == 1 and native['rngOrCounterWrites'] == 0
    assert native['instructionBytesPatched'] == 0 and not native['inputInjected']
    assert native['caseInitialization']['attractBitClearOnly']
    assert native['pendingCrossThreadHardwareStatePreserved']
    assert native['unrecognizedExceptionPolicyUnchanged']
    assert not native['ordinaryMenuReplayInitialization']
    assert not native['scriptRngAccessWatchArmed']
    count = native['callbacks']
    assert count == 1293

    build = R / 'artifacts/th14/scene-camera-read-job-nov04/session-observer-v2/observer-build.json'
    driver = R / 'tools/th14-compare-native-scene-word-read-nov04.mjs'
    assert SHA(driver.read_bytes()) == '2ab9b608568fa6de14f1a5f3f495d94fd74c773e8f036c87d25cc9040b93d0c1'
    argv = ['C:/nvm4w/nodejs/node.exe', '--no-warnings', str(driver),
            '--native', str(N), '--assets',
            str(R / 'artifacts/th14/native-campaign-assets/57d84a5cbe82-ec04b9bea043'),
            '--build', str(build), '--output', str(M / 'model'),
            '--selection', '0,1,1,1', '--scheduler-phases', 'observed']
    M.mkdir()
    (M / 'argv.json').write_text(json.dumps(argv, indent=2) + '\n')
    started = time.monotonic()
    with (M / 'process.log').open('wb') as log:
        child = subprocess.run(argv, cwd=R, stdout=log, stderr=subprocess.STDOUT,
                               timeout=180, creationflags=subprocess.CREATE_NO_WINDOW)
    (M / 'process-end.json').write_text(json.dumps(dict(
        exitCode=child.returncode, elapsedSeconds=time.monotonic()-started,
        completeGame=False)) + '\n')
    assert child.returncode == 0, 'Retained full replay comparison failed'
    subprocess.run([sys.executable, '-X', 'utf8', str(R / 'tools/th14-verify-native-campaign.py'),
                    '--native', str(N), '--model', str(M / 'model'), '--build', str(build),
                    '--output', str(D / 'raw-verified.json')], cwd=R, check=True)

    model = M / 'model'
    camera = (N / 'world-camera.raw').read_bytes()
    tail = (N / 'world-camera-tail.u32').read_bytes()
    actual = (model / 'full-camera.u32').read_bytes()
    assert len(camera) == count*292 and len(tail) == count*8
    assert len(actual) == (count-1)*300
    for i in range(1, count):
        assert actual[(i-1)*300:i*300] == camera[i*292:(i+1)*292] + tail[i*8:(i+1)*8]
    cursor = (N / 'replay-cursor.u32').read_bytes()
    actual = (model / 'replay-cursor.u32').read_bytes()
    assert len(cursor) == count*56 and len(actual) == (count-1)*16
    for i in range(1, count):
        assert struct.unpack_from('<4I', actual, (i-1)*16) == tuple(
            struct.unpack_from('<I', cursor, i*56+j*4)[0] for j in [3, 7, 8, 9])

    browser = load(R / 'docs/porting/th14-browser-new-recording-nov05.json')
    assert native['sourceFullReplaySha256'] == browser['recording']['sha256']
    samples = native['terminalMenuSamples']
    assert len(samples) == 3
    fields = []
    for sample in samples:
        assert sample['callbacks'] == sample['controlFrame'] == count
        assert sample['pauseWords'] == [2, 3] and sample['disabledEntries'] == [3, 2, 0]
        assert sample['forcedExit'] == 1 and sample['cursor'] == 1 and sample['menuCount'] == 5
        economy, replay = sample['economyWords'], sample['replayCursorWords']
        assert len(economy) == 28 and len(replay) == 14
        assert economy[:2] == [0, 1] and economy[3] == 1 and economy[4] == 0
        assert sample['hudDisplayedScoreUnits'] == economy[2] == 424
        assert economy[15] == 0xffffffff and sample['lifeState'] == 2
        assert economy[14] == 100 and economy[17] < 49
        assert replay[2:4] == [1, 1] and replay[7:10] == [1293, 1293, 1294]
        points = economy[9] // 100
        signed_lives = struct.unpack('<i', struct.pack('<I', economy[15]))[0]
        visible = dict(displayedScore=sample['hudDisplayedScoreUnits']*10+economy[4],
                       lives=max(0, signed_lives), lifePieces=f'{economy[16]}/3',
                       bombs=economy[18], bombPieces=f'{economy[19]}/8',
                       power=f'{economy[12]//economy[14]}.{economy[12]%economy[14]*100//economy[14]:02}',
                       pointValue=points-points%10, graze=economy[6])
        assert visible == {key: browser['selectedVisibleTerminalFields'][key] for key in visible}
        fields.append(visible)
    assert fields[0] == fields[1] == fields[2]
    model_report = load(model / 'report.json')
    assert not model_report['diagnosticPrefixOnly']
    assert model_report['finalObservedCallbacks'] == count
    assert model_report['stableMenuAfter90Ticks'][0] == 2
    assert model_report['stableMenuAfter90Ticks'][5] == 3
    hud = load(model / 'hud-report.json')
    assert hud['terminalPortable'] == [424, 424]
    gate = load(D / 'raw-verified.json')
    result = dict(
        verifiedOneBrowserRecordingOriginalPlayback=True,
        intactBrowserReplay=True, replaySha256=browser['recording']['sha256'],
        declaredFrames=1294, callbacks=count, originalStableMenuSamples=len(samples),
        all32StateFieldsEqual=True, all75CameraWordsEqual=True,
        comparedCameraWords=(count-1)*75, all4CursorFieldsEqual=True,
        all2HudFieldsEqual=True, vm303Rows=gate['vm303Rows'],
        combatCheckpoints=gate['combatCheckpoints'], orderedPublications=gate['orderedPublications'],
        selectedVisibleTerminalFields=fields[0],
        originalInternalLifeCountMinusOne=True, originalLifeState=2,
        originalCursorAtMenu=1293, declaredRangeExhaustedAtMenu=False,
        actualDeclaredInputExhaustionBranchObserved=native['actualDeclaredInputExhaustionBranchObserved'],
        actualAllFfffMarkerBranchObserved=native['actualAllFfffMarkerBranchObserved'],
        originalObservedStableReplayEnd=True, modelStableMenuAfter90Ticks=True,
        quiet=True, nativeDebugExceptions=0, additionalGameplayMemoryWrites=0,
        privateAttractHarness=True, ordinaryOriginalGuiReplayMenuAccepted=False,
        observedHostClockScheduleSupplied=True, independentTimingAccepted=False,
        originalGpuPixelsOrPcmCompared=False, allModesAccepted=False,
        productionSourcesChanged=False, completeGame=False, nativeEquivalent=False,
        observerSha256=native['sourceSha256'], nativeReportSha256=SHA((N / 'report.json').read_bytes()),
        rawVerifierSha256=SHA((D / 'raw-verified.json').read_bytes()),
        toolSha256=SHA(Path(__file__).read_bytes()))
    (D / 'verified.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result))


if __name__ == '__main__':
    main()
