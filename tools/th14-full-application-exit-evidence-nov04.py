"""Compare the current complete Application replay/exit with its same-core parent.

The parent is a C++ Application, not original whole-game pixels/PCM. Differences
are retained before a nonzero exit; no field, handle or pixel is normalized.
"""
from pathlib import Path
import argparse,hashlib,json

R=Path(__file__).resolve().parents[1];H=R/'artifacts/th14/config-startup-fallback-nov04'
P=R/'artifacts/th14/scene-camera-read-job-nov04/ordinary-full-exit'
SHA=lambda raw:hashlib.sha256(raw).hexdigest()

def evidence():
    bindings={}
    def read(path):
        path=Path(path).resolve(strict=True);assert path.is_relative_to(R)
        raw=path.read_bytes();bindings[path.relative_to(R).as_posix()]=dict(bytes=len(raw),sha256=SHA(raw));return raw
    def load(path):return json.loads(read(path))
    folder=H/'full-flow';plan=load(folder/'plan.json');now=load(folder/'gles/report.json');old=load(P/'gles/report.json')
    assert load(folder/'process-end.json')['exitCode']==load(P/'process-end.json')['exitCode']==0
    for run in [now,old]:
        assert run['completed'] and not run['error'] and run['exitSaveCompleted'] and run['exitSaveRequested']
        assert run['physicalAudioDevicesOpened']==0 and not run['browserRun'] and not run['browserAcceptance']
        assert all(row['passed']for row in run['checks']) and len(run['checks'])==53
        assert len(run['actions'])==34 and len(run['captures'])==10
        assert run['actions'][-1]['state'][0]==4
        assert run['actions'][23]['state'][0:2]==[2,6]
        assert run['actions'][23]['state'][7]==8 and run['actions'][23]['state'][9]==91452576
        assert [run['actions'][12]['state'][1]]+[run['actions'][13+2*n]['state'][1]for n in range(5)]==[1,2,3,4,5,6]
    build_home=R/plan['build'];build=load(build_home/'build.json')
    assert now['buildReportSha256']==SHA(read(build_home/'build.json'))
    assert now['wasmSha256']==plan['wasmSha256']==build['wasmSha256']==SHA(read(build_home/'application.wasm'))
    assert build['rootApplicationSourceSha256']==SHA(read(R/'runtimes/th12/th12_web/cpp/sdl/Application.cpp'))
    assert now['toolSha256']==SHA(read(folder/'gles/run-tool.py'))==plan['hostSha256']
    assert SHA(read(P/'gles/report.json'))==plan['sameCoreParentRunSha256']
    assert now['scenarioSha256']==old['scenarioSha256']==plan['scenarioSha256']==SHA(read(P/'scenario.json'))
    assert build['coreObjects']==load(P/'build/build.json')['coreObjects']
    for row in build['coreObjects']+build['applicationObjectBindings']:assert SHA(read(row['path']))==row['sha256']
    for name,row in build['sourceBindings'].items():assert SHA(read(R/name))==row['sha256']
    fields=['frames','checks','initialSave','finalSave','rows','actions','glCalls','pendingAsyncCallbacks',
        'deliveredCallbackSequence','files','pcmFrames','pcmSha256','applicationTicks',
        'replayConstructionTransitions','replayCadenceObservations','finalReferenceState']
    differing_payloads=[name for name in fields if now[name]!=old[name]]
    images=[];vm=[]
    for current,previous in zip(now['captures'],old['captures']):
        assert current['label']==previous['label'] and current['frame']==previous['frame']
        raw=read(folder/'gles'/current['file']);before=read(P/'gles'/previous['file'])
        assert len(raw)==len(before)==640*480*4 and SHA(raw)==current['sha256'] and SHA(before)==previous['sha256']
        wrong=sum(a!=b for a,b in zip(raw,before))
        images.append(dict(label=current['label'],frame=current['frame'],comparedBytes=len(raw),differentBytes=wrong,
            referenceStateEqual=current['referenceState']==previous['referenceState']))
        current_vm=load(folder/'gles'/current['liveAnimations']['file']);previous_vm=load(P/'gles'/previous['liveAnimations']['file'])
        for item in [current_vm,previous_vm]:assert item['readOnly'] and item['complete'] and item['comparedValues']==303
        assert SHA(read(folder/'gles'/current['liveAnimations']['file']))==current['liveAnimations']['sha256']
        assert SHA(read(P/'gles'/previous['liveAnimations']['file']))==previous['liveAnimations']['sha256']
        a,b=current_vm['rows'],previous_vm['rows']
        if len(a)==len(b):
            wrong_fields={str(field):sum(x[field]!=y[field]for x,y in zip(a,b))for field in range(303)}
            wrong_fields={key:value for key,value in wrong_fields.items()if value}
        else:wrong_fields=None
        vm.append(dict(label=current['label'],rows=len(a),parentRows=len(b),rowsAndRegistryOrderEqual=a==b,
            differentFields=wrong_fields,metadataEqual={k:v for k,v in current_vm.items()if k!='rows'}=={k:v for k,v in previous_vm.items()if k!='rows'}))
    for name,row in now['finalSave'].items():assert SHA(read(folder/'gles/save'/name))==row['sha256']
    assert now['initialSave']['replay/th14_01.rpy']==now['finalSave']['replay/th14_01.rpy']
    persisted=load(H/'persisted-score-readback/verified.json')
    assert persisted['verifiedActualApplicationNondefaultScoreReadback'] and persisted['wasmSha256']==now['wasmSha256']
    assert persisted['toolSha256']==SHA(read(R/'tools/th14-persisted-score-readback-nov04.py'))
    assert persisted['reportSha256']==SHA(read(H/'persisted-score-readback/gles/report.json'))
    assert load(H/'persisted-score-readback/process-end.json')['exitCode']==0
    for name in ['scoreth14.dat','th14.cfg']:
        assert read(H/'persisted-score-readback/initial-save'/name)==read(H/'persisted-score-readback/gles/save'/name)
    passed=not differing_payloads and all(not row['differentBytes']and row['referenceStateEqual']for row in images)and all(row['rowsAndRegistryOrderEqual']and row['metadataEqual']for row in vm)
    return dict(schema='th14/current-application-full-exit/1',verifiedCurrentApplicationFullFlow=passed,
        applicationSourceCommit=plan['applicationSourceCommit'],unchangedGameplayCoreCommit=plan['sourceCoreCommit'],
        wasmSha256=now['wasmSha256'],frames=now['frames'],assertions=53,naturalReplayEndFrame=now['actions'][23]['endFrame'],
        stages=[1,2,3,4,5,6],naturalEndScoreUnits=91452576,naturalEndLives=8,ordinaryNormalizedQuitAndProductionSave=True,
        inputReplayByteUnchanged=True,comparedParentPayloads=fields,differingParentPayloads=differing_payloads,
        images=images,vmSnapshots=vm,silentPcmFrames=now['pcmFrames'],silentPcmSha256=now['pcmSha256'],
        physicalAudioDevicesOpened=0,nondefaultScoreReadbackBytes=21656,nondefaultScoreAndConfigReadbackUnchanged=True,
        wholeApplicationReferenceIsSameCoreCppParent=True,originalWholePixelsOrPcmCompared=False,
        originalGuiAccepted=False,browserAcceptance=False,independentSchedulingAccepted=False,
        completeGame=False,nativeEquivalent=False,bindings=bindings,verifierSha256=SHA(Path(__file__).read_bytes()))

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);p.add_argument('--check',action='store_true');a=p.parse_args()
    out=a.output.resolve();assert out.is_relative_to(R);value=evidence()
    if a.check:assert json.loads(out.read_bytes())==value
    else:assert not out.exists();out.write_text(json.dumps(value,indent=2)+'\n')
    print(json.dumps({key:value[key]for key in ['verifiedCurrentApplicationFullFlow','frames','assertions','differingParentPayloads','browserAcceptance']}))
    assert value['verifiedCurrentApplicationFullFlow'],'Retained differences must be reviewed'

if __name__=='__main__':main()
