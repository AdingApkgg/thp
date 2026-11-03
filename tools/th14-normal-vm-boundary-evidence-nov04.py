"""Verify integrated VM boundaries, witnessed original inputs and current builds."""
from pathlib import Path
import argparse, collections, hashlib, importlib.util, json, struct
R=Path(__file__).resolve().parents[1];H=R/'artifacts/th14/normal-vm-boundaries-v2-nov04'
sha=lambda raw:hashlib.sha256(raw).hexdigest()


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--check',action='store_true')
    p.add_argument('--output',type=Path,default=R/'docs/porting/th14-normal-vm-boundary-nov04.json');a=p.parse_args();bindings={}
    def read(path):
        raw=path.read_bytes();bindings[path.relative_to(R).as_posix()]=dict(bytes=len(raw),sha256=sha(raw));return raw
    def load(path):return json.loads(read(path))
    def recheck(rows):
        for name,binding in rows.items():
            raw=read(R/name);assert len(raw)==binding['bytes']and sha(raw)==binding['sha256'],name
    integrated=load(H/'integration.json');assert integrated['integrated']and len(integrated['changedFiles'])==6
    assert integrated['integrationToolSha256']==sha(read(R/'tools/th14-integrate-normal-vm-boundaries-nov04.py'))
    recheck(integrated['bindings'])
    prepared=load(H/'prepared.json')
    assert prepared['preparerSha256']==sha(read(R/'tools/th14-prepare-normal-vm-boundaries-nov04.py'))
    for row in integrated['changedFiles']:assert sha(read(R/'runtimes/th12'/row['path']))==row['afterSha256']
    ordinary=load(H/'build/ordinary/observer-build.json');typed=load(H/'build/typed/observer-build.json')
    assert ordinary['objectBindings']==typed['objectBindings']and ordinary['sourceHashes']==typed['sourceHashes']and ordinary['headerHashes']==typed['headerHashes']
    for name,build in [('ordinary',ordinary),('typed',typed)]:
        assert build['wasmSha256']==sha(read(H/'build'/name/'observer.wasm'))
        assert len(build['objectBindings'])==141 and build['all141CoreObjectsRecompiled']and build['engineObjectsReused']==0
        assert build['buildToolSha256']==sha(read(R/'tools/th14-build-normal-vm-boundaries-nov04.py'))
        for row in build['objectBindings']:assert sha(read(Path(row['path'])))==row['sha256']
        for path,digest in build['fixtureDependencyHashes'].items():assert sha(read(Path(path)))==digest
        for path,digest in {**build['sourceHashes'],**build['headerHashes']}.items():assert sha(read(Path(build['sourceSnapshotRoot'])/path))==digest
    assert ordinary['wasmSha256']==integrated['coreWasmSha256']==sha(read(H/'production-core/observer.wasm'))
    proof=load(H/'observed-inputs.json')
    spec=importlib.util.spec_from_file_location('contract',R/'tools/th14-normal-vm-input-contract-nov04.py');contract=importlib.util.module_from_spec(spec);spec.loader.exec_module(contract)
    observed_contract=contract.validate(R/proof['native'],H/'public-observed-run/model',H/'build/typed/observer-build.json',H/'observed-inputs.json')
    observed=load(H/'public-observed-run/raw-verified.json');recheck(observed['bindings'])
    assert observed['verifiedFiniteEvidence']and observed['callbacks']==35000 and observed['vm303Rows']==1057 and observed['combatCheckpoints']==393
    assert observed['allSelected32Equal']and observed['allCamera25Equal']and observed['allHud2Equal']
    for name in('exceptions','timing','scene'):assert load(H/'public-observed-run'/(name+'.json'))['passed']
    scene=load(H/'public-observed-run/scene.json')
    assert scene['observedVmInputContract']==observed_contract
    assert scene['verifierSha256']==sha(read(R/'tools/th14-verify-observed-normal-vm-scene-nov04.py'))
    assert scene['baseVerifierSha256']==sha(read(R/'tools/th14-verify-native-scene-boundaries-nov03.py'))
    protocol=load(H/'protocol-controls-v2/verified.json')
    assert protocol['verifiedBeforeCallAndAfterReturnFailurePropagation']and protocol['toolSha256']==sha(read(R/'tools/th14-check-normal-vm-boundary-protocol-nov04.py'))
    for point,name in enumerate(('before-call','after-return')):
        row=load(H/'protocol-controls-v2'/name/'model/protocol.json')
        assert row['point']==point and row['failed']==1 and row['delivered']==0 and row['callback']==14082 and 'loading at normal VM boundary'in row['error']
    checks=load(H/'api-checks/report.json')
    assert checks['passed']and len(checks['cases'])==12 and len(checks['negativeControls'])==7 and all(x['rejected']for x in checks['negativeControls'])
    assert checks['toolSha256']==sha(read(R/'tools/th14-check-normal-vm-boundaries-nov04.py'))
    regressions=load(H/'current-modes/end.json');modes=[];total=0
    for row in regressions['cases']:
        if not row['strictV4Passed']:
            assert row['key']=='reimub-easy'and row['notRunOnCurrentCore']and row['reportedDebugExceptions']==12;continue
        raw=load(H/'current-modes'/row['key']/'raw-verified.json');recheck(raw['bindings'])
        assert raw['verifiedFiniteEvidence']and raw['wasmSha256']==ordinary['wasmSha256']and raw['callbacks']==row['callbacks']
        assert row['newModelRun']and row['model']['exitCode']==row['verifier']['exitCode']==0
        for name in('exceptions','timing','scene'):assert load(H/'current-modes'/row['key']/(name+'.json'))['passed']
        modes.append(dict(key=row['key'],selection=row['selection'],callbacks=row['callbacks'],vmRows=raw['vm303Rows'],combatCheckpoints=raw['combatCheckpoints']))
        total+=row['callbacks']
    assert len(modes)==16 and total==1379760
    app_build=load(H/'gles-build/build.json');app=load(H/'gles-two-stage/report.json')
    reference_home=R/'artifacts/th14/replay-cadence-reset-nov04/gles-two-stage';reference=load(reference_home/'report.json')
    assert app_build['coreWasmSha256']==ordinary['wasmSha256']and app_build['coreObjects']==ordinary['objectBindings']
    assert app['wasmSha256']==app_build['wasmSha256']==sha(read(H/'gles-build/application.wasm'))
    assert app['completed']and not app['error']and app['frames']==app['applicationTicks']==2289
    assert len(app['checks'])==27 and all(x['passed']for x in app['checks'])and app['glCalls']['SDL_GL_SwapWindow']==2289
    assert app['physicalAudioDevicesOpened']==0 and len(app['captures'])==len(reference['captures'])==2
    for actual,expected in zip(app['captures'],reference['captures'],strict=True):
        assert {key:actual[key]for key in expected}==expected
    assert(app['pcmFrames'],app['pcmSha256'])==(reference['pcmFrames'],reference['pcmSha256'])
    for image in app['captures']:assert read(H/'gles-two-stage'/image['file'])==read(reference_home/image['file'])
    recheck(app_build['sourceBindings'])
    assert app_build['toolSha256']==sha(read(R/'tools/th14-build-native-application.py'))
    assert app['toolSha256']==sha(read(R/'tools/th14-native-application-process-host-oct27.py'))
    browser=load(H/'browser-build/build.json')
    assert browser['compiled']and browser['sourceUnits']==browser['compiledUnits']==146 and browser['reusedObjectCount']==0
    assert not browser['browserRun']and not browser['browserAcceptance']
    assert browser['wasmSha256']==sha(read(H/'browser-build/th14-sdl.wasm'))and browser['loaderSha256']==sha(read(H/'browser-build/th14-sdl.mjs'))
    assert browser['toolSha256']==sha(read(R/'tools/th14-build-webgpu-reuse-worker-nov03.py'))
    for name,digest in {**ordinary['sourceHashes'],**ordinary['headerHashes']}.items():assert browser['sourceBindings'][name]['sha256']==digest,name
    for row in integrated['changedFiles']:assert browser['sourceBindings'][row['path']]['sha256']==row['afterSha256']
    # A third existing native record has no proven VM identity at its stores.
    # Independently retain its actual current-core failure, without clock guesses.
    third=R/'artifacts/th14/replay-rng-template-trace-nov04';third_end=load(third/'comparison-vm-boundary/end.json')
    third_model=load(third/'comparison-vm-boundary/model/report.json');third_native=load(third/'native/report.json')
    assert third_end['model']['exitCode']==third_end['verifier']['exitCode']==1 and not third_end['strictAndIndependentPassed']
    assert not third_native['debugErrors']and third_native['callbacks']==35000 and third_native['childExited']
    assert third_model['wasmSha256']==ordinary['wasmSha256']and third_model['noPerFrameStateOverrides']
    left=read(third/'native/selected-state.u32');right=read(third/'comparison-vm-boundary/model/selected-state.u32')
    assert len(left)==len(right)==35000*128
    differences=collections.Counter()
    for original,portable in zip(struct.iter_unpack('<32I',left),struct.iter_unpack('<32I',right),strict=True):
        for word,(x,y)in enumerate(zip(original,portable,strict=True)):
            if x!=y:differences[str(word)]+=1
    assert dict(differences)==third_model['differenceCounts']=={'21':4137,'22':283,'26':1}
    for name,digest in integrated['protectedFiles'].items():assert sha(read(R/name))==digest
    for name in('th14-observed-normal-vm-inputs-nov04.py','th14-normal-vm-input-contract-nov04.py',
        'th14-prepare-normal-vm-boundary-driver-nov04.py','th14-verify-observed-normal-vm-campaign-nov04.py',
        'th14-prepare-replay-rng-store-vm-observer-nov04.py','th14-prepare-replay-rng-template-observer-nov04.py'):read(R/'tools'/name)
    result=dict(verifiedIntegratedNormalVmBoundaries=True,changedGameFiles=6,all141CoreObjectsFresh=True,
        ordinaryWasmSha256=ordinary['wasmSha256'],typedFixtureWasmSha256=typed['wasmSha256'],
        originalObservedVmBoundaryCallbacks=35000,observedVmRows303=1057,observedCombatCheckpoints=393,
        originalVmCallReturnPc=[0x47e65b,0x47e660],sameStoppedEventTimestampAliasNs=[611900,867800],
        canonicalInitializeTimeRetained=True,minimumWaitChanged=False,normalVmFunctionPointersWrapped=False,
        nativeRngOrStateValuesProvidedToEngine=False,observedInputContract=observed_contract,
        defaultFiniteRecords=16,defaultFiniteCallbacks=total,defaultFiniteModes=modes,
        knownOriginalExceptionRecordRejected=True,sharedTitleSyntaxChecks=12,negativeInputControls=7,vmBoundaryFailureControls=2,
        applicationFrames=2289,applicationChecks=27,applicationPresents=2289,physicalAudioDevicesOpened=0,
        frozenReferenceImagesMatched=2,offlinePcmFrames=app['pcmFrames'],offlinePcmMatchesFrozenReference=True,
        browserCompiledUnits=146,browserWasmSha256=browser['wasmSha256'],browserAcceptance=False,
        thirdNativeRecordCurrentCoreDifferences=dict(differences),thirdNativeRecordStrictlyAccepted=False,
        old40kUnprovenChildClockHypothesisAccepted=False,old36826FailureClosed=False,
        ordinaryIndependentThreadTimingAccepted=False,initialReplayStillSynchronous=True,defaultBrowserAllStoresReady=True,
        completeGame=False,nativeEquivalent=False,bindings=bindings,verifierSha256=sha(Path(__file__).read_bytes()))
    output=a.output.resolve();assert output.is_relative_to(R/'docs/porting')or output.is_relative_to(H)
    data=(json.dumps(result,indent=2)+'\n').encode()
    if a.check:assert output.read_bytes()==data
    else:output.write_bytes(data)
    print(json.dumps({key:value for key,value in result.items()if key not in('bindings','defaultFiniteModes','observedInputContract')}),flush=True)


if __name__=='__main__':main()
