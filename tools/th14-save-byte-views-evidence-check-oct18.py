"""Read-only verification of frozen TH14 save-byte-view evidence; runs no producer."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WASM = 'f798639ddabdc0be3b278dbf56fed2b43e4a27b78b964f8f9cddff5d3b4fb4ec'
BEFORE = 'c44463fb394ca57dbf1a3a925cb44f2a2cfa4a9da4e5a441c751d7cc9cf66a55'
AFTER = 'a899ac238872df29802d45ac36b75350ebb91c9e81515fdac8f532f65ce637d1'

def load(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))

def digest(path):
    return hashlib.file_digest(Path(path).open('rb'), 'sha256').hexdigest()

def main():
    doc = load(ROOT / 'docs/porting/th14-save-byte-views-observed-oct18.json')
    assert doc['checkerSha256'] == digest(__file__)
    for name, row in doc['bindings'].items():
        path = (ROOT / name).resolve()
        assert path.is_relative_to(ROOT)
        assert path.stat().st_size == row['bytes'] and digest(path) == row['sha256'], name
    base = ROOT / 'artifacts/th14'
    old = base / 'save-byte-views-before-oct18'
    new = base / 'save-byte-views-after-oct18'
    before, after = load(old / 'capture/report.json'), load(new / 'capture/report.json')
    assert not before['passed'] and len(before['cases']) == 10 and '另一个窗口' in before['error']
    assert after['passed'] and after['executedCases'] == len(after['cases']) == 13
    assert all(row['passed'] for row in after['cases'])
    assert before['cases'] == after['cases'][:10]
    assert after['cases'][9]['falseConflictReproduced'] and after['cases'][9]['remoteType'] == 'Int8Array'
    assert after['cases'][9]['physicalBytes'] == [0, 127, 128, 255, 214]
    assert not after['cases'][7]['actualQuotaError']
    assert before['database'] != after['database']
    for report in [before, after]:
        assert report['actualIndexedDb'] and report['actualEmscriptenFs'] and report['actualIdbfs']
        assert report['wasmSha256'] == WASM and report['actualGameFrames'] == report['gpuDraws'] == 0
        assert not report['audioPlayed'] and not report['productionGameChanged']
    assert (old / 'run.mjs').read_bytes() == (new / 'run.mjs').read_bytes() == (ROOT / 'tools/th14-save-byte-views-browser-check-oct18.mjs').read_bytes()
    assert digest(old / 'delta.mjs') == digest(old / 'delta-before.mjs') == digest(new / 'delta-before.mjs') == BEFORE
    assert digest(new / 'delta.mjs') == digest(ROOT / 'runtimes/th14/th14_web/browser-save-delta.mjs') == AFTER
    observed = load(base / 'save-byte-views-fixed-preview-oct18/observed.json')
    assert observed['managerCount'] == 4 and len(observed['managerFiles']) == 4
    assert observed['quietGame'] and observed['quietManager'] and not observed['gameWarningsAndErrors']
    assert observed['secondsFromFirstCommitToObservation'] >= 600
    assert not observed['naturalReplayEofObserved'] and not observed['actualBrowserFrameCountInstrumented']
    assert not observed['newScoreExported'] and not observed['fullGameReloadDuringPlayback']
    events = [json.loads(row['message'].split('] ', 1)[1]) for row in observed['gameLogs']]
    checks = [row for row in events if row['event'] == 'remote-check']
    commits = [row for row in events if row['event'] == 'committed']
    assert checks[0]['remote']['viewType'] == 'Int8Array' and checks[0]['baseline']['viewType'] == 'Uint8Array'
    assert checks[0]['remote']['bytes'] == checks[0]['baseline']['bytes'] == 21639
    assert len(commits) >= 5 and all(not row['removes'] for row in commits)
    assert commits[0]['writes'][0]['path'] == '/savesth14/scoreth14.dat'
    assert commits[0]['writes'][0]['bytes'] == 21640
    runtime = load(ROOT / 'docs/porting/th14-launcher-runtime-save-byte-views-oct18.json')
    site = load(ROOT / 'docs/porting/th14-launcher-site-save-byte-views-oct18.json')
    old_runtime = load(ROOT / 'docs/porting/th14-launcher-runtime-loading-family-oct16.json')
    old_site = load(ROOT / 'docs/porting/th14-launcher-site-loading-family-oct16.json')
    assert runtime['sameProductionWasm'] and runtime['sourceSnapshotBound'] and runtime['build']['sha256'] == WASM
    assert site['sameProductionWasm'] and site['frozenLauncherReused'] and not site['currentWorkspaceGameSourcesVerified']
    assert runtime['sourceSaveDeltaSha256'] == site['sourceSaveDeltaSha256'] == AFTER
    for report, previous, folder, count in [(runtime, old_runtime, runtime['out'], 40), (site, old_site, site['site'], 127)]:
        assert len(report['files']) == count and set(report['files']) == set(previous['files'])
        for name, row in report['files'].items():
            path = Path(folder) / name
            assert path.stat().st_size == row['bytes'] and digest(path) == row['sha256'], name
    changed_runtime = sorted(name for name, row in runtime['files'].items() if row != old_runtime['files'][name])
    changed_site = sorted(name for name, row in site['files'].items() if row != old_site['files'][name])
    assert changed_runtime == ['shell.mjs']
    assert changed_site == site['changedFiles'] == ['app-shell-sw.js', 'runtime/th14/runtime-files.json', 'runtime/th14/shell.mjs']
    assert not doc['completeGame'] and not doc['nativeEquivalent'] and doc['consoleObserverUsedInActualGame']
    print(json.dumps(dict(storedEvidenceVerified=True, producerExecutedByChecker=False,
        isolatedBrowserCases=13, beforePositiveSignedCaseFailed=True, actualManagerReplayFiles=4,
        actualGameSuccessfulCommits=len(commits), observedAfterFirstCommitSeconds=observed['secondsFromFirstCommitToObservation'],
        sameProductionWasm=True, completeGame=False, nativeEquivalent=False)))

if __name__ == '__main__':
    main()
