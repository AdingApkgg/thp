"""Verify actual before/after worker seed-store observations without inferring main-thread order."""
from pathlib import Path
import argparse,ast,hashlib,importlib.util,json,struct
R=Path(__file__).resolve().parents[1];SHA=lambda b:hashlib.sha256(b).hexdigest()


def evidence(home):
    home=home.resolve(strict=True);assert home.is_relative_to(R/'artifacts/th14');N=home/'native';bindings={}
    def raw(path):
        p=path.resolve(strict=True);assert p.is_relative_to(R);b=p.read_bytes();bindings[p.relative_to(R).as_posix()]=dict(bytes=len(b),sha256=SHA(b));return b
    def load(path):return json.loads(raw(path))
    original=load(N/'report.json');terminal=load(home/'process-end.json');plan=load(home/'plan.json');prepared=load(home/'observer-prepared.json')
    assert terminal['exitCode']==1 and terminal['guardStop']is None and original['childExited']and not original['error']and not original['debugErrors']
    assert original['diagnosticPrefixOnly']and original['callbacks']==26000 and not original['observedForcedReplayEndMenu']
    assert original['hardwareBreakpointsOnly']and original['instructionBytesPatched']==original['rngOrCounterWrites']==0
    assert original['executableSha256']=='f08e885e28d2e0fc8c579e88034dd7de8f2a648d8f08ce781cf08eadc9ffe353'
    preflight=load(home/'instruction-preflight.json');assert preflight['actualMachineBytesCheckedBeforeSecondRun']and preflight['originalExeSha256']==original['executableSha256']
    assert [(x['pc'],x['bytes'],x['size'])for x in preflight['instructions']]==[(0x456123,'66a308b54d00',6),(0x456129,'c70514b54d0000000000',10)]
    assert not original['inputInjected']and original['gameStateWordWrites']==1 and original['caseInitialization']['attractBitClearOnly']
    assert original['seedStoreInstructionReadOnly']and original['seedStoreInstructionEvents']==2
    assert original['seedStoreOriginalInstructionBytesPatched']==0 and not original['seedStoreValuesProvidedToEngine']
    assert original['observerOptions']['normal_vm_window_events']and original['observerOptions']['worker_active_vm_snapshot']
    assert plan['normalVmEdgeWindowsEnabled']and plan['diagnosticPrefixOnly']and not plan['expectedNaturalReplayEnd']
    source=raw(R/'tools/th14-stage3-seed-store-observer-v2-nov01.py');base=raw(R/'tools/th14-native-campaign-observer-oct25.py')
    assert original['sourceSha256']==plan['sourceSha256']==prepared['observerSha256']==SHA(source)
    assert SHA(base)==prepared['baseObserverSha256']=='ce533a0503163d69a6b93f3a132b950ba96b40cc24bc1f9bbabd9b33b6ca2da7'
    def calls(text,name):return [ast.dump(x,include_attributes=False)for x in ast.walk(ast.parse(text))if isinstance(x,ast.Call)and isinstance(x.func,ast.Attribute)and x.func.attr==name]
    for name in ['WriteProcessMemory','SuspendThread','ResumeThread']:assert calls(source,name)==calls(base,name)
    content=raw(N/'seed-store-instruction-events.jsonl');assert SHA(content)==original['seedStoreInstructionEventsSha256'];events=[json.loads(x)for x in content.decode().splitlines()]
    assert len(events)==2 and [x['pc']for x in events]==[0x456123,0x456129]and events[0]['hostMonotonicNs']<events[1]['hostMonotonicNs']
    assert events[0]['threadId']==events[1]['threadId']and events[0]['registers']['eax']==events[1]['registers']['eax']
    result=[]
    for row,prefix in zip(events,['66a308b54d00','c70514b54d0000000000'],strict=True):
        assert row['stage']==3 and row['readOnly']and not row['providedToEngine']and not row['threadSchedulingControlled']
        assert row['debuggerPausesAffectTiming']and row['exactEarlierMainRngInstructionOrderNotInferred']
        assert row['originalInstructionBytes'].startswith(prefix)and row['registers']['eip']==row['pc']
        rng=struct.unpack('<4I',bytes.fromhex(row['rngHex']));assert len(bytes.fromhex(row['mainThreadStackHex']))<=64
        snapshot=row['activeVmSnapshot'];assert snapshot['readOnly']and not snapshot['providedToEngine']
        identity=None
        if snapshot['observedCallActive']:
            blob=bytes.fromhex(snapshot['rawVmHex']);assert len(blob)==0x5cc
            identity=dict(handle=struct.unpack_from('<I',blob,0x540)[0],file=struct.unpack_from('<H',blob,0x36)[0],script=struct.unpack_from('<H',blob,0x4aa)[0]);assert identity==snapshot['identity']
            active=row['activeNormalVmCall'];assert active['vm']==snapshot['vm']and active['ordinal']==snapshot['callEntryOrdinal']
            assert snapshot['callIdentityStillMatches']==all(identity[k]==active[k]for k in identity)
        result.append(dict(pc=row['pc'],callback=row['precedingPlayerCallbacks'],mainPcAtWorkerDebugObservation=row['mainThreadRegisters']['eip'],normalVmObservedCallActive=snapshot['observedCallActive'],normalVmIdentity=identity,seedCurrentlyEqualsWorkerEax=(rng[0]&65535)==(row['registers']['eax']&65535),preciseConcurrentMainRngReadOrderAccepted=False))
    transitions=[json.loads(x)for x in raw(N/'transition-events.jsonl').decode().splitlines()];later=[x for x in transitions if x['event']=='replay-seeds-restored-before-globals-copy'and x.get('stage')==3]
    assert len(later)==1 and later[0]['hostMonotonicNs']>events[1]['hostMonotonicNs']
    edges=[json.loads(x)for x in raw(N/'normal-vm-window-events.jsonl').decode().splitlines()];assert edges
    assert len(raw(N/'selected-state.u32'))==26000*128 and len(raw(N/'world-camera.raw'))==26000*0x124 and len(raw(N/'hud-score.u32'))==26000*8
    storage_path=R/'tools/th14-test-storage.py';raw(storage_path);spec=importlib.util.spec_from_file_location('seed_observation_storage',storage_path);storage=importlib.util.module_from_spec(spec);spec.loader.exec_module(storage)
    assert original['privateImmutableStorageCacheUsed']and original['originalGameFilesNotHardlinked']
    used=storage.check_budget(N,100*1024**3,128*1024**2)
    for p in home.iterdir():
        if p.is_file():used+=p.stat().st_size
        elif p.is_dir()and p!=N:used+=storage.check_budget(p,100*1024**3,128*1024**2)
    assert used<=128*1024**2
    return dict(verifiedFiniteBeforeAndAfterOriginalSeedStore=True,diagnosticPrefixOnly=True,callbacks=26000,workerSeedStorePcs=[0x456123,0x456129],workerSeedStoreEvents=2,existingCaptureBudgetHelperUsed=True,observationBudgetBytes=128*1024**2,immutableInputCacheExcludedByExistingCapturePolicy=True,events=result,normalVmWindowEdges=len(edges),later456133ObservationStillRetained=True,originalCodeWrites=0,additionalRngOrCounterOrInputWrites=0,processWriteAndExplicitSuspendResumeCallAstsIdentical=True,debuggerPausesAffectTiming=True,preciseEarlierMainRngReadOrderAccepted=False,nativeValuesProvidedToEngine=False,productionCodeChanged=False,modelEquivalenceAccepted=False,originalNaturalReplayEndAccepted=False,ordinaryOriginalMenuAccepted=False,independentSchedulingAccepted=False,completeGame=False,nativeEquivalent=False,bindings=bindings,verifierSha256=SHA(Path(__file__).read_bytes()))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--case',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--check',action='store_true');a=p.parse_args();out=a.output.resolve();assert out.is_relative_to(R/'artifacts/th14')or out.is_relative_to(R/'docs/porting');result=evidence(a.case)
    if a.check:assert json.loads(out.read_bytes())==result
    else:out.write_text(json.dumps(result,indent=2)+'\n',encoding='utf8')
    print(json.dumps({k:v for k,v in result.items()if k!='bindings'}))
