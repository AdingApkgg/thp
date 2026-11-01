"""Require both terminal full Applications built after the initialization repair."""
from pathlib import Path
import argparse,hashlib,importlib.util,json,shutil,subprocess
R=Path(__file__).resolve().parents[1];SHA=lambda b:hashlib.sha256(b).hexdigest()

def evidence(webgpu_home,gles_home):
    bindings={}
    def raw(path):
        path=path.resolve(strict=True);assert path.is_relative_to(R)
        data=path.read_bytes();bindings[path.relative_to(R).as_posix()]=dict(bytes=len(data),sha256=SHA(data));return data
    def load(path):return json.loads(raw(path))
    # Read terminal receipts first: live prefixes cannot satisfy this gate.
    homes=[webgpu_home.resolve(strict=True),gles_home.resolve(strict=True)]
    assert all(h.is_relative_to(R/'artifacts/th14')for h in homes)
    ends=[load(h/'process-end.json')for h in homes]
    assert all(e['exitCode']==0 and e['guardStop']is None and e['elapsedSeconds']<=6060 for e in ends)
    runs=[load(h/backend/'report.json')for h,backend in zip(homes,['webgpu','gles'])]
    assert all(r['completed']and not r['error']and r['frames']==122622 for r in runs)
    module_path=R/'tools/th14-initialization-boundary-evidence-nov01.py';raw(module_path)
    spec=importlib.util.spec_from_file_location('initialization_repair_proof',module_path);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    repair=module.evidence(R/'artifacts/th14/nested-init-worker-nov01')
    assert repair==load(R/'docs/porting/th14-initialization-boundary-nov01.json')and repair['verifiedControlledInitializationBoundary']
    peer_home=R/'artifacts/th14/reimub-normal-ordinary-application-oct30'
    historical=raw(peer_home/'verified.json');assert SHA(historical)=='ba9a17b608155407c4408c6ffa27ae4d4ce554484cf774e996539687fa688627'
    sealed=json.loads(historical)
    for name,binding in sealed['bindings'].items():
        p=R/name;data=p.read_bytes()
        if SHA(data)!=binding['sha256']:
            assert name.startswith(('runtimes/','tools/'))
            data=subprocess.check_output(['git','-C',str(R/'tools/tmp/github-source-release'),'show','8d50230dc1123c30f83a0fb29de2f6728564f60b:'+name])
        assert len(data)==binding['bytes']and SHA(data)==binding['sha256'],name
    peer=load(peer_home/'gles/report.json');plans=[load(h/'plan.json')for h in homes]
    builds=[]
    for home,backend,run,plan in zip(homes,['webgpu','gles'],runs,plans):
        assert plan['sourceCommit']=='9b4201204405e1d7f6d5f28d6c71faf603b2836d'and plan['backend']==run['backend']==backend
        assert plan['maximumFrames']==150000 and plan['maximumWallSeconds']==6000
        assert plan['minimumFreeBytes']==100*1024**3 and plan['maximumOutputBytes']==128*1024**2
        assert plan['productionInitializationBoundaryRepair']and not plan['previousCompleteResultInherited']and not plan['automaticNextCase']
        build_home=R/plan['build'];build=load(build_home/'build.json');builds.append(build)
        assert build['compiled']and build['productionSourceFilesUnmodified']and len(build['coreObjects'])==141
        assert SHA(raw(build_home/'application.wasm'))==build['wasmSha256']==plan['wasmSha256']==run['wasmSha256']
        assert SHA(raw(build_home/'build.json'))==run['buildReportSha256']
        for row in build['coreObjects']:assert SHA(raw(Path(row['path'])))==row['sha256']
        for name,digest in build['newObjects'].items():assert SHA(raw(build_home/name))==digest
        for name,binding in build['sourceBindings'].items():assert SHA(raw(R/name))==binding['sha256']
        assert run['actualProductionApplicationAndDevices']and run['platformClockAndIoDeclared']and run['physicalAudioDevicesOpened']==0
        assert not run['browserRun']and not run['browserAcceptance']and not run['completeGame']and not run['nativeEquivalent']
        assert plan['runnerSha256']==run['toolSha256']==SHA(raw(home/backend/'run-tool.py'))==SHA(raw(R/plan['runner']))
        assert run['hostToolSha256']==SHA(raw(R/('tools/th14-native-webgpu-context.py'if backend=='webgpu'else'tools/th14-native-gles-context.py')))
        assert raw(home/'scenario.json')==raw(peer_home/'scenario.json')and run['scenarioSha256']==plan['scenarioSha256']==peer['scenarioSha256']
        assert len(run['checks'])==45 and all(c['passed']for c in run['checks'])and len(run['actions'])==25
        assert run['actions'][-2]['endFrame']==122562 and run['actions'][-1]['endFrame']==122622
        assert run['actions'][-1]['state'][7]==8 and run['actions'][-1]['state'][9]==91452576
        assert load(home/backend/'declared-process-entropy.json')==load(peer_home/'gles/declared-process-entropy.json')
        replay=raw(home/'initial-save/replay/th14_01.rpy');assert replay==raw(home/backend/'save/replay/th14_01.rpy')==raw(peer_home/'initial-save/replay/th14_01.rpy')
        assert SHA(replay)==plan['sourceReplaySha256']==sealed['replaySha256']
        for key in ['actions','checks','rows','initialSave','finalSave','pcmFrames','pcmSha256','pendingAsyncCallbacks','deliveredCallbackSequence','declaredInitialGameTicks','metadataEpochAtFrameZero']:
            assert run[key]==peer[key],(backend,key)
        assert len(run['captures'])==len(peer['captures'])==8
        for capture,old in zip(run['captures'],peer['captures'],strict=True):
            for key in ['frame','label','referenceState','liveAnimations']:assert capture[key]==old[key]
            pixels=raw(home/backend/capture['file']);assert len(pixels)==1228800 and SHA(pixels)==capture['sha256']and pixels==raw(peer_home/'gles'/old['file'])
            live=capture['liveAnimations'];data=raw(home/backend/live['file']);assert SHA(data)==live['sha256']and data==raw(peer_home/'gles'/old['liveAnimations']['file'])
        assert sum(p.stat().st_size for p in home.rglob('*')if p.is_file())<=128*1024**2 and shutil.disk_usage(home).free>=100*1024**3
    assert builds[0]['coreObjects']==builds[1]['coreObjects']and builds[0]['coreSourceHashes']==builds[1]['coreSourceHashes']
    assert builds[0]['coreBuildSha256']==builds[1]['coreBuildSha256']and builds[0]['compilerSha256']==builds[1]['compilerSha256']
    return dict(verifiedCurrentInitializedApplicationsFullReplay=True,sourceCommit=plans[0]['sourceCommit'],backends=['webgpu','gles'],framesPerBackend=122622,assertionsPerBackend=45,naturalEndFrame=122562,stableEndFrames=60,fullImagesPerBackend=8,coreObjectsVerified=141,currentBackendsAndSealedHistoricalGlesSelectedJournalsEqual=True,allCapturedVmRowsAndFullImagesByteEqual=True,filesAndReplayByteEqual=True,silentPcmFrames=runs[0]['pcmFrames'],silentPcmSha256=runs[0]['pcmSha256'],currentGlesWholeRunActuallyExecuted=True,oldGlesProofVersionBoundAndRechecked=True,physicalAudioDevicesOpened=0,ordinaryOriginalGuiAccepted=False,originalWholePixelsOrPcmAccepted=False,independentSchedulingAccepted=False,browserAcceptance=False,completeGame=False,nativeEquivalent=False,bindings=bindings,verifierSha256=SHA(Path(__file__).read_bytes()))

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--webgpu-home',type=Path,required=True);p.add_argument('--gles-home',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--check',action='store_true');a=p.parse_args()
    output=a.output.resolve();assert output.is_relative_to(R/'artifacts/th14')or output.is_relative_to(R/'docs/porting');result=evidence(a.webgpu_home,a.gles_home)
    if a.check:assert json.loads(output.read_bytes())==result
    else:output.write_text(json.dumps(result,indent=2)+'\n',encoding='utf8')
    print(json.dumps({k:v for k,v in result.items()if k!='bindings'}))
