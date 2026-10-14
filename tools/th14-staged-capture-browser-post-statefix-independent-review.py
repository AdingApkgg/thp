"""Read-only custody and scope review of the small post-fix browser case.

No browser, database, Native, compiler or network execution is performed.
The original observation report and all its inputs remain unchanged.
"""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / 'docs/porting/th14-staged-capture-browser-post-statefix-observed-oct14.json'
OUT = ROOT / 'artifacts/th14/browser-staged-capture-state-oct14/post-statefix-independent-review.json'
EXPECTED = 'fe5d60b007b2b2c9518ab9cef33deaee58307d66c05a5955f7c0890a0d4f6b63'


def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        while chunk := stream.read(4 * 1024 * 1024):
            h.update(chunk)
    return h.hexdigest()


def main():
    assert not OUT.exists(), 'Completed review receipt remains immutable'
    assert digest(REPORT) == EXPECTED
    report = json.loads(REPORT.read_bytes())
    assert report['bindingCount'] == len(report['bindings']) == 191
    for name, binding in report['bindings'].items():
        path = (ROOT / name).resolve()
        assert path.is_relative_to(ROOT)
        assert path.stat().st_size == binding['bytes'], name
        assert digest(path) == binding['sha256'], name
    observation_tool = ROOT / 'tools/th14-staged-capture-browser-post-statefix-check.py'
    assert digest(observation_tool) == report['toolSha256']
    for name, key in [('before-reload-console.json', 'beforeReload'),
                      ('after-playback-console.json', 'afterPlayback')]:
        actual = json.loads((OUT.parent / name).read_bytes())
        assert actual == report['consoleSnapshots'][key]
    before = report['consoleSnapshots']['beforeReload']
    after = report['consoleSnapshots']['afterPlayback']
    assert (len(before), len(after)) == (120, 160)
    errors = [row for row in after if row['level'] == 'error']
    assert errors == [row for row in before if row['level'] == 'error']
    assert errors == report['retainedHistoricalErrorRecords'] and len(errors) == 1
    assert errors[0]['timestamp'] == '2026-10-14T10:38:43.373Z'
    assert "Cannot access 'state' before initialization" in errors[0]['message']
    fixed_rows = [row for row in after if row['timestamp'] >= report['fixedRuntimeWindowStart']]
    assert not [row for row in fixed_rows if row['level'] in ('error', 'warn', 'warning')]
    assert not report['wholeConsoleSnapshotsAreErrorFree']
    assert report['firstTdzFailureReceiptStillFailed']
    assert report['sameOriginVisibleReplayPersistenceAcrossOneReloadVerified']
    assert report['sameOriginSaveAndReloadObserved'] and report['fullReloadDeclaredByRoot']
    assert report['originObserved'] == 'http://localhost:8208'
    assert report['savedVisibleMetadata']['name'] == report['afterReloadVisibleMetadata']['name'] == 'A'
    assert report['savedVisibleMetadata']['slot'] == report['afterReloadVisibleMetadata']['slot'] == 1
    assert report['afterReloadVisibleMetadata']['time'] == '19:04'
    assert report['replaySelection']['runtimeReportedBytes'] == 1240
    assert report['replaySelection']['selected']['timestamp'] == '2026-10-14T11:10:52.272Z'
    assert report['replaySelection']['completion']['timestamp'] == '2026-10-14T11:10:52.374Z'
    assert report['naturalReturnToReplayListObserved']
    assert report['noFurtherGameplayInputAfterStageSelectionDeclaredByRoot']
    assert not report['allInputEventsMechanicallyRecorded']
    assert report['replayByteSha256'] is None and report['replayFrameCount'] is None
    for key in ['completeGame', 'nativeEquivalent', 'replayExported', 'rawByteIdentityVerified',
                'nativeCodecVerified', 'allIndexedDbPayloadsVerified', 'fullStorageFlowVerified',
                'fullLongNextStageVerified', 'intermediateGameplayFrameCaptured',
                'actualSpeakerOutputMeasured', 'existingFrozenCoreCheckpointModified',
                'priorBrowserFalsePromotedToWholeFlowPass']:
        assert report[key] is False, key

    site = Path(report['frozenSite'])
    shell = site / 'runtime/th14/shell.mjs'
    sdl = site / 'runtime/th14/th14-sdl.mjs'
    def source_assert(path, snippets):
        name = path.relative_to(ROOT).as_posix()
        assert name in report['bindings']
        source = path.read_text(encoding='utf-8')
        for snippet in snippets:
            assert snippet in source, snippet
        return dict(path=name, **report['bindings'][name], checkedSourceSnippets=snippets)
    shell_proof = source_assert(shell, [
        "Module.FS.mount(Module.IDBFS,{},'/savesth14');await sync(true);",
        "Module.FS.mkdirTree('/savesth14/replay');Module.FS.symlink('/savesth14','/save');",
        'Module.FS.syncfs(populate,e=>e?j(e):r())',
        "window.addEventListener('pagehide',()=>{clearKeyboard();cancelTouches();if(core&&launched){suspendRuntimeAudio(Module,core);void save().catch(console.error);}});",
    ])
    sdl_proof = source_assert(sdl, [
        'var IDBFS={dbs:{},indexedDB:()=>indexedDB,DB_VERSION:21,DB_STORE_NAME:"FILE_DATA"',
        'IDBFS.getDB(mount.mountpoint,(err,db)=>',
        'IDBFS.indexedDB().open(name,IDBFS.DB_VERSION)',
    ])
    result = dict(
        independentCustodyAndScopeReviewPassed=True, actualBrowserReexecuted=False,
        databaseInspected=False, compilerOrNativeExecuted=False, networkRequestsSent=False,
        observationReport=dict(path=REPORT.relative_to(ROOT).as_posix(), bytes=REPORT.stat().st_size, sha256=EXPECTED),
        verifiedInputBindings=191, failedInputBindings=0,
        oneReloadReplayPersistenceObserved=True,
        indexedDbBackingInferredFromPackagedSource=True,
        directDatabaseBytesVerified=False, recordedReplayBytesHashObserved=False,
        measuredReplayFrames=None, intermediateGameplayFrameCaptured=False,
        selectedRuntimeReportedBytes=1240, naturalReturnToReplayListObserved=True,
        actionSequenceAndNoFurtherInputSource='ROOT actual CUA declarations; complete input event ledger not captured',
        retainedHistoricalErrorCount=1, retainedHistoricalErrorTimestamp=errors[0]['timestamp'],
        fixedRuntimeWindowStart=report['fixedRuntimeWindowStart'], fixedRuntimeWindowErrors=0, fixedRuntimeWindowWarnings=0,
        wholeConsoleHistoryErrorFree=False,
        packagedStorageSourceEvidence=dict(shell=shell_proof, emscriptenIdbfs=sdl_proof),
        generalStoragePass=False, completeGame=False, nativeEquivalent=False,
        originalObservationAndFirstFailedReceiptModified=False, frozenCheckpointModified=False,
        scope='Independent hashes and parse checks for the already executed small save/reload/select/return UI case. The original screenshots were visually inspected: new slot01 A is visible at save and after the ROOT-reported full same-origin reload/new boot; 19:04 is visible in the after-reload Replay list, not in the save-menu screenshot. This observed persistence succeeds. Current packaged shell mounts IDBFS at /savesth14 and restores it with sync(true), while its bound Emscripten implementation uses IndexedDB/FILE_DATA; this explains a source-based storage backing inference, not direct database-byte inspection. Selected1240B is a runtime log, not an exported-record digest. No measured playback frame count or intermediate gameplay screenshot exists. Both complete console snapshots retain the earlier TDZ failure, while the later fixed window has zero observed errors/warnings. No general storage, Native/full-game equivalence or frozen checkpoint BrowserFalse promotion follows.',
        toolSha256=digest(Path(__file__)),
    )
    OUT.write_bytes((json.dumps(result, indent=2) + '\n').encode())
    print(json.dumps(dict(report=str(OUT), sha256=digest(OUT), bindingsVerified=191,
                          oneReloadReplayPersistenceObserved=True, directDatabaseBytesVerified=False)))


if __name__ == '__main__':
    main()
