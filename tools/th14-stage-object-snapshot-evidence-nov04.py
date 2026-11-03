"""Verify finite Stage object/snapshot readiness evidence, optionally integrate only seven reviewed files."""
from pathlib import Path
import argparse,datetime,hashlib,json
R=Path(__file__).resolve().parents[1];H=R/'artifacts/th14/stage-object-snapshot-readiness-nov04';sha=lambda raw:hashlib.sha256(raw).hexdigest()

def verify():
    bindings={}
    def read(path):
        raw=path.read_bytes();bindings[path.relative_to(R).as_posix()]=dict(bytes=len(raw),sha256=sha(raw));return raw
    def load(path):return json.loads(read(path))
    prep=load(H/'prepared.json');corepath=H/'build/ordinary/observer-build.json';core=load(corepath);source=Path(core['sourceSnapshotRoot'])
    assert core['all141CoreObjectsRecompiled']and len(core['objectBindings'])==141
    assert sha(read(corepath.parent/'observer.wasm'))==core['wasmSha256']
    for row in core['objectBindings']:assert sha(read(Path(row['path'])))==row['sha256']
    for name,digest in {**core['sourceHashes'],**core['headerHashes']}.items():assert sha(read(source/name))==digest
    assert len(prep['productionChanges'])==7 and prep['preparerSha256']==sha(read(R/'tools/th14-prepare-stage-object-snapshot-readiness-nov04.py'))
    stageprep=load(R/prep['parentStageObjectPreparation']);assert sha(read(R/prep['parentStageObjectPreparation']))==prep['parentPreparationSha256']
    assert stageprep['preparerSha256']==sha(read(R/'tools/th14-prepare-stage-object-boundaries-nov04.py'))
    resume=load(H/'snapshot-check/snapshot-session.json');failed=load(H/'snapshot-failure-check/snapshot-session-failure.json');control=load(H/'snapshot-session-control/observer-build.json')
    assert control['objectBindings']==core['objectBindings']and control['controlledHostReadinessFixture']
    assert resume['verifiedControlledProductionSessionSnapshotResume']and failed['verifiedControlledProductionSessionSnapshotFailure']
    assert resume['wasmSha256']==failed['wasmSha256']==control['wasmSha256']==sha(read(H/'snapshot-session-control/observer.wasm'))
    for path,digest in control['fixtureDependencyHashes'].items():assert sha(read(Path(path)))==digest
    for name,report in [('check',resume),('failure-check',failed)]:assert report['driverSha256']==sha(read(R/('tools/th14-replay-snapshot-session-'+name+'-nov04.mjs')))
    assert [x[0]for x in resume['events']]==[0,2,3]and len(resume['events'])==3
    assert resume['snapshotReadiness'][1]>=resume['snapshotReadiness'][0]+2 and resume['snapshotReadiness'][3]>0
    assert failed['completedSeedStores']==3 and failed['snapshotCopyFailed']and failed['errorPropagatedToGameSessionAndBattle']
    assert failed['snapshotReadiness'][1]==0 and failed['controlledFailureAt']>=failed['snapshotReadiness'][0]+2
    assert not resume['earlyHudSceneOrTimelineRequests']and not failed['earlyHudSceneOrTimelineRequests']
    protocol=load(H/'stage-object-protocol-v2/verified.json');assert protocol['verifiedRealStageObjectVmFailurePropagation']and len(protocol['cases'])==2
    assert protocol['fixtureSha256']==sha(read(R/'runtimes/th12/th12_web/tests/cpp/th14-stage-object-boundary-fixture-nov04.cpp'))
    checks=load(H/'api-checks/report.json');stagechecks=load(H/'stage-syntax/report.json')
    assert checks['passed']and len(checks['cases'])==12 and len(checks['negativeControls'])==7 and all(x['rejected']for x in checks['negativeControls'])
    assert stagechecks['passed']and len(stagechecks['cases'])==4
    regress=load(H/'current-modes/end.json');assert regress['casesCompleted']==17 and regress['strictV4Passes']==regress['newModelRuns']==16
    callbacks=0
    for case in regress['cases']:
        if not case['strictV4Passed']:
            assert case['key']=='reimub-easy'and case['notRunOnCurrentCore']and case['reportedDebugExceptions']==12;continue
        raw=load(H/'current-modes'/case['key']/'raw-verified.json');assert raw['verifiedFiniteEvidence']and raw['wasmSha256']==core['wasmSha256']and raw['callbacks']==case['callbacks']
        for path,binding in raw['bindings'].items():
            data=read(R/path);assert len(data)==binding['bytes']and sha(data)==binding['sha256']
        callbacks+=case['callbacks']
    assert callbacks==1379760
    witness=load(H/'public-observed-run/raw-verified.json');assert witness['verifiedFiniteEvidence']and witness['callbacks']==35000 and witness['vm303Rows']==1057 and witness['combatCheckpoints']==393
    for path,binding in witness['bindings'].items():
        data=read(R/path);assert len(data)==binding['bytes']and sha(data)==binding['sha256']
    contract=load(H/'public-observed-run/scene.json');assert contract['passed']and contract['observedVmInputContract']['verifiedObservedVmInputContract']
    app=load(H/'gles-two-stage/report.json');appbuild=load(H/'gles-build-v2/build.json');reference=R/'artifacts/th14/overlay-vm-boundaries-v2-nov04/gles-two-stage';ref=load(reference/'report.json')
    assert app['completed']and not app['error']and app['frames']==app['applicationTicks']==2289 and len(app['checks'])==27 and all(x['passed']for x in app['checks'])
    assert app['physicalAudioDevicesOpened']==0 and app['glCalls']['SDL_GL_SwapWindow']==2289
    assert appbuild['applicationCompiledAgainstFrozenCoreHeaders']and appbuild['coreObjects']==core['objectBindings']and appbuild['coreWasmSha256']==core['wasmSha256']
    assert app['wasmSha256']==appbuild['wasmSha256']==sha(read(H/'gles-build-v2/application.wasm'))
    assert appbuild['toolSha256']==sha(read(R/'tools/th14-build-frozen-native-application-nov04.py'))
    for path,binding in appbuild['sourceBindings'].items():
        data=read(R/path);assert len(data)==binding['bytes']and sha(data)==binding['sha256']
    assert app['captures']==ref['captures']and(app['pcmFrames'],app['pcmSha256'])==(ref['pcmFrames'],ref['pcmSha256'])
    for image in app['captures']:assert read(H/'gles-two-stage'/image['file'])==read(reference/image['file'])
    browser=load(H/'browser-build/build.json');inputs=load(H/'browser-build/compile-inputs.json')
    assert browser['compiled']and browser['sourceUnits']==browser['compiledUnits']==146 and not browser['browserRun']and not browser['browserAcceptance']
    assert browser['wasmSha256']==sha(read(H/'browser-build/th14-sdl.wasm'))and browser['loaderSha256']==sha(read(H/'browser-build/th14-sdl.mjs'))
    assert inputs['frozenCoreBuildSha256']==sha(read(corepath))and inputs['frozenCoreWasmSha256']==core['wasmSha256']
    assert inputs['toolSha256']==sha(read(R/'tools/th14-build-frozen-stage-object-browser-nov04.py'))
    for name,digest in {**core['sourceHashes'],**core['headerHashes']}.items():assert inputs['sourceBindings'][name]['sha256']==digest
    old=load(R/'artifacts/th14/replay-rng-template-trace-nov04/comparison-stage-snapshot/model/report.json');oldend=load(R/'artifacts/th14/replay-rng-template-trace-nov04/comparison-stage-snapshot/end.json')
    assert not oldend['strictAndIndependentPassed']and old['wasmSha256']==core['wasmSha256']and old['differenceCounts']=={'21':4137,'22':283,'26':1}
    context=load(R/'artifacts/th14/current-rng-context-nov04/causal-verified.json');native=load(R/'artifacts/th14/replay-rng-stage-object-trace-nov04/stage-object-observations-v2.json')
    assert context['verifiedCurrentReadOnlyOutgoingObjectRngContext']and not context['oldFailureClosed']and native['verifiedOriginalStageObjectObservations']
    protected={'runtimes/th12/th12_web/cpp/game/ResourceCrypt.cpp':'a291010053963e25dadef2be15ddb3c217110cd2377fc495402ef375150f8c45','artifacts/th14/vm-return-worker-oct29/work-state.json':'2236db52bee27439486e69216333cd88ddc27d1dcc28233f87bacdcaadc1f33c'}
    for name,digest in protected.items():assert sha(read(R/name))==digest
    result=dict(verifiedStageObjectSnapshotReadiness=True,coreWasmSha256=core['wasmSha256'],freshCoreObjects=141,finiteDefaultCases=16,finiteDefaultCallbacks=callbacks,witnessedNormalVmCallbacks=35000,witnessedVmRows=1057,witnessedCombatCheckpoints=393,sharedTitleSyntaxChecks=16,negativeInputControls=7,stageBoundaryFailureControls=2,separateSnapshotResumeAndFailureControls=2,applicationFrames=2289,applicationChecks=27,byteIdenticalReferenceImages=2,offlinePcmFrames=app['pcmFrames'],physicalAudioDevicesOpened=0,browserCompiledUnits=146,browserWasmSha256=browser['wasmSha256'],browserAcceptance=False,oldFailureDifferences=old['differenceCounts'],oldFailureClosed=False,nativeEquivalent=False,completeGame=False,ordinaryIndependentThreadTimingAccepted=False,initialReplayStillSynchronous=True,defaultReadinessImmediate=True,protectedFiles=protected,bindings=bindings,verifierSha256=sha(Path(__file__).read_bytes()))
    return result,prep,core,source

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--integrate',action='store_true');p.add_argument('--output',type=Path);a=p.parse_args()
    report,prep,core,source=verify()
    if a.integrate:
        assert not(H/'integration.json').exists()
        for row in prep['productionChanges']:
            assert sha((R/'runtimes/th12'/row['path']).read_bytes())==row['beforeSha256']
            assert sha((source/row['path']).read_bytes())==row['afterSha256']
        for row in prep['productionChanges']:
            path=R/'runtimes/th12'/row['path'];backup=H/'before-integration'/row['path'];backup.parent.mkdir(parents=True,exist_ok=True);backup.write_bytes(path.read_bytes());path.write_bytes((source/row['path']).read_bytes())
            assert sha(path.read_bytes())==row['afterSha256']
        production=H/'production-core';production.mkdir();(production/'observer.wasm').write_bytes((H/'build/ordinary/observer.wasm').read_bytes())
        build=dict(core,productionIntegrated=True,rootProductionSourcesModified=True,sourcePublishedCommit=None,sourcePublicationPending=True,parentGameplayCorePublishedCommit='8c946994f36827bfe1bba6c8eb9b6c7706425f30',productionChangedGameFiles=[x['path']for x in prep['productionChanges']],candidateBuildReport='artifacts/th14/stage-object-snapshot-readiness-nov04/build/ordinary/observer-build.json')
        (production/'observer-build.json').write_bytes((json.dumps(build,indent=2)+'\n').encode())
        (H/'integration.json').write_bytes((json.dumps(dict(integrated=True,changedFiles=prep['productionChanges'],evidence=report,utc=datetime.datetime.now(datetime.timezone.utc).isoformat()),indent=2)+'\n').encode())
    integrated=(H/'integration.json').exists()
    if integrated:
        for row in prep['productionChanges']:assert sha((R/'runtimes/th12'/row['path']).read_bytes())==row['afterSha256']
    report['productionIntegrated']=integrated
    if a.output:
        output=a.output.resolve();assert output.is_relative_to(R)and not output.exists();output.parent.mkdir(parents=True,exist_ok=True);output.write_bytes((json.dumps(report,indent=2)+'\n').encode())
    print(json.dumps({k:v for k,v in report.items()if k not in('bindings','protectedFiles')}),flush=True)
if __name__=='__main__':main()
