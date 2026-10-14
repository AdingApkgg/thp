"""Bind actual small browser save/reload/select/return observations after fix.

No browser automation, file export, frame measurement or Native/codec execution.
All console histories and the first TDZ failure remain in the evidence.
"""
import hashlib
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / 'artifacts/th14/browser-staged-capture-state-oct14'
DOC = ROOT / 'docs/porting/th14-staged-capture-browser-post-statefix-observed-oct14.json'
SHA = lambda data: hashlib.sha256(data).hexdigest()


def main():
    assert not DOC.exists(), 'Completed observation receipt remains immutable'
    bindings = {}
    def bind(path, expected=None, size=None):
        path = Path(path)
        if not path.is_absolute():
            path = ROOT / path
        path = path.resolve()
        assert path.is_relative_to(ROOT)
        key = path.relative_to(ROOT).as_posix()
        if key not in bindings:
            h = hashlib.sha256()
            with path.open('rb') as f:
                while chunk := f.read(4 * 1024 * 1024):
                    h.update(chunk)
            bindings[key] = dict(bytes=path.stat().st_size, sha256=h.hexdigest())
        row = bindings[key]
        if expected is not None:
            assert row['sha256'] == expected, key
        if size is not None:
            assert row['bytes'] == size, key
        return row
    def load(name, expected=None):
        bind(name, expected)
        return json.loads((ROOT / name).read_bytes())
    def event(rows, message, timestamp):
        matches = [row for row in rows if row['message'] == message and row['timestamp'] == timestamp]
        assert len(matches) == 1
        assert matches[0]['level'] == 'log' and matches[0]['url'] == 'http://localhost:8208/runtime/th14/th14-sdl.mjs'
        return matches[0]

    before = load('artifacts/th14/browser-staged-capture-state-oct14/before-reload-console.json')
    after = load('artifacts/th14/browser-staged-capture-state-oct14/after-playback-console.json')
    assert len(before) == 120 and len(after) == 160
    errors_before = [row for row in before if row['level'] == 'error']
    errors_after = [row for row in after if row['level'] == 'error']
    assert errors_before == errors_after and len(errors_after) == 1
    assert errors_after[0]['timestamp'] == '2026-10-14T10:38:43.373Z'
    assert "Cannot access 'state' before initialization" in errors_after[0]['message']
    first_failure = load('docs/porting/th14-staged-capture-browser-first-observed-oct14.json',
                         '3783503fb4c349b992d50d65680cc04fb86e694dc2dccb5139f0633cd13ae0cc')
    assert first_failure['retainedErrorRecords'] == errors_after
    assert not first_failure['wholeObservationPassedWithoutErrors']
    fixed_first = event(after, '[clock14] monotonic ticks=69; initial seed=69', '2026-10-14T10:54:22.847Z')
    fixed_boot = event(after, '[loading14] ascii script17 started; 9 resource uploads pending', '2026-10-14T10:54:22.985Z')
    ordinary_upload = event(before, '[loading14] stage entry; 6 resource uploads pending', '2026-10-14T11:02:39.227Z')
    ordinary_ready = event(before, '[loading14] resource uploads complete; interrupt1 delivered', '2026-10-14T11:02:39.297Z')
    reload_first = event(after, '[clock14] monotonic ticks=87; initial seed=87', '2026-10-14T11:06:12.736Z')
    reload_boot = event(after, '[loading14] ascii script17 started; 9 resource uploads pending', '2026-10-14T11:06:12.856Z')
    reload_ready = event(after, '[loading14] resource uploads complete; interrupt1 delivered', '2026-10-14T11:06:13.560Z')
    selected = event(after, '[replay] selected: record stage 1, character 0 subtype 0 difficulty 1, 1240 bytes', '2026-10-14T11:10:52.272Z')
    selected_upload = event(after, '[loading14] stage entry; 6 resource uploads pending', '2026-10-14T11:10:52.306Z')
    selected_ready = event(after, '[loading14] resource uploads complete; interrupt1 delivered', '2026-10-14T11:10:52.374Z')
    fixed_window = [row for row in after if row['timestamp'] >= fixed_first['timestamp']]
    assert all(row['level'] not in ('warn', 'warning', 'error') for row in fixed_window)
    screenshots = ['ordinary-entry.jpg', 'replay-save-result.jpg', 'replay-after-reload.jpg',
                   'replay-start.jpg', 'replay-progress.jpg', 'after-playback.jpg']
    for name in screenshots:
        path = ART / name
        bind(path)
        assert path.read_bytes()[:3] == bytes.fromhex('ffd8ff')
    for name in ['before-reload-ax.txt', 'after-playback-ax.txt']:
        path = ART / name
        bind(path)
        ax = path.read_text(encoding='utf-8')
        assert 'localhost:8208/index.html?game=th14' in ax and 'localhost:8208/runtime/th14/th14.html?hosted=1&managedData=1' in ax
        assert 'th14-workspace-quiet' in ax and '本机测试静音' in ax

    package_name = 'docs/porting/th14-launcher-preview-prepared-staged-capture-state-oct14.json'
    package = load(package_name, '2b9bd3371dae248ad566939538aa45dc5fbdfdf0e57742a761365a11e848438c')
    assert package['passed'] and package['buildId'] == '6e56b45514ba672ebc1c'
    assert Path(package['site']).parent.name == '64b46da7c4aa1af2-cc7135ef8ebe'
    runtime = load('docs/porting/th14-launcher-runtime-prepared-staged-capture-oct14.json', package['runtimeManifestSha256'])
    assert runtime['passed'] and len(runtime['files']) == 40 and len(package['files']) == 127
    site = Path(package['site'])
    for name, row in package['files'].items():
        bind(site / name, row['sha256'], row['bytes'])
    for name, row in runtime['files'].items():
        bind(Path(runtime['out']) / name, row['sha256'], row['bytes'])
    module = runtime['build']
    assert (module['sha256'], module['bytes']) == ('64b46da7c4aa1af2426d024c176e8c77b9ecae5a3da13a1eeea6c648ee82ca54', 1890810)
    bind(site / 'runtime/th14/th14-sdl.wasm', module['sha256'], module['bytes'])
    statefix = load('docs/porting/th14-launcher-state-initialization-verified-oct14.json')
    assert statefix['launcherStateInitializationVerified'] and not statefix['browserExecuted']
    assert statefix['actualSource']['sha256'] == 'e13bf9de16d886f5cf1a234e3caf869724823685b1d0a2e2aad05ffea026af91'
    bind(statefix['actualSource']['path'], statefix['actualSource']['sha256'])
    bind(statefix['clientSource']['path'], statefix['clientSource']['sha256'])
    bind('tools/th14-launcher-state-initialization-check.mjs', statefix['toolSha256'])
    fixed_host = package['moduleSources']['assets/launcher/app.mjs']
    bind(fixed_host['source'], fixed_host['sourceSha256'])
    bind(site / 'assets/launcher/app.mjs', fixed_host['sha256'])
    server_tool = bind('tools/th14-serve-workspace-current.mjs', '36accd68398804cb03803d2bc28d4f01d4d199633bba1536e32b6c33a5f07293')
    server_unit = load('docs/porting/th14-local-workspace-current-staged-capture-server-verified-oct14.json')
    assert server_unit['readOnlyVerified'] and not server_unit['browserExecuted']
    assert server_unit['toolSha256'] == server_tool['sha256']
    for name, digest in server_unit['frozenSources'].items():
        bind('tools/' + name, digest)

    observations = {
        'ordinary-entry.jpg': 'Visually inspected ordinary Reimu weapon selection with Normal mode; no gameplay frame is inferred from this menu image.',
        'replay-save-result.jpg': 'Visually inspected new slot01 A,26/10/14,ReimuA N St1 and displayed score7650; ROOT reports ordinary Game Start,natural death,Save Replay and nameA actions.',
        'replay-after-reload.jpg': 'After ROOT-reported complete reload/new boot,Replay list visibly contains slot01 A,26/10/14 19:04,ReimuA Normal St1,0.0%. This is visible metadata persistence,not exported byte identity.',
        'replay-start.jpg': 'Stage1 selection transition screenshot; no intermediate gameplay frame is present.',
        'replay-progress.jpg': 'Passive later observation visibly back at Replay list with slot01 A metadata; filename does not imply an intermediate gameplay screenshot.',
        'after-playback.jpg': 'Later screenshot and AX retain the Replay list/runtime child; ROOT reports no further gameplay input after the Stage1 confirmation.'
    }
    report = dict(postStatefixSmallBrowserObservationVerified=True, completeGame=False, nativeEquivalent=False, productionChanged=False,
                  originObserved='http://localhost:8208', frozenSiteBuildId=package['buildId'], frozenSite=package['site'],
                  serverSessionReportedByRoot=67107, serverToolSha256=server_tool['sha256'], serverBoundModuleSha256=module['sha256'],
                  serverBoundModuleBytes=module['bytes'], fixedParentSourceSha256=statefix['actualSource']['sha256'],
                  browserFetchedModuleDigestDirectlyObserved=False, sameOriginSaveAndReloadObserved=True,
                  savedVisibleMetadata=dict(slot=1, name='A', date='26/10/14', character='ReimuA', difficulty='Normal', stage=1, scoreShownAtSave=7650),
                  afterReloadVisibleMetadata=dict(slot=1, name='A', date='26/10/14', time='19:04', character='ReimuA', difficulty='Normal', stage=1, slowdownText='0.0%'),
                  ordinaryGameplayAndNaturalDeathDeclaredByRoot=True, allIntermediateActionsMechanicallyRecorded=False,
                  ordinaryStageUploads=dict(start=ordinary_upload, completion=ordinary_ready),
                  fullReloadDeclaredByRoot=True, freshBootAfterReload=dict(first=reload_first, pending=reload_boot, completion=reload_ready),
                  replaySelection=dict(stage=1, character=0, subtype=0, difficulty=1, runtimeReportedBytes=1240, selected=selected,
                                       pending=selected_upload, completion=selected_ready),
                  noFurtherGameplayInputAfterStageSelectionDeclaredByRoot=True, allInputEventsMechanicallyRecorded=False,
                  naturalReturnToReplayListObserved=True, intermediateGameplayFrameCaptured=False,
                  replayExported=False, replayByteSha256=None, replayFrameCount=None, rawByteIdentityVerified=False, nativeCodecVerified=False,
                  sameOriginVisibleReplayPersistenceAcrossOneReloadVerified=True, allIndexedDbPayloadsVerified=False,
                  scorePayloadPersistenceVerified=False, fullStorageFlowVerified=False, fullLongNextStageVerified=False,
                  actualSpeakerOutputMeasured=False, quietBadgeObserved=True, nativePixelsOrAudioEquivalent=False,
                  fixedRuntimeWindowStart=fixed_first['timestamp'], fixedRuntimeWindowLast=after[-1]['timestamp'],
                  fixedRuntimeWindowErrorCount=0, fixedRuntimeWindowWarningCount=0,
                  beforeConsoleRows=len(before), afterConsoleRows=len(after), beforeConsoleLevels=dict(Counter(row['level'] for row in before)),
                  afterConsoleLevels=dict(Counter(row['level'] for row in after)), retainedHistoricalErrorRecords=errors_after,
                  wholeConsoleSnapshotsAreErrorFree=False, firstTdzFailureReceiptStillFailed=True,
                  consoleSnapshots=dict(beforeReload=before, afterPlayback=after), screenshotVisualObservations=observations,
                  existingFrozenCoreCheckpointModified=False, priorBrowserFalsePromotedToWholeFlowPass=False,
                  bindings=bindings, bindingCount=len(bindings), toolSha256=SHA(Path(__file__).read_bytes()),
                  scope='Small actual ROOT CUA save/reload/select/return case after the host state-initialization fix. Images visually inspected and entire120/160 console snapshots retained,including the10:38:43.373 TDZ failure from the first package; first failure receipt stays immutable/failed. The later fixed runtime window has no observed errors/warnings. New slotA visible metadata remains after one full same-origin reload,and the runtime reports selection of1240-byte stage1 data with6 uploads completing,followed by a passively observed Replay-list return. ROOT declarations establish actions/no subsequent gameplay input; screenshots/logs do not mechanically record every action. No replay file was exported,no byte digest or frame count measured,and no intermediate gameplay frame captured. Current127-file package/40-file runtime,parent source,node unit/server code are bound; source association is to the server-bound64b46 module rather than a browser-measured module digest. Quiet badge is no loudspeaker/native audio measurement. No complete Native flow,long ordinary NextStage,all storage/IndexedDB payloads,score persistence,all modes,graphics/audio equality or whole-game1:1 is claimed. Core checkpoint/browserfalse and other docs remain unchanged.')
    DOC.write_bytes((json.dumps(report, indent=2) + '\n').encode())
    print(json.dumps(dict(report=str(DOC), sha256=SHA(DOC.read_bytes()), visibleReplayPersistence=True,
                         selectedRuntimeReportedBytes=1240, measuredFrames=None, byteHash=None,
                         wholeSnapshotHistoricalErrors=1, fixedWindowErrors=0, bindings=report['bindingCount'])))


if __name__ == '__main__':
    main()
