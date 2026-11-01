"""Recompute the controlled initialization boundary and two full retained regressions."""
from pathlib import Path
import argparse,gzip,hashlib,importlib.util,json,struct
R=Path(__file__).resolve().parents[1];SHA=lambda raw:hashlib.sha256(raw).hexdigest()

def evidence(home):
    home=home.resolve(strict=True);assert home.is_relative_to(R/'artifacts/th14');bindings={}
    def raw(path):
        path=path.resolve(strict=True);assert path.is_relative_to(R)
        data=path.read_bytes();bindings[path.relative_to(R).as_posix()]=dict(bytes=len(data),sha256=SHA(data));return data
    def load(path):return json.loads(raw(path))
    def module(name,path):
        raw(path);spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
    vm=module('initialization_vm_decoder',R/'tools/th14-passive-entry-clock-evidence-oct30.py')
    combat=module('initialization_combat_decoder',R/'tools/th14-combat-pool-readonly-v3-oct25.py')
    n=load(home/'native/report.json');plan=load(home/'native/controlled-schedule-plan.json')
    assert n['childExited']and not n['error']and n['callbacks']==15500 and not n['observedForcedReplayEndMenu']
    assert n['threadSchedulingControlled']and n['controlledScheduleComplete']and not n['hardwareBreakpointsOnly']
    assert n['gameStateWordWrites']==1 and n['caseInitialization']['attractBitClearOnly']
    assert n['instructionBytesPatched']==n['rngOrCounterWrites']==0 and not n['inputInjected']
    assert n['sourceSha256']==SHA(raw(home/'native/observer-source.py'))==SHA(raw(R/'tools/th14-native-initialization-boundary-observer-nov01.py'))
    assert plan['stage']==2 and plan['mainHoldCallPc']==0x47ef1e and plan['workerGlobalsCopyCompletePc']==0x456135
    assert(plan['targetVmFile'],plan['targetVmScript'],plan['targetParentVmFile'],plan['targetParentVmScript'])==(2,16,2,17)
    assert plan['boundaryKind']=='before-original-attached-child-initial-update'and not plan['ordinaryIndependentTiming']
    assert plan['oneMainSuspendIncrementOnly']and plan['oneWorkerSuspendIncrementOnly']and plan['maximumHoldSeconds']==2
    events=[json.loads(line)for line in raw(home/'native/controlled-schedule-events.jsonl').decode().splitlines()]
    assert events==n['controlledScheduleEvents']and len(events)==6
    assert [x['event']for x in events]==['hold-worker-before-original-sleep','suspend-main-before-ascii16-initial-update','resume-worker-to-execute-original-sleep','seed-restored-while-main-held','globals-copy-complete-before-main-resume','resume-main-after-globals-copy']
    worker,main,resume_worker,seed,copied,resume_main=events
    assert worker['pc']==0x435b0f and main['pc']==copied['mainHeldAtPc']==0x47ef1e and copied['pc']==0x456135
    assert(main['file'],main['script'],main['parentFile'],main['parentScript'])==(2,16,2,17)
    child=bytes.fromhex(main['vmRawHex']);parent=bytes.fromhex(main['parentRawHex']);assert len(child)==len(parent)==0x5cc
    assert struct.unpack_from('<I',child,0x594)[0]==main['parentVm']and struct.unpack_from('<I',child,0x540)[0]==main['vmHandle']==0
    assert struct.unpack_from('<H',child,0x36)[0]==struct.unpack_from('<H',parent,0x36)[0]==2
    assert struct.unpack_from('<H',child,0x4aa)[0]==16 and struct.unpack_from('<H',parent,0x4aa)[0]==17
    assert main['timerCurrent']==main['ageCurrent']==0 and main['precedingPlayerCallbacks']==13919
    times=[x['hostMonotonicNs']for x in events];assert times==sorted(set(times))and times[3]-times[2]>=60000000
    for hold,resume in[(worker,resume_worker),(main,resume_main)]:
        assert hold['threadId']==resume['threadId']and hold['addedSuspendCount']==1 and resume['ownIncrementOnly']
        assert resume['previousSuspendCount']==hold['previousSuspendCount']+1 and resume['restoredSuspendCount']==hold['previousSuspendCount']
        assert 0<resume['hostMonotonicNs']-hold['hostMonotonicNs']<=2000000000
    assert worker['threadId']!=main['threadId']and worker['threadId']==seed['threadId']==copied['threadId']
    assert seed['originalSeedRestoreExecuted']and seed['mainStillHeld']and seed['noSeedOrCounterWriteByObserver']
    assert copied['originalRepMovsdCompleted']and not copied['observedValuesProvidedToEngine']
    exe=raw(home/'native/work/th14.exe');assert SHA(exe)=='f08e885e28d2e0fc8c579e88034dd7de8f2a648d8f08ce781cf08eadc9ffe353'
    pe=struct.unpack_from('<I',exe,60)[0];opt=pe+24;base=struct.unpack_from('<I',exe,opt+28)[0];table=opt+struct.unpack_from('<H',exe,pe+20)[0]
    def instruction(pc,size):
        for at in range(table,table+40*struct.unpack_from('<H',exe,pe+6)[0],40):
            vs,va,length,offset=struct.unpack_from('<IIII',exe,at+8)
            if va<=pc-base<va+max(vs,length):return exe[offset+pc-base-va:offset+pc-base-va+size]
        raise AssertionError(hex(pc))
    call=instruction(0x47ef1e,5);assert call.hex()==main['originalInstructionBytes']=='e82d0fffff'
    assert 0x47ef23+struct.unpack_from('<i',call,1)[0]==0x46fe50 and instruction(0x47ef18,6).hex()=='899f94050000'
    assert instruction(0x456133,8).hex()=='f3a55f5e8be55dc3'
    transition=[json.loads(line)for line in raw(home/'native/transition-events.jsonl').decode().splitlines()]
    restored=next(x for x in transition if x['stage']==2 and x['pc']==0x456133)
    assert restored['hostMonotonicNs']==seed['hostMonotonicNs']and restored['mainThreadPcAtWorkerEvent']==0x47ef1e
    for name in ['retained','candidate-no-fine-clock']:
        report=load(home/name/'report.json');state=raw(home/name/'selected-state.u32')
        original=raw(home/'native/selected-state.u32');different=[i for i in range(15500)if state[i*128:(i+1)*128]!=original[i*128:(i+1)*128]]
        assert different==list(range(13919,15500))and report['differenceCounts']=={'21':1581}and not report['allRaw32ByteIdentical']
        for i in different:
            assert state[i*128:i*128+84]==original[i*128:i*128+84]and state[i*128+88:(i+1)*128]==original[i*128+88:(i+1)*128]
    build=load(home/'production-core/observer-build.json');rebuild=load(home/'public-rebuild-v2/observer-build.json')
    wasm=raw(home/'production-core/observer.wasm');assert SHA(wasm)==build['wasmSha256']==rebuild['wasmSha256']==SHA(raw(home/'public-rebuild-v2/observer.wasm'))
    assert build['all141ObjectsRecompiledForChangedClassLayout']and rebuild['all141ObjectsRecompiledForChangedClassLayout']
    assert len(build['objectBindings'])==len(rebuild['objectBindings'])==141
    assert build['sourceHashes']==rebuild['sourceHashes']and build['headerHashes']==rebuild['headerHashes']
    assert rebuild['buildToolSha256']==SHA(raw(R/'tools/th14-build-initialization-boundary-observer-nov01.py'))
    for path,digest in rebuild['fixtureDependencyHashes'].items():assert SHA(raw(Path(path)))==digest
    for compiled in [build,rebuild]:
        for row in compiled['objectBindings']:assert SHA(raw(Path(row['path'])))==row['sha256']
    for kind in ['sourceHashes','headerHashes']:
        for name,digest in build[kind].items():
            p=R/'runtimes/th12'/name
            if name=='th12_web/cpp/game/ResourceCrypt.cpp':p=R/'tools/tmp/github-source-release/runtimes/th12'/name
            assert SHA(raw(p))==digest and SHA(raw(home/'production-core/source'/name))==digest
    assert SHA(raw(R/'runtimes/th12/th12_web/cpp/game/ResourceCrypt.cpp'))=='a291010053963e25dadef2be15ddb3c217110cd2377fc495402ef375150f8c45'
    fixture=R/'runtimes/th12/th12_web/tests/cpp/th14-initialization-clock-fixture-nov01.cpp'
    assert SHA(raw(fixture))==rebuild['expandedFixtureSha256']
    def verify_run(native,model,end_path,count,vm_rows,checkpoints):
        nr=load(native/'report.json');report=load(model/'report.json');end=load(end_path)
        assert nr['childExited']and not nr['error']and nr['callbacks']==count
        assert nr['instructionBytesPatched']==nr['rngOrCounterWrites']==0 and nr['gameStateWordWrites']==1 and not nr['inputInjected']
        assert end['strictPassed']and end['exitCode']==0 and end['guardStop']is None
        assert report['callbacks']==report['nativeCallbacks']==count and report['allRaw32ByteIdentical']and not report['differenceCounts']
        assert report['wasmSha256']==SHA(wasm)and report['noPerFrameStateOverrides']and report['noNativePublicationValuesProvidedToEngine']
        selected=raw(native/'selected-state.u32');assert len(selected)==count*128 and selected==raw(model/'selected-state.u32')
        camera=raw(native/'world-camera.raw');assert len(camera)==count*0x124
        expected=b''.join(camera[i*0x124+o:i*0x124+o+4]for i in range(count)for o in [*range(0,88,4),0x104,0x108,0x10c])
        assert raw(model/'portable-camera.u32')==expected and raw(native/'hud-score.u32')==raw(model/'portable-hud.u32')
        live=load(model/'live-report.json');assert live['allLiveValuesEqual']and live['comparedValues']==303
        rows=0
        for snapshot in live['snapshots']:
            at=snapshot['frame'];original=load(native/f'live-vms-callback-{at}.json')['rows'];portable=load(model/f'portable-live-{at}.json')
            handles={struct.unpack_from('<I',bytes.fromhex(v['rawVmHex']),0x570)[0]:v['handle']for v in original}
            assert [vm.vm_values(v,handles)for v in original]==portable;rows+=len(original)
        assert rows==vm_rows
        cp=load(model/'combat-snapshots.json');idx=load(native/'combat-pool-index.json');lookup={x['callback']:x for x in idx['snapshots']}
        assert len(cp['snapshots'])==checkpoints and not cp['differences']and idx['fields']==json.loads(json.dumps(combat.SCHEMA))
        for checkpoint in cp['snapshots']:
            at=checkpoint['callback'];binding=lookup[at];compressed=raw(native/'combat-pools'/binding['file']);assert SHA(compressed)==binding['sha256']
            original=json.loads(gzip.decompress(compressed));portable=load(model/f'combat-{at}.json')
            assert(original['callback'],original['stage'],original['stageFrame'])==(portable['callback'],portable['stage'],portable['stageFrame'])
            for family,fields in combat.SCHEMA.items():assert [combat.selected(bytes.fromhex(obj['rawHex']),fields,obj['slot'])for obj in original['original'][family]]==portable['rows'][family]
        allocations=[json.loads(line)for line in raw(native/'allocation-events.jsonl').decode().splitlines()]
        allocations=[x for x in allocations if x['precedingPlayerCallbacks']<1000];portable=load(model/'portable-allocations-initial-through-1000.json')
        assert [[x[k]for k in ['handle','file','script']]for x in allocations]==[[x[k]for k in ['handle','file','script']]for x in portable]
        return dict(callbacks=count,vmRows=rows,vmFieldsPerRow=303,combatCheckpoints=checkpoints,initialPublications=len(allocations),selectedCameraHudVmAndCombatExact=True)
    controlled=verify_run(home/'native',home/'production-controlled',home/'production-controlled-process-end.json',15500,224,143)
    point=load(home/'production-controlled/report.json')['initializationBoundaryObservation'];assert point['callback']==13919 and point['readyNs']==copied['hostMonotonicNs']and point['delivered']==1 and point['failed']==0
    driver=raw(home/'compare-observed.mjs');assert SHA(driver)==load(home/'production-controlled/report.json')['comparisonToolSha256']
    expected=raw(R/'tools/th14-compare-native-campaign.mjs').decode().replace("const root=resolve(import.meta.dirname,'..')","const root='H:/code/thp'")
    declared=dict(callback=13919,readyNs=copied['hostMonotonicNs'],nativeCallPc=0x47ef1e,stage=2,child=[2,16],parent=[2,17])
    expected=expected.replace('const combatSnapshots=[],combatDifferences=[]',"const initializationPoint="+json.dumps(declared)+";assert.equal(c.observed_initialization_clock(initializationPoint.callback,baseNow+BigInt(initializationPoint.readyNs)-playerOrigin),1);\nconst combatSnapshots=[],combatDifferences=[]")
    expected=expected.replace("write(resolve(out,'report.json'),JSON.stringify(report,null,2)","report.initializationBoundaryObservation={...initializationPoint,delivered:c.observed_initialization_clock_state(0),failed:c.observed_initialization_clock_state(1)};assert.equal(report.initializationBoundaryObservation.delivered,1);assert.equal(report.initializationBoundaryObservation.failed,0);\nwrite(resolve(out,'report.json'),JSON.stringify(report,null,2)")
    assert driver.decode().replace('\r\n','\n')==expected.replace('\r\n','\n'),'All original strict assertions must remain intact'
    marisa=verify_run(R/'artifacts/th14/marisaa-easy-passive-full-nov01/native',home/'production-marisaa-natural',home/'production-marisaa-natural-process-end.json',80594,680,907)
    old_plan=load(R/'artifacts/th14/reimub-normal-construction-current-oct30/plan.json')
    reimu=verify_run(R/old_plan['native'],home/'production-reimub-full',home/'production-reimub-full-process-end.json',122537,2586,1294)
    controls=load(home/'loader-controls/verified.json');assert controls['actualProductionLoaderChecks']==24 and controls['allPassed']and controls['wasmSha256']==SHA(raw(home/'loader-controls/controls.wasm'))
    raw(R/'runtimes/th12/th12_web/tests/cpp/th14-stage-initialization-boundary-nov01.cpp');raw(home/'loader-controls/check.mjs')
    frame_controls=[]
    native_frame=R/'artifacts/th14/native-frame-readback-oct28/inline-ecl-worker-boundaries-v2'
    frame_report=load(native_frame/'report.json');pixels=raw(native_frame/frame_report['readback']['file']);assert len(pixels)==1228800
    decoder=module('initialization_frame_decoder',R/'tools/th14-native-title-live-compare-oct27.py')
    native_rows=load(native_frame/'live-vms-before-readback.json')['rows']
    handles={struct.unpack_from('<I',bytes.fromhex(v['rawVmHex']),0x570)[0]:v['handle']for v in native_rows}
    expected_rows=[decoder.native_words(v,handles)[1]for v in native_rows];assert len(expected_rows)==334
    for backend in ['gles','webgpu']:
        strict=load(home/f'strict-{backend}.json');assert strict['strictAllSelectedStateLiveVmsAndPixelsEqual']and strict['noPixelToleranceOrFpsNormalization']
        for name,binding in strict['bindings'].items():assert SHA(raw(R/name))==binding['sha256']
        application=load(home/f'{backend}-build/build.json');run=load(home/f'frame-{backend}/run/report.json')
        assert application['coreBuildSha256']==SHA(raw(home/'production-core/observer-build.json'))and application['coreSourceHashes']==build['sourceHashes']
        assert application['wasmSha256']==run['wasmSha256']==SHA(raw(home/f'{backend}-build/application.wasm'))
        for name,binding in application['sourceBindings'].items():assert SHA(raw(R/name))==binding['sha256']
        assert run['completed']and not run['error']and run['frames']==2270 and len(run['checks'])==7 and all(x['passed']for x in run['checks'])
        assert run['physicalAudioDevicesOpened']==0 and not run['browserAcceptance']
        capture=run['captures'][0];assert raw(home/f'frame-{backend}/run'/capture['file'])==pixels
        live=load(home/f'frame-{backend}/run'/capture['liveAnimations']['file']);assert live['rows']==expected_rows and live['complete']and live['comparedValues']==303
        profile=load(home/f'frame-{backend}/availability.json');assert run['observedResourceAvailabilityControl']['profile']==profile
        assert profile['nativeReport']['sha256']==SHA(raw(native_frame/'report.json'))and profile['noVmRngPixelOrGameStateOverrides']and not profile['productionSchedulingChanged']
        frame_controls.append(dict(backend=backend,applicationFrames=2270,assertions=7,fullBgraBytesEqual=1228800,vmRows=334,vmFields=303,bothRngExact=True,observedResourceAvailabilityDeclared=True,independentSchedulingAccepted=False))
    return dict(verifiedControlledInitializationBoundary=True,originalStage=2,originalCallback=13919,originalMainPc='0x47ef1e',childFileScript=[2,16],parentFileScript=[2,17],originalSeedRestoreExecuted=True,originalInstructionRngCounterInputWrites=False,declaredAttractBitClearCount=1,ownSuspendIncrementPerThread=1,maximumHoldSeconds=2,oldCoreRngMismatchRows=1581,candidateWithoutFineClockMismatchRows=1581,controlled=controlled,fullMarisaaNaturalRegression=marisa,fullReimubRegression=reimu,loaderBoundaryChecks=24,actualApplicationFrameControls=frame_controls,allCoreObjectsRecompiled=141,publicRebuildWasmByteIdentical=True,productionGameplayModified=True,independentThreadSchedulingAccepted=False,old80324FailureClosed=False,wholeOriginalPixelsOrPcmAccepted=False,allModesAccepted=False,completeGame=False,nativeEquivalent=False,bindings=bindings,verifierSha256=SHA(Path(__file__).read_bytes()))

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--case',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--check',action='store_true');args=p.parse_args()
    target=args.output.resolve();assert target.is_relative_to(R/'artifacts/th14')or target.is_relative_to(R/'docs/porting');result=evidence(args.case)
    if args.check:assert json.loads(target.read_bytes())==result
    else:target.write_text(json.dumps(result,indent=2)+'\n',encoding='utf8')
    print(json.dumps({k:v for k,v in result.items()if k!='bindings'}))
if __name__=='__main__':main()
