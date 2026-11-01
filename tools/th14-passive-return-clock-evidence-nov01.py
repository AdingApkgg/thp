"""Independently recompute the retained 48000-callback passive-return comparison."""
from pathlib import Path
import argparse,gzip,hashlib,importlib.util,json,struct
R=Path(__file__).resolve().parents[1]
S=lambda b:hashlib.sha256(b).hexdigest()

def evidence(home):
    home=home.resolve(strict=True);assert home.is_relative_to(R/'artifacts/th14');bindings={}
    def raw(path):
        path=path.resolve(strict=True);assert path.is_relative_to(R)
        data=path.read_bytes();bindings[path.relative_to(R).as_posix()]=dict(bytes=len(data),sha256=S(data));return data
    def load(path):return json.loads(raw(path))
    def module(name,path):
        raw(path);spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
    native=home/'native';proof=load(home/'return-observation-verified.json')
    observation=module('passive_return',R/'tools/th14-passive-vm-return-evidence-nov01.py').evidence(native)
    assert proof==observation;bindings.update(proof['bindings'])
    vm=module('retained_vm_decoder',R/'tools/th14-passive-entry-clock-evidence-oct30.py')
    combat=module('retained_combat_decoder',R/'tools/th14-combat-pool-readonly-v3-oct25.py')
    before=home/'current-compare';after=home/'observed-return-current';b=load(before/'model/report.json');a=load(after/'model/report.json')
    for case,expected_exit in [(before,1),(after,0)]:
        end=load(case/'process-end.json');assert end['exitCode']==expected_exit and end['guardStop']is None
    assert a['wasmSha256']==b['wasmSha256']=='7c4c9066a9e8a86fb7db162638ad2d50d73441dad90d2418e5b5aa2b0e84b0ee'
    build_path=R/'artifacts/th14/reimub-normal-construction-current-oct30/observer/observer-build.json';build=load(build_path)
    assert S(raw(build_path.parent/'observer.wasm'))==build['wasmSha256']==a['wasmSha256']
    for name in ['GameSession.cpp','GameBattle.cpp','AnmManager.cpp']:
        key='th12_web/cpp/game/'+name;assert S(raw(R/'runtimes/th12'/key))==build['sourceHashes'][key]
    for name in ['GameSession.hpp','AnmManager.hpp']:
        key='th12_web/cpp/game/'+name;assert S(raw(R/'runtimes/th12'/key))==build['headerHashes'][key]
    plan=load(after/'plan.json');assert not plan['productionGameplayModified']and not plan['originalProcessesStarted']and plan['physicalAudioDevicesOpened']==0
    assert plan['maximumObservationBytes']<=128*1024**2 and plan['minimumFreeBytes']>=100*1024**3
    assert plan['producerSha256']==S(raw(R/'tools/th14-passive-return-clock-compare-nov01.py'))
    clock=load(after/'return-clock-observation.json');boundary=a['normalVmBoundaryObservation']
    assert clock=={k:v for k,v in boundary.items()if k!='modelClock'}
    assert clock['callback']==31049 and clock['originalPc']==0x47e660 and clock['file']==5 and clock['script']==4
    assert clock['passiveOriginalReturnPcActuallyObserved']and not clock['normalRegistryEntryProjection']
    assert clock['nativeReportSha256']==S(raw(native/'report.json'))and clock['passiveProofSha256']==S(raw(home/'return-observation-verified.json'))
    events=[json.loads(line)for line in raw(native/'normal-vm-window-events.jsonl').decode().splitlines()]
    calls=[e for e in events if e['precedingPlayerCallbacks']==31049 and e['pc']==0x47e65b]
    assert [(x['file'],x['script'])for x in calls]==[(9,35),(9,36),(5,2),(5,3),(5,4)]
    assert boundary['modelClock']==dict(delivered=1,failed=0,ownVmPollSlot=len(calls)+1,visits=len(calls)+1)
    base=raw(R/'tools/th14-compare-native-campaign.mjs');script=raw(after/'compare.mjs')
    assert plan['comparisonBaseSha256']==S(base)and plan['comparisonGeneratedSha256']==S(script)==a['comparisonToolSha256']
    insertion="""const passiveReturnClock=JSON.parse(read(resolve(import.meta.dirname,'return-clock-observation.json')));
assert(prefix===48000 && schedulerPhases==='observed' && !normalBoundary && !options.has('normal-vm-boundary-observation'));
assert.equal(sha(read(resolve(nativeHome,'report.json'))),passiveReturnClock.nativeReportSha256);
normalVmBoundary=passiveReturnClock;
assert.equal(c.observed_normal_vm_clock(normalVmBoundary.callback,baseNow+BigInt(normalVmBoundary.readyNs)-playerOrigin,normalVmBoundary.file,normalVmBoundary.script),1);
"""
    expected=base.decode().replace('\r\n','\n').replace("const root=resolve(import.meta.dirname,'..')","const root="+json.dumps(R.as_posix()))
    expected=expected.replace('let normalVmBoundary=null;','let normalVmBoundary=null;\n'+insertion).replace("normalVmBoundary.retainedBaseline?'controlled-vm-return-baseline':'controlled-vm-return'","normalVmBoundary.retainedBaseline?'controlled-vm-return-baseline':'passive-observed-vm-return'")
    assert script.decode().replace('\r\n','\n')==expected
    assert b['hostNormalBoundaryMode']=='none'and b['differenceCounts']=={'21':16951,'22':2201}and b['firstDifference']['index']==31049
    assert a['hostNormalBoundaryMode']=='passive-observed-vm-return'and a['allRaw32ByteIdentical']and not a['differenceCounts']
    native_state=raw(native/'selected-state.u32');assert len(native_state)==48000*128
    camera=raw(native/'world-camera.raw');expected_camera=b''.join(camera[i*0x124+o:i*0x124+o+4]for i in range(48000)for o in [*range(0,88,4),0x104,0x108,0x10c])
    hud=raw(native/'hud-score.u32');assert len(hud)==48000*8
    index=load(native/'combat-pool-index.json');by_callback={x['callback']:x for x in index['snapshots']}
    vm_rows=0;combat_counts=[]
    for case,report in [(before,b),(after,a)]:
        model=case/'model';assert report['completed']and report['callbacks']==48000 and report['diagnosticPrefixOnly']
        assert report['intactOriginalReplay']and report['stageHeaderInputAndFpsRetainedExactly']and report['noPerFrameStateOverrides']
        assert not report['actualGpuOrAudio']and not report['completeGame']and not report['nativeEquivalent']
        state=raw(model/'selected-state.u32');assert len(state)==len(native_state)and S(state)==report['selectedSha256']and S(native_state)==report['nativeSelectedSha256']
        counts={}
        for i in range(48000*32):
            if state[i*4:i*4+4]!=native_state[i*4:i*4+4]:counts[str(i%32)]=counts.get(str(i%32),0)+1
        assert counts==report['differenceCounts']
        assert raw(model/'portable-camera.u32')==expected_camera and raw(model/'portable-hud.u32')==hud
        live=load(model/'live-report.json');assert live['allLiveValuesEqual']==(case==after)
        if case==after:
            for row in live['snapshots']:
                frame=row['frame'];nr=load(native/f'live-vms-callback-{frame}.json')['rows'];pr=load(model/f'portable-live-{frame}.json')
                addresses={struct.unpack_from('<I',bytes.fromhex(n['rawVmHex']),0x570)[0]:n['handle']for n in nr}
                assert [vm.vm_values(n,addresses)for n in nr]==pr;vm_rows+=len(nr)
        cp=load(model/'combat-snapshots.json');assert len(cp['snapshots'])==432
        differences=0
        for checkpoint in cp['snapshots']:
            callback=checkpoint['callback'];ref=by_callback[callback];compressed=raw(native/'combat-pools'/ref['file']);assert S(compressed)==ref['sha256']
            original=json.loads(gzip.decompress(compressed));portable=load(model/f'combat-{callback}.json')
            assert original['callback']==portable['callback']==callback and original['stage']==portable['stage']and original['stageFrame']==portable['stageFrame']
            for family,fields in combat.SCHEMA.items():
                n=[combat.selected(bytes.fromhex(x['rawHex']),fields,x['slot'])for x in original['original'][family]];p=portable['rows'][family]
                assert len(n)==len(p)
                differences+=sum(x!=y for nr,pr in zip(n,p)for x,y in zip(nr,pr))
                assert all(len(row)==len(fields)for row in p)
        assert differences==len(cp['differences'])==(599 if case==before else 0);combat_counts.append(differences)
        native_alloc=[json.loads(s)for s in raw(native/'allocation-events.jsonl').decode().splitlines()]
        native_alloc=[n for n in native_alloc if n['precedingPlayerCallbacks']<1000]
        portable_alloc=load(model/'portable-allocations-initial-through-1000.json');assert len(native_alloc)==len(portable_alloc)==2870
        assert [[n[k]for k in ['handle','file','script']]for n in native_alloc]==[[n[k]for k in ['handle','file','script']]for n in portable_alloc]
    assert vm_rows==666
    return dict(verifiedFinitePassiveVmReturnClockComparison=True,callbacks=48000,nativeCallEdges=4380,nativeCallPairs=2190,
        observedOriginalReturnPc=0x47e660,returnDeliveredAfterSeedRestore=True,targetNormalVmOrdinal=5,modelClockDeliveredExactlyOnce=True,
        baselineStrictFailureRetained=True,baselineSeedWordDifferences=16951,baselineCallCountWordDifferences=2201,
        combatCheckpoints=432,combatDifferingFieldsBefore=599,combatDifferingFieldsAfter=0,selected32AllCallbacksEqual=True,
        vmSnapshots=3,vmRowsRecomputed=vm_rows,vmFieldsPerRow=303,cameraWordsPerCallback=25,hudWordsPerCallback=2,initialPublications=2870,
        existingProductionNormalVmReturnPollUsed=True,productionGameplayModified=False,productionWasmChanged=False,
        onlyObservedHostClockAndCallBoundaryProvided=True,normalRegistryEntryTimeProjection=False,
        originalDebuggerPausesAffectTiming=True,independentThreadSchedulingAccepted=False,ordinaryMenuInitializationAccepted=False,
        old80324FailureClosed=False,completeGame=False,nativeEquivalent=False,bindings=bindings,verifierSha256=S(Path(__file__).read_bytes()))

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--case',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--check',action='store_true');a=p.parse_args()
    target=a.output.resolve();assert target.is_relative_to(R/'artifacts/th14')or target.is_relative_to(R/'docs/porting')
    result=evidence(a.case)
    if a.check:assert json.loads(target.read_bytes())==result
    else:target.write_text(json.dumps(result,indent=2)+'\n',encoding='utf8')
    print(json.dumps({k:v for k,v in result.items()if k!='bindings'}))
if __name__=='__main__':main()
