"""Bind one actual ordinary full browser replay to frozen later-stage source."""
from pathlib import Path
import argparse,datetime,hashlib,json,subprocess

R=Path(__file__).resolve().parents[1];H=R/'artifacts/th14/native-frame-readback-oct28'
SHA=lambda b:hashlib.sha256(b).hexdigest()

def evidence():
    bindings={}
    def raw(path):
        path=path.resolve(strict=True);assert path.is_relative_to(R)
        data=path.read_bytes();bindings[path.relative_to(R).as_posix()]=dict(bytes=len(data),sha256=SHA(data));return data
    def load(path):return json.loads(raw(path))
    source='babc4e04e4b37f98cbf89d5117065e084fbd8b26'
    ui=H/'later-stage-full-replay-current';launch=load(ui/'launch-request.json');flow=load(ui/'flow-receipt.json')
    assert launch['sourceCommit']==flow['sourceCommit']==source
    assert launch['runtimeEpoch']==flow['runtimeEpoch']==1 and launch['fromStage']==flow['startedAtStage']==1
    for key in ('naturalEndObserved','stableEndObserved','returnedReplayList','fullParentReloadAndRediscovery',
        'gameReplayListRediscovered','ordinaryDownloadPassed','mainAndWorkerServedBytesUnchanged','browser120msKeyConfirmedReturn'):assert flow[key],key
    assert flow['observedStagesDirect']==[2,3,4,5,6]and not flow['stage1RunningScreenshotAvailable']
    assert flow['managerFileCount']==1 and flow['managerReplayName']=='th14_01.rpy'
    assert not flow['stable60FpsAccepted']and not flow['browserVsOriginalWholeFrameComparison']and not flow['browserVsOriginalWholeAudioComparison']
    assert flow['hud']==dict(score=1511063140,lives=1,powerHundredths=358,pointValue=305490,graze=34144)
    elapsed=(datetime.datetime.fromisoformat(flow['naturalEndObservedUtc'].replace('Z','+00:00'))-
        datetime.datetime.fromisoformat(launch['requestedUtc'].replace('Z','+00:00'))).total_seconds();assert elapsed>1200
    original=raw(R/'artifacts/th14/application-full-replay-oct26/initial-save/replay/th14_01.rpy')
    downloaded=raw(ui/'downloaded-full-replay.rpy');download=load(ui/'download-receipt.json')
    assert original==downloaded and len(downloaded)==launch['replayBytes']==flow['replayBytes']==download['bytes']==110306
    assert SHA(downloaded)==launch['replaySha256']==flow['replaySha256']==download['sha256']=='866bf6bac02e1c2b9067dacce6705dc71a512eeb2755106474be492a2d23dcdc'
    home=H/'later-stage-browser-candidate';build=load(home/'build.json')
    publication=load(H/'later-stage-worker-publication/published.json');assert publication['sourceCommit']==source
    manifest=json.loads(subprocess.check_output(['git','-C',str(R/'tools/tmp/github-source-release'),
        'show',source+':docs/github-publication-manifest.json']))
    rows={row['path']:row for row in manifest['files']}
    for path,row in build['sourceBindings'].items():assert SHA(raw(home/'source'/path))==row['sha256']==rows['runtimes/th12/'+path]['sha256']
    main=SHA(raw(home/'th14-sdl.wasm'))
    assert main==build['wasmSha256']==launch['mainWasmSha256']=='0d798fc5cb1830dc4dfc16e976753dd8f9e48415fd494cc3b72ed76d8aa827ae'
    served=load(ui/'served-after-full-run.json');assert served['mainAndWorkerUnchangedAfterFullRun']
    served_rows={row['route']:row for row in served['requests']}
    assert served_rows['/runtime/th14/th14-sdl.wasm']['sha256']==main
    worker=served_rows['/runtime/th14/archive-decoder.wasm']['sha256']
    assert worker=='217c46f4b367a106affb34acdd8a20b2f37576a5546da37f12a89638de39f38d'
    assert all('no-store'in row['cacheControl']for row in served_rows.values())
    logs=load(ui/'full-run.logs.json');messages=[row['message']for row in logs]
    assert any('initial worker ready; control callbacks attached'in message for message in messages)
    waits=[message for message in messages if 'worker wait completed after'in message]
    assert len(waits)==5 and all(float(message.split('after ')[1].split('ms')[0])>=60 for message in waits)
    for name in ('full-replay-list','stage-one-selected','stage2-running',
        *['progress-observation-'+str(index).zfill(2)for index in range(1,10)],
        'natural-end','stable-natural-end','returned-replay-list','manager-after-parent-reload',
        'rediscovered-full-replay','export-result'):
        assert raw(ui/(name+'.jpg'))[:3]==b'\xff\xd8\xff';state=raw(ui/(name+'.ax.txt'))
        assert b'127.0.0.1:8236'in state
    for name in ['th14-browser-full-replay-verified-oct29.json','th14-core-tail-full-replay-verified-oct29.json']:
        prior=load(R/'docs/porting'/name)
        previous=prior.get('selectedDisplayedHud')
        if previous is not None:assert previous==flow['hud']
        else:assert prior['selectedFinalHudScoreDisplayed']==flow['hud']['score']and prior['selectedFinalLives']==flow['hud']['lives']
    return dict(verifiedOneLaterStageOrdinaryBrowserFullReplayFlow=True,frozenSourceCommit=source,
        browserWasmSha256=main,workerWasmSha256=worker,mode='SakuyaB Hard',recording='Deam',startedAtStage=1,
        stagesVisuallySampledDuringFullRun=[2,3,4,5,6],stage1MenuSelectionAndStartupLogsRetained=True,stage1RunningScreenshotAvailable=False,
        actualLaterWorkerWaitCompletions=5,naturalReplayEndAndStableHudObserved=True,selectedDisplayedHud=flow['hud'],
        sameSelectedHudAsTwoEarlierFrozenBrowserRuns=True,elapsedWallSecondsToFirstEndObservation=elapsed,wallTimeIsNotSimulationFrameCount=True,
        parentReloadGameReplayRediscoveryAndOrdinaryDownloadPassed=True,reloadedManagerFileCount=1,
        originalAndDownloadedReplayBytesEqual=110306,replaySha256=SHA(downloaded),
        firstShortConfirmHadNoVisibleEffect=True,documentedBrowser120msKeyConfirmedReturn=True,stable60FpsAccepted=False,
        browserInternalEconomyScoreObserved=False,browserVsOriginalWholeFrameComparison=False,browserVsOriginalWholeAudioComparison=False,
        completeBrowserAcceptance=False,completeGame=False,nativeEquivalent=False,
        verifierSha256=SHA(Path(__file__).read_bytes()),bindings=bindings)

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--check',action='store_true');args=parser.parse_args()
    proof=evidence();target=R/'docs/porting/th14-later-stage-full-replay-verified-oct29.json'
    if args.check:assert json.loads(target.read_bytes())==proof
    else:target.write_text(json.dumps(proof,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    print(json.dumps({key:proof[key]for key in ['verifiedOneLaterStageOrdinaryBrowserFullReplayFlow','frozenSourceCommit','stable60FpsAccepted','completeGame']}))
if __name__=='__main__':main()
