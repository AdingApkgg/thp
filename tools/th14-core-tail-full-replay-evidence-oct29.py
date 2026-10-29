"""Bind the second actual full browser replay to its frozen core-tail source."""
from pathlib import Path
import argparse,datetime,hashlib,json,subprocess
R=Path(__file__).resolve().parents[1];H=R/'artifacts/th14/native-frame-readback-oct28';SHA=lambda b:hashlib.sha256(b).hexdigest()
def evidence():
    bindings={}
    def raw(path):
        path=path.resolve(strict=True);assert path.is_relative_to(R);data=path.read_bytes();bindings[path.relative_to(R).as_posix()]=dict(bytes=len(data),sha256=SHA(data));return data
    def load(path):return json.loads(raw(path))
    ui=H/'core-tail-full-replay-current';launch=load(ui/'launch-request.json');flow=load(ui/'flow-receipt.json')
    source='2e6d794a821cf89b28ca7ea743c78c628442e01b';assert launch['sourceCommit']==flow['sourceCommit']==source
    assert launch['runtimeEpoch']==2 and launch['fromStage']==1
    for key in ('naturalEndObserved','stableEndObserved','returnedReplayList','fullParentReloadAndRediscovery','ordinaryDownloadPassed','earlierDrawThrottlingObserved'):assert flow[key],key
    assert not flow['stable60FpsAccepted']and flow['observedStagesDirect']==[1,2,3,4,5,6]
    assert flow['hud']==dict(score=1511063140,lives=1,powerHundredths=358,pointValue=305490,graze=34144)
    elapsed=(datetime.datetime.fromisoformat(flow['naturalEndObservedUtc'].replace('Z','+00:00'))-datetime.datetime.fromisoformat(launch['requestedUtc'].replace('Z','+00:00'))).total_seconds();assert elapsed>1200
    original=raw(R/'artifacts/th14/application-full-replay-oct26/initial-save/replay/th14_01.rpy');downloaded=raw(ui/'downloaded-full-replay.rpy')
    assert original==downloaded and len(downloaded)==launch['replayBytes']==110306 and SHA(downloaded)==launch['replaySha256']=='866bf6bac02e1c2b9067dacce6705dc71a512eeb2755106474be492a2d23dcdc'
    home=H/'core-tail-browser-candidate';build=load(home/'build.json');published=load(H/'core-tail-worker-publication/published.json')
    assert published['sourceCommit']==source and build['wasmSha256']==launch['mainWasmSha256']=='3957b4a20e3ca984842db5d66e2ce60d637085a4c3d5955ffc29f81f3c91e460'
    manifest=json.loads(subprocess.check_output(['git','-C',str(R/'tools/tmp/github-source-release'),'show',source+':docs/github-publication-manifest.json']));rows={row['path']:row for row in manifest['files']}
    for path,row in build['sourceBindings'].items():assert SHA(raw(home/'source'/path))==row['sha256']==rows['runtimes/th12/'+path]['sha256']
    check=SHA(raw(home/'th14-sdl.wasm'));assert check==build['wasmSha256']
    served=load(H/'core-tail-launcher/served-current.json');assert served['wasmSha256']==check and served['quietInjectedIntoParentAndIframe']
    for name in ('manager-two-files','full-replay-list','stage-one-selected','stage1-running',
        *['progress-observation-'+str(index).zfill(2)for index in range(2,12)],
        'natural-end','stable-natural-end','returned-replay-list','rediscovered-full-replay','export-result'):
        assert raw(ui/(name+'.jpg'))[:3]==b'\xff\xd8\xff';raw(ui/(name+'.ax.txt'))
    prior=load(R/'docs/porting/th14-browser-full-replay-verified-oct29.json');assert prior['selectedFinalHudScoreDisplayed']==flow['hud']['score']and prior['selectedFinalLives']==flow['hud']['lives']
    return dict(verifiedOneCoreTailOrdinaryBrowserFullReplayFlow=True,frozenSourceCommit=source,browserWasmSha256=check,
        mode='SakuyaB Hard',recording='Deam',startedAtStage=1,stagesVisuallySampledDuringFullRun=[1,2,3,4,5,6],
        naturalReplayEndAndStableHudObserved=True,selectedDisplayedHud=flow['hud'],sameSelectedHudAsEarlierFrozenBrowserRun=True,
        elapsedWallSecondsToFirstEndObservation=elapsed,wallTimeIsNotSimulationFrameCount=True,earlierDrawThrottlingObserved=True,stable60FpsAccepted=False,
        parentReloadReplayRediscoveryAndOrdinaryDownloadPassed=True,originalAndDownloadedReplayBytesEqual=110306,replaySha256=SHA(downloaded),
        currentLaterStageCandidateInheritsThisFullRun=False,browserInternalEconomyScoreObserved=False,
        browserVsOriginalWholeFrameComparison=False,browserVsOriginalWholeAudioComparison=False,completeBrowserAcceptance=False,completeGame=False,nativeEquivalent=False,
        verifierSha256=SHA(Path(__file__).read_bytes()),bindings=bindings)
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--check',action='store_true');a=p.parse_args();proof=evidence();target=R/'docs/porting/th14-core-tail-full-replay-verified-oct29.json'
    if a.check:assert json.loads(target.read_bytes())==proof
    else:target.write_text(json.dumps(proof,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    print(json.dumps({k:proof[k]for k in ('verifiedOneCoreTailOrdinaryBrowserFullReplayFlow','frozenSourceCommit','stable60FpsAccepted','completeGame')}))
if __name__=='__main__':main()
