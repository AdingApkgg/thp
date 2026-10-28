"""Bind one ordinary full browser replay's visual/file evidence to frozen code."""
from pathlib import Path
import argparse,datetime,hashlib,json,subprocess
R=Path(__file__).resolve().parents[1];H=R/'artifacts/th14/native-frame-readback-oct28';SHA=lambda b:hashlib.sha256(b).hexdigest()
def evidence():
    bindings={}
    def raw(path):
        path=path.resolve(strict=True);assert path.is_relative_to(R);b=path.read_bytes();bindings[path.relative_to(R).as_posix()]=dict(bytes=len(b),sha256=SHA(b));return b
    def load(path):return json.loads(raw(path))
    ui=H/'browser-full-replay-current';prepared=load(ui/'preparation.json');launch=load(ui/'launch-time.json');flow=load(ui/'flow-receipt.json')
    source='7d490039fea57057995d7902e325bb45ec355823';assert prepared['sourceCommit']==launch['sourceCommit']==flow['sourceCommit']==source
    assert flow['naturalEndObserved']and flow['stableEndObserved']and flow['returnedReplayList']and flow['fullParentReloadAndRediscovery']
    assert flow['hud']['score']==1511063140 and flow['hud']['lives']==1
    assert flow['observedStagesDirect']==[1,2,4,5,6]and flow['stage3DuringFullRunNotVisuallySampled']
    elapsed=(datetime.datetime.fromisoformat(flow['naturalEndObservedUtc'].replace('Z','+00:00'))-datetime.datetime.fromisoformat(launch['launchedUtc'].replace('Z','+00:00'))).total_seconds()
    assert elapsed>1200
    original=raw(Path(prepared['replayPath']));downloaded=raw(ui/'downloaded-full-replay.rpy')
    assert original==downloaded and len(downloaded)==prepared['replayBytes']==110306 and SHA(downloaded)==prepared['replaySha256']=='866bf6bac02e1c2b9067dacce6705dc71a512eeb2755106474be492a2d23dcdc'
    browser_home=H/'anm-parser-browser-candidate-v2';build=load(browser_home/'build.json');published=load(H/'anm-worker-publication/published.json')
    assert published['sourceCommit']==source and build['wasmSha256']==prepared['browserWasmSha256']=='cef8961af946ff8ff24e440a4681907da5940a5cf7acad03c730ca87cfc48182'
    # Compare the immutable build sources to the actual published source tree,
    # not the newer, intentionally changed workspace STD/ECL implementation.
    manifest_raw=subprocess.check_output(['git','-C',str(R/'tools/tmp/github-source-release'),'show',source+':docs/github-publication-manifest.json']);manifest=json.loads(manifest_raw);rows={x['path']:x for x in manifest['files']}
    for path,row in build['sourceBindings'].items():
        assert SHA(raw(browser_home/'source'/path))==row['sha256']and rows['runtimes/th12/'+path]['sha256']==row['sha256']
    assert SHA(raw(browser_home/'th14-sdl.wasm'))==build['wasmSha256']
    served=load(H/'anm-parser-launcher/served-current.json');assert served['wasmSha256']==build['wasmSha256']and served['quietInjectedIntoParentAndIframe']
    for name in ('import-result','full-user-replay-list','full-stage-selection','stage1-running','progress-002','progress-003','progress-004','progress-005','progress-006','natural-end','stable-natural-end','returned-replay-list','rediscovered-full-replay','export-result'):
        image=raw(ui/(name+'.jpg'));assert image[:3]==b'\xff\xd8\xff';raw(ui/(name+'.ax.txt'))
    native=load(H/'initial-decode-full-replay/gles/report.json');assert native['completed']and native['frames']==123412
    ends=[x['state']for x in native['actions']if x['state'][0]==2 and x['state'][7]==1]
    assert ends and ends[-1][9]==154806314
    frozen=next(x for x in native['captures']if x['label']=='stable-replay-end')
    assert SHA(raw(H/'initial-decode-full-replay/gles'/frozen['file']))==frozen['sha256']=='e57236384f3ec728a64d5fa78b0a1b60a5e03963c2cbc84b3ef1f5796a78670b'
    raw(ui/'frozen-native-stable-end.png');audit=load(ui/'comparison-audit.json')
    assert audit['previousStateVsHudComparisonWithdrawn']and audit['frozenNativeHudDisplayedScore']==flow['hud']['score']
    assert audit['browserInternalEconomyScoreNotObserved']and not audit['productionChangeMadeToForceScoreMatch']
    return dict(verifiedOneOrdinaryBrowserFullReplayFlow=True,frozenSourceCommit=source,browserWasmSha256=build['wasmSha256'],mode='SakuyaB Hard',recording='Deam',startedAtStage=1,
        naturalReplayEndAndStableHudObserved=True,selectedFinalHudScoreDisplayed=1511063140,selectedFinalLives=1,
        elapsedWallSecondsToFirstEndObservation=elapsed,elapsedWallTimeIsNotSimulationFrameCount=True,
        stagesVisuallySampledDuringFullRun=[1,2,4,5,6],stage3FullRunScreenshotMissing=True,
        parentReloadReplayRediscoveryAndDownloadPassed=True,originalAndDownloadedReplayBytesEqual=110306,
        replaySha256=SHA(downloaded),frozenNativeHudVisualSelectedFieldsMatch=True,
        frozenNativeInternalScoreUnits=154806314,browserInternalEconomyScoreObserved=False,
        previousStateVsHudComparisonWithdrawn=True,
        browserVsOriginalWholeFrameComparison=False,browserVsOriginalWholeAudioComparison=False,
        currentStageEclCandidateInheritsThisFullRun=False,completeBrowserAcceptance=False,completeGame=False,nativeEquivalent=False,
        verifierSha256=SHA(Path(__file__).read_bytes()),bindings=bindings)
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--check',action='store_true');a=p.parse_args();proof=evidence();target=R/'docs/porting/th14-browser-full-replay-verified-oct29.json'
    if a.check:assert json.loads(target.read_bytes())==proof
    else:target.write_text(json.dumps(proof,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    print(json.dumps({k:proof[k]for k in ('verifiedOneOrdinaryBrowserFullReplayFlow','frozenSourceCommit','originalAndDownloadedReplayBytesEqual','completeGame')}))
if __name__=='__main__':main()
