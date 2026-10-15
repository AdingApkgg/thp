"""Recheck stored actual-browser save evidence; does not run the producers."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
SHA=lambda b:hashlib.sha256(b).hexdigest()

def main():
    doc=json.loads((ROOT/'docs/porting/th14-save-delta-observed-oct16.json').read_text(encoding='utf-8'))
    assert doc['schema']=='th14-save-delta-evidence-v1' and not doc['completeGame'] and not doc['nativeEquivalent']
    assert SHA(Path(__file__).read_bytes())==doc['checkerSha256']
    for name,row in doc['bindings'].items():
        path=(ROOT/name).resolve();assert path.is_relative_to(ROOT)
        data=path.read_bytes();assert len(data)==row['bytes'] and SHA(data)==row['sha256'],name
    qa=ROOT/'artifacts/th14/save-delta-browser-check-oct16'
    result=json.loads((qa/'capture/report.json').read_text())
    assert result['passed'] and result['executedCases']==9 and len(result['cases'])==9 and not result['error']
    assert all(row['passed'] for row in result['cases'])
    assert result['actualIndexedDb'] and result['actualEmscriptenFs'] and result['actualIdbfs']
    assert result['actualGameFrames']==result['gpuDraws']==0 and not result['audioPlayed']
    assert result['cases'][0]['newReplayDeleted'] and not result['cases'][7]['actualQuotaError']
    assert (qa/'delta.mjs').read_bytes()==(ROOT/'runtimes/th14/th14_web/browser-save-delta.mjs').read_bytes()
    assert (qa/'run.mjs').read_bytes()==(ROOT/'tools/th14-save-delta-browser-check-oct16.mjs').read_bytes()
    runtime=json.loads((ROOT/'docs/porting/th14-launcher-runtime-save-delta-oct16.json').read_text())
    site=json.loads((ROOT/'docs/porting/th14-launcher-site-save-delta-oct16.json').read_text())
    assert runtime['sameProductionWasm'] and runtime['sourceSnapshotBound'] and not runtime['currentWorkspaceSourcesVerified']
    assert site['sameProductionWasm'] and site['frozenLauncherReused'] and not site['currentWorkspaceGameSourcesVerified']
    frozen=Path(runtime['buildDirectory']);build=runtime['build']
    for name,digest in {**build['sources'],**build['headers']}.items():
        assert SHA((frozen/'source'/name).read_bytes())==digest,name
    for name,digest in build['objectHashes'].items():assert SHA((frozen/name).read_bytes())==digest,name
    expected='7e42a509065676ece981f2e8e5e7ce9a86d2960d02149398b1c0c0316c15f088'
    assert result['wasmSha256']==runtime['build']['sha256']==expected
    assert SHA((ROOT/'runtimes/th14/th14_web/browser-save-delta.mjs').read_bytes())==runtime['sourceSaveDeltaSha256']==site['sourceSaveDeltaSha256']
    for report,folder in [(runtime,runtime['out']),(site,site['site'])]:
        for name,row in report['files'].items():
            data=(Path(folder)/name).read_bytes();assert len(data)==row['bytes'] and SHA(data)==row['sha256'],name
    assert len(runtime['files'])==40 and len(site['files'])==127
    assert site['changedFiles']==['app-shell-sw.js','runtime/th14/runtime-files.json','runtime/th14/shell.mjs']
    assert SHA((Path(runtime['out'])/'th14-sdl.wasm').read_bytes())==expected
    observed=json.loads((ROOT/'artifacts/th14/save-delta-preview-oct16/two-window-final-observed.json').read_text())
    assert observed['managerCount']==3 and observed['firstWindowRunning'] and observed['quietBothWindows']
    assert not observed['warningsAndErrors'] and observed['fullDocumentReloads']==2 and observed['secondsFromImportToFinalRead']>=120
    assert not observed['periodicSyncInstrumented'] and not observed['newReplayExported']
    assert not doc['currentWorkspaceCppRebuilt'] and doc['frozenProductionWasmReused']
    print(json.dumps(dict(storedEvidenceVerified=True,producerExecutedByChecker=False,actualBrowserCases=9,actualGameWindows=2,
        afterReloadReplayCount=3,sameProductionWasm=expected,completeGame=False,nativeEquivalent=False)))

if __name__=='__main__':main()
