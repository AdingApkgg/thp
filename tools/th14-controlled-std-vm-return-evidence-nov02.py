"""Verify a declared original two-thread schedule at an actual STD object VM return."""
from pathlib import Path
import argparse,ast,hashlib,importlib.util,json,struct
R=Path(__file__).resolve().parents[1];SHA=lambda b:hashlib.sha256(b).hexdigest()


def evidence(home):
    home=home.resolve(strict=True);assert home.is_relative_to(R/'artifacts/th14');N=home/'native';bindings={}
    def raw(path):
        p=path.resolve(strict=True);assert p.is_relative_to(R);b=p.read_bytes();bindings[p.relative_to(R).as_posix()]=dict(bytes=len(b),sha256=SHA(b));return b
    def load(path):return json.loads(raw(path))
    run=load(N/'report.json');plan=load(N/'controlled-schedule-plan.json');prepared=load(home/'observer-prepared.json');end=load(home/'process-end.json')
    assert end['exitCode']==1 and end['guardStop']is None and run['childExited']and not run['error']and not run['debugErrors']
    assert run['callbacks']==26000 and run['diagnosticPrefixOnly']and not run['observedForcedReplayEndMenu']
    assert run['threadSchedulingControlled']and run['controlledScheduleComplete']and not run['hardwareBreakpointsOnly']
    assert run['controlledExactMainVmReturnPc']==plan['mainHoldReturnPc']==0x40f2a7
    assert run['controlledExactGlobalsCopyCompletePc']==plan['workerGlobalsCopyCompletePc']==0x456135
    assert run['controlledVmWindowKind']=='stage-object-STD'and plan['originalStdCallPc']==0x40f2a2 and plan['originalVmUpdateTarget']==0x46fe50
    assert run['executableSha256']=='f08e885e28d2e0fc8c579e88034dd7de8f2a648d8f08ce781cf08eadc9ffe353'
    assert run['instructionBytesPatched']==run['rngOrCounterWrites']==0 and not run['inputInjected']
    assert run['gameStateWordWrites']==1 and run['caseInitialization']['attractBitClearOnly']
    assert not run['observerOptions']['normal_vm_window_events']and not run['observerOptions']['worker_active_vm_snapshot']
    source=raw(N/'observer-source.py');assert SHA(source)==run['sourceSha256']==prepared['observerSha256']
    normal=raw(R/'tools/th14-native-campaign-observer-oct25.py');assert SHA(normal)=='ce533a0503163d69a6b93f3a132b950ba96b40cc24bc1f9bbabd9b33b6ca2da7'
    def calls(text,name):return [ast.dump(x,include_attributes=False)for x in ast.walk(ast.parse(text))if isinstance(x,ast.Call)and isinstance(x.func,ast.Attribute)and x.func.attr==name]
    assert calls(source,'WriteProcessMemory')==calls(normal,'WriteProcessMemory')
    assert calls(source,'Wow64SetThreadContext')==calls(normal,'Wow64SetThreadContext')
    preflight=load(home/'scene-call-preflight.json');assert preflight['originalExeSha256']==run['executableSha256']and preflight['actualCallTarget']==0x46fe50
    instructions=load(home/'std-object-loop-static.json');assert any(x['pc']==0x40f29a and x['operands']=='edi, dword ptr [ecx + 0x208]'for x in instructions)
    rows=[json.loads(x)for x in raw(N/'controlled-schedule-events.jsonl').decode().splitlines()]
    assert rows==run['controlledScheduleEvents']and len(rows)==6
    assert[x['event']for x in rows]==['hold-worker-before-original-sleep','suspend-main-after-STD-object-vm-update','resume-worker-to-execute-original-sleep','seed-restored-while-main-held','globals-copy-complete-before-main-resume','resume-main-after-globals-copy']
    assert all(a['hostMonotonicNs']<b['hostMonotonicNs']for a,b in zip(rows,rows[1:]))
    worker,main,worker_resume,restored,copied,main_resume=rows
    assert worker['pc']==0x435b0f and worker['originalInstructionBytes']=='ffd0'and main['pc']==0x40f2a7 and main['originalInstructionBytes']=='837f2800'
    assert worker['stage']==main['stage']==copied['stage']==plan['stage']==3 and worker['threadId']!=main['threadId']
    for hold,resume in [(worker,worker_resume),(main,main_resume)]:
        assert hold['addedSuspendCount']==1 and resume['ownIncrementOnly']and hold['threadId']==resume['threadId']
        assert resume['previousSuspendCount']==hold['previousSuspendCount']+1 and resume['restoredSuspendCount']==hold['previousSuspendCount']
        assert not hold['gameplayValuesWritten']and hold['schedulerInterventionDeclared']
        assert 0<resume['hostMonotonicNs']-hold['hostMonotonicNs']<=plan['maximumHoldSeconds']*1_000_000_000
    assert plan['maximumHoldSeconds']==5 and plan['oneMainSuspendIncrementOnly']and plan['oneWorkerSuspendIncrementOnly']
    blob=bytes.fromhex(main['rawVmHex']);assert len(blob)==0x5cc
    assert main['vmHandle']==struct.unpack_from('<I',blob,0x540)[0]and main['file']==struct.unpack_from('<H',blob,0x36)[0]and main['script']==struct.unpack_from('<H',blob,0x4aa)[0]
    assert main['arrayMembershipFromActualStdLoopProved']and main['vmArrayIndex']>=0 and main['vm']==main['vmArrayBase']+main['vmArrayIndex']*0x5cc
    assert restored['pc']==0x456133 and restored['mainStillHeld']and restored['originalSeedRestoreExecuted']and restored['noSeedOrCounterWriteByObserver']
    assert copied['pc']==0x456135 and copied['originalRepMovsdCompleted']and copied['mainHeldAtPc']==0x40f2a7
    assert not copied['observedValuesProvidedToEngine']and len(bytes.fromhex(copied['globalSnapshotHex']))==0x70
    seeds=[json.loads(x)for x in raw(N/'seed-store-instruction-events.jsonl').decode().splitlines()]
    assert len(seeds)==2 and [x['pc']for x in seeds]==[0x456123,0x456129]
    for row in seeds:
        assert row['readOnly']and not row['providedToEngine']and row['mainThreadRegisters']['eip']==0x40f2a7
    assert(struct.unpack('<4I',bytes.fromhex(seeds[1]['rngHex']))[0]&65535)==(seeds[1]['registers']['eax']&65535)
    transitions=[json.loads(x)for x in raw(N/'transition-events.jsonl').decode().splitlines()]
    sleep=next(x for x in transitions if x['stage']==3 and x['event']=='sleep60-before-call');returned=next(x for x in transitions if x['stage']==3 and x['event']=='sleep60-returned')
    assert sleep['requestedMilliseconds']==60 and returned['hostMonotonicNs']-sleep['hostMonotonicNs']>=60_000_000
    for name,stride in [('selected-state.u32',128),('world-camera.raw',0x124),('hud-score.u32',8)]:assert len(raw(N/name))==26000*stride
    tool=R/'tools/th14-test-storage.py';raw(tool);spec=importlib.util.spec_from_file_location('controlled_std_budget',tool);storage=importlib.util.module_from_spec(spec);spec.loader.exec_module(storage)
    used=storage.check_budget(N,100*1024**3,128*1024**2)
    for p in home.iterdir():
        if p.is_file():used+=p.stat().st_size
        elif p.is_dir()and p!=N:used+=storage.check_budget(p,100*1024**3,128*1024**2)
    assert used<=128*1024**2
    return dict(verifiedControlledOriginalStdVmReturnBoundary=True,diagnosticPrefixOnly=True,capturedCallbacks=26000,stage=3,precedingPlayerCallbacks=main['precedingPlayerCallbacks'],originalMainReturnPc=0x40f2a7,originalVmUpdateCallTarget=0x46fe50,targetVmFile=main['file'],targetVmScript=main['script'],targetVmArrayIndex=main['vmArrayIndex'],targetVmTimer=main['timerCurrent'],targetVmAge=main['ageCurrent'],originalArrayMembershipAtActualReturnProved=True,originalGlobalsCopyCompletePc=0x456135,globalsCopyCompleteHostNs=copied['hostMonotonicNs'],ownSuspendIncrementPerThread=1,workerHoldNanoseconds=worker_resume['hostMonotonicNs']-worker['hostMonotonicNs'],mainHoldNanoseconds=main_resume['hostMonotonicNs']-main['hostMonotonicNs'],originalSleepAndSeedRestoreAndGlobalsCopyExecuted=True,originalInstructionBytesUnmodified=True,gameInstructionRngCounterHealthOrInputWrites=False,nativeObservedValuesProvidedToEngine=False,ordinaryIndependentThreadTimingAcceptance=False,oldInsideVmSeedInterleaveFailureClosed=False,originalNaturalReplayEndAccepted=False,modelEquivalenceAccepted=False,completeGame=False,nativeEquivalent=False,bindings=bindings,verifierSha256=SHA(Path(__file__).read_bytes()))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--case',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--check',action='store_true');a=p.parse_args();out=a.output.resolve();assert out.is_relative_to(R/'artifacts/th14')or out.is_relative_to(R/'docs/porting');result=evidence(a.case)
    if a.check:assert json.loads(out.read_bytes())==result
    else:out.write_text(json.dumps(result,indent=2)+'\n',encoding='utf8')
    print(json.dumps({k:v for k,v in result.items()if k!='bindings'}))
