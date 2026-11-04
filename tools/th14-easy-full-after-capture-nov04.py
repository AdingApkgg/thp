"""Seal a terminated Easy capture, then run the unchanged observed-clock model.

No live raw files are compared. Failed original exception gates or model
assertions remain failures; no alternative scheduling is selected automatically.
"""
from pathlib import Path
import argparse,hashlib,importlib.util,json,shutil,struct,subprocess,time

R=Path(__file__).resolve().parents[1]
H=R/'artifacts/th14/reimub-easy-full-context-nov04/startup-preserved'
N=H/'full/native';D=H/'full/current-core-comparison'
DRIVER=R/'tools/th14-compare-native-scene-word-read-nov04.mjs'
BUILD=R/'artifacts/th14/scene-camera-read-job-nov04/session-observer-v2/observer-build.json'
ASSETS=R/'artifacts/th14/native-campaign-assets/57d84a5cbe82-ce4cf5a131e3'
sha=lambda path:hashlib.file_digest(Path(path).open('rb'),'sha256').hexdigest()

def seal():
    end=json.loads((H/'full/process-end.json').read_bytes());report=json.loads((N/'report.json').read_bytes());prep=json.loads((H/'prepared.json').read_bytes())
    checks=dict(observerExitedSuccessfully=end['exitCode']==0,outerGuardNotTriggered=end['guardStop']is None,
        childExited=report['childExited'],observerErrorEmpty=not report['error'],noDebugExceptions=not report['debugErrors'],
        originalEndMenuObserved=report['observedForcedReplayEndMenu'],onlyAttractFlagWritten=report['gameStateWordWrites']==1,
        noRngOrCounterWrites=report['rngOrCounterWrites']==0,all75CameraWordsCaptured=report['worldCameraAll75WordsCaptured'],
        muted=report['configuredMusicAndSoundVolumeZero'],observerSourceUnchanged=report['sourceSha256']==prep['observerSha256']==sha(H/'observer.py'),
        replayUnchanged=report['sourceFullReplaySha256']=='ce4cf5a131e3527548d5c7a8ad0312ccaf2b663524bf653426f7ec958bfbeafd')
    count=report['callbacks'];assert count>0
    bindings=[('selected-state.u32','selectedSha256',128),('player-host-monotonic.u64','playerHostTimesSha256',8),
        ('world-camera.raw','worldCameraSha256',292),('world-camera-tail.u32','worldCameraTailSha256',8),
        ('replay-cursor.u32','replayCursorSha256',56),('hud-score.u32','hudScoreSha256',8)]
    hashes={}
    for name,key,stride in bindings:
        path=N/name;digest=sha(path);hashes[name]=digest
        checks[name+'Size']=path.stat().st_size==count*stride;checks[name+'Hash']=digest==report[key]
    stages={};first={};last={};previous=0
    with (N/'selected-state.u32').open('rb')as stream:
        for callback in range(1,count+1):
            row=struct.unpack('<32I',stream.read(128));stage=row[30];assert stage>=previous and 1<=stage<=6
            stages[stage]=stages.get(stage,0)+1;first.setdefault(stage,callback);last[stage]=callback;previous=stage
    checks['allSixStagesObserved']=sorted(stages)==list(range(1,7))
    result=dict(originalCaptureGatePassed=all(checks.values()),checks=checks,callbacks=count,stageCallbacks=stages,stageFirstCallback=first,
        stageLastCallback=last,rawHashes=hashes,nativeReportSha256=sha(N/'report.json'),processEndSha256=sha(H/'full/process-end.json'),
        sourceSha256=report['sourceSha256'],debugExceptionCount=len(report['debugErrors']),exceptionGateWaived=False,
        originalEndDoesNotMeanReplayInputEof=True,ordinaryIndependentTimingAccepted=False,wholeGameAccepted=False,completeGame=False)
    target=H/'full/native-sealed.json';assert not target.exists();target.write_text(json.dumps(result,indent=2)+'\n')
    return result

def main(wait_seconds):
    assert not D.exists();start=time.monotonic();last_notice=0
    while not (H/'full/process-end.json').exists():
        elapsed=time.monotonic()-start
        assert elapsed<wait_seconds,'Capture is still running; retained data were not compared'
        if elapsed-last_notice>=30:
            print(json.dumps(dict(waitingForOriginalTerminal=True,elapsedSeconds=round(elapsed),liveRawComparisonStarted=False)),flush=True);last_notice=elapsed
        time.sleep(2)
    sealed=seal();print(json.dumps(dict(originalCaptureGatePassed=sealed['originalCaptureGatePassed'],callbacks=sealed['callbacks'],debugExceptionCount=sealed['debugExceptionCount'])),flush=True)
    if not sealed['originalCaptureGatePassed']:return 2
    assert sha(DRIVER)=='2ab9b608568fa6de14f1a5f3f495d94fd74c773e8f036c87d25cc9040b93d0c1'
    build=json.loads(BUILD.read_bytes());assert build['wasmSha256']=='22f5abbc63eb71509088ccc822064894d3bc472c3dac89f5a73372e540cf4d0d'
    assert sha(BUILD.parent/'observer.wasm')==build['wasmSha256']
    assert shutil.disk_usage(H).free>100*1024**3
    D.mkdir();argv=['C:/nvm4w/nodejs/node.exe','--no-warnings',str(DRIVER),'--native',str(N),'--assets',str(ASSETS),
        '--build',str(BUILD),'--output',str(D/'model'),'--selection','0,1,0,1','--scheduler-phases','observed']
    (D/'argv.json').write_text(json.dumps(argv,indent=2)+'\n')
    (D/'plan.json').write_text(json.dumps(dict(nativeSealedSha256=sha(H/'full/native-sealed.json'),driverSha256=sha(DRIVER),
        buildSha256=sha(BUILD),wasmSha256=build['wasmSha256'],unchangedNormalDriverUsed=True,
        scheduleSelectedFromNativeStateDifferences=False,strictAcceptanceWhitelistModified=False,maximumSeconds=180,completeGame=False),indent=2)+'\n')
    started=time.monotonic();timed_out=False
    with (D/'process.log').open('wb')as log:
        child=subprocess.Popen(argv,cwd=R,stdout=log,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW)
        try:code=child.wait(timeout=180)
        except subprocess.TimeoutExpired:child.kill();code=child.wait();timed_out=True
    result=dict(exitCode=code,timedOut=timed_out,elapsedSeconds=time.monotonic()-started,completeGame=False)
    (D/'process-end.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result),flush=True)
    return 3 if timed_out else code

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--wait-seconds',type=int,default=1800);args=parser.parse_args();assert 1<=args.wait_seconds<=7200
    raise SystemExit(main(args.wait_seconds))
