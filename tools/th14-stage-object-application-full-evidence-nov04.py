"""Reject live prefixes and verify finite full Applications of the published 02ecc core."""
from pathlib import Path
import argparse,hashlib,importlib.util,json,shutil
R=Path(__file__).resolve().parents[1];H=R/'artifacts/th14/stage-object-snapshot-readiness-nov04';SHA=lambda b:hashlib.sha256(b).hexdigest()
def evidence(backends):
    bindings={}
    def raw(path):
        path=path.resolve(strict=True);assert path.is_relative_to(R);data=path.read_bytes();bindings[path.relative_to(R).as_posix()]=dict(bytes=len(data),sha256=SHA(data));return data
    def load(path):return json.loads(raw(path))
    ends={b:load(H/('full-'+b)/'process-end.json')for b in backends}
    assert all(e['exitCode']==0 and e['guardStop']is None and e['elapsedSeconds']<=6060 for e in ends.values())
    spec=importlib.util.spec_from_file_location('frozen_stage_evidence',R/'tools/th14-stage-object-snapshot-evidence-nov04.py');verifier=importlib.util.module_from_spec(spec);spec.loader.exec_module(verifier)
    finite,prepared,core,source=verifier.verify();bindings.update(finite['bindings']);raw(R/'tools/th14-stage-object-snapshot-evidence-nov04.py')
    published=load(H/'publication/published.json');assert published['sourceCommit']=='02eccdb19b81d10e5a1a1b9fe2eeb70880ee15eb'
    peer_home=R/'artifacts/th14/reimub-normal-ordinary-application-oct30';sealed_raw=raw(peer_home/'verified.json')
    assert SHA(sealed_raw)=='ba9a17b608155407c4408c6ffa27ae4d4ce554484cf774e996539687fa688627'
    sealed=json.loads(sealed_raw);peer_raw=raw(peer_home/'gles/report.json');peer=json.loads(peer_raw);binding=sealed['bindings'][(peer_home/'gles/report.json').relative_to(R).as_posix()]
    assert len(peer_raw)==binding['bytes']and SHA(peer_raw)==binding['sha256'];results=[]
    for backend in backends:
        home=H/('full-'+backend);plan=load(home/'plan.json');run=load(home/backend/'report.json');bh=R/plan['build'];build=load(bh/'build.json')
        assert run['completed']and not run['error']and run['frames']==122622 and len(run['checks'])==45 and all(x['passed']for x in run['checks'])
        assert run['backend']==plan['backend']==backend and plan['sourceCommit']==published['sourceCommit']and not plan['previousCompleteResultInherited']
        assert run['actualProductionApplicationAndDevices']and run['physicalAudioDevicesOpened']==0 and not run['browserRun']and not run['browserAcceptance']
        assert build['applicationCompiledAgainstFrozenCoreHeaders']and build['coreObjects']==core['objectBindings']and build['coreSourceHashes']==core['sourceHashes']and build['coreWasmSha256']==core['wasmSha256']
        assert SHA(raw(bh/'application.wasm'))==build['wasmSha256']==run['wasmSha256']==plan['wasmSha256']and SHA(raw(bh/'build.json'))==run['buildReportSha256']
        for name,digest in build['newObjects'].items():assert SHA(raw(bh/name))==digest
        for name,binding in build['sourceBindings'].items():
            data=raw(R/name);assert len(data)==binding['bytes']and SHA(data)==binding['sha256']
        assert plan['maximumFrames']==150000 and plan['maximumWallSeconds']==6000 and plan['minimumFreeBytes']==100*1024**3 and plan['maximumOutputBytes']==128*1024**2
        assert raw(home/'scenario.json')==raw(peer_home/'scenario.json')and run['scenarioSha256']==plan['scenarioSha256']==peer['scenarioSha256']
        assert run['actions'][-2]['endFrame']==122562 and run['actions'][-1]['endFrame']==122622
        assert run['actions'][-1]['state'][7]==8 and run['actions'][-1]['state'][9]==91452576
        actual_runner=SHA(raw(home/backend/'run-tool.py'));assert run['toolSha256']==actual_runner
        if plan['runnerSha256']!=actual_runner:
            correction=load(home/'runner-binding-correction.json')
            assert correction['planRunnerSha256ClaimWasStale']and correction['originalPlanPreserved']and not correction['gameplayOrTimingInputsChanged']
            assert correction['originalPlanSha256']==SHA(raw(home/'plan.json'))and correction['originalPlanRunnerSha256']==plan['runnerSha256']
            assert correction['actualRunReportSha256']==SHA(raw(home/backend/'report.json'))and correction['actualFrozenRunnerSha256']==actual_runner
            import subprocess
            published_runner=subprocess.check_output(['git','-C',str(R/'tools/tmp/github-source-release'),'show',published['sourceCommit']+':'+plan['runner']])
            assert published_runner==raw(home/backend/'run-tool.py')and correction['actualRunnerMatchesPublishedSourceCommit']==published['sourceCommit']
        for key in ['actions','checks','rows','initialSave','finalSave','pcmFrames','pcmSha256','pendingAsyncCallbacks','deliveredCallbackSequence','declaredInitialGameTicks','metadataEpochAtFrameZero']:assert run[key]==peer[key],(backend,key)
        assert run['pcmFrames']==89969664 and run['pcmSha256']=='39e9d4e4c65b7dea3b259e7a83189c06b7aaf28d76ef71bf9942a5c005453b54'
        assert len(run['captures'])==len(peer['captures'])==8
        for image,reference in zip(run['captures'],peer['captures'],strict=True):
            for key in ['frame','label','referenceState','liveAnimations']:assert image[key]==reference[key],(backend,image['label'],key)
            actual=raw(home/backend/image['file']);assert SHA(actual)==image['sha256']and actual==raw(peer_home/'gles'/reference['file'])
            assert raw(home/backend/image['liveAnimations']['file'])==raw(peer_home/'gles'/reference['liveAnimations']['file'])
        assert raw(home/'initial-save/replay/th14_01.rpy')==raw(home/backend/'save/replay/th14_01.rpy')==raw(peer_home/'initial-save/replay/th14_01.rpy')
        assert sum(p.stat().st_size for p in home.rglob('*')if p.is_file())<=128*1024**2 and shutil.disk_usage(home).free>=100*1024**3
        results.append(dict(backend=backend,frames=122622,assertions=45,images=8,elapsedSeconds=ends[backend]['elapsedSeconds']))
    return dict(verifiedCurrentStageObjectApplicationsFullReplay=len(backends)==2,verifiedFiniteSingleBackendFullReplay=len(backends)==1,sourceCommit=published['sourceCommit'],coreWasmSha256=core['wasmSha256'],results=results,physicalAudioDevicesOpened=0,historicalReferenceOnly=True,staleRunnerPlanCorrectionDisclosed=True,originalWholePixelsOrPcmAccepted=False,ordinaryOriginalGuiAccepted=False,replaySourceEofObserved=False,independentSchedulingAccepted=False,browserAcceptance=False,completeGame=False,nativeEquivalent=False,bindings=bindings,verifierSha256=SHA(Path(__file__).read_bytes()))
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--backend',choices=['both','gles','webgpu'],required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();result=evidence(['gles','webgpu']if a.backend=='both'else[a.backend]);out=a.output.resolve();assert out.is_relative_to(R/'artifacts/th14')and not out.exists();out.write_bytes((json.dumps(result,indent=2)+'\n').encode());print(json.dumps({k:v for k,v in result.items()if k!='bindings'}),flush=True)
if __name__=='__main__':main()
