"""Verify a declared original two-thread schedule at an actual nested ANM instruction boundary."""
from pathlib import Path
import argparse,ast,hashlib,importlib.util,json,struct
R=Path(__file__).resolve().parents[1];SHA=lambda b:hashlib.sha256(b).hexdigest()


def evidence(home):
    home=home.resolve(strict=True);assert home.is_relative_to(R/'artifacts/th14');N=home/'native';bindings={}
    def raw(path):
        p=path.resolve(strict=True);assert p.is_relative_to(R);b=p.read_bytes();bindings[p.relative_to(R).as_posix()]=dict(bytes=len(b),sha256=SHA(b));return b
    def load(path):return json.loads(raw(path))
    run=load(N/'report.json');plan=load(N/'controlled-schedule-plan.json');prepared=load(home/'preflight.json');end=load(home/'process-end.json')
    assert end['observerExitCode']==1 and end['actualMastersZero'] and end['guardStop']is None and run['childExited']and not run['error']and not run['debugErrors']
    assert run['callbacks']==26000 and run['diagnosticPrefixOnly']and not run['observedForcedReplayEndMenu']
    assert run['threadSchedulingControlled']and run['controlledScheduleComplete']and not run['hardwareBreakpointsOnly']
    assert run['controlledExactMainVmReturnPc']==plan['mainHoldPc']==0x4700a3
    assert run['controlledExactGlobalsCopyCompletePc']==plan['workerGlobalsCopyCompletePc']==0x456135
    assert run['controlledVmWindowKind']=='nested-initial-instruction'and plan['originalNestedCallPc']==0x47114b and plan['originalNestedFactory']==0x47ee90 and plan['originalVmUpdateTarget']==0x46fe50
    assert run['executableSha256']=='f08e885e28d2e0fc8c579e88034dd7de8f2a648d8f08ce781cf08eadc9ffe353'
    assert run['instructionBytesPatched']==run['rngOrCounterWrites']==0 and not run['inputInjected']
    assert run['gameStateWordWrites']==1 and run['caseInitialization']['attractBitClearOnly']
    assert not run['observerOptions']['normal_vm_window_events']and not run['observerOptions']['worker_active_vm_snapshot']
    source=raw(N/'observer-source.py');assert SHA(source)==run['sourceSha256']==prepared['sourceSha256']
    normal=raw(R/'tools/th14-native-campaign-observer-oct25.py');assert SHA(normal)=='ce533a0503163d69a6b93f3a132b950ba96b40cc24bc1f9bbabd9b33b6ca2da7'
    def calls(text,name):return [ast.dump(x,include_attributes=False)for x in ast.walk(ast.parse(text))if isinstance(x,ast.Call)and isinstance(x.func,ast.Attribute)and x.func.attr==name]
    assert calls(source,'WriteProcessMemory')==calls(normal,'WriteProcessMemory')
    assert calls(source,'Wow64SetThreadContext')==calls(normal,'Wow64SetThreadContext')
    from importlib import import_module
    image,*_=import_module('th-anm-handlers').handlers(14)
    assert image.read(0x4700a3,3)==bytes.fromhex('0fbf03')
    for pc,target in [(0x47114b,0x47ee90),(0x47ef1e,0x46fe50)]:
        code=image.read(pc,5);assert code[0]==0xe8 and pc+5+struct.unpack_from('<i',code,1)[0]==target
    quiet=load(home/'native-silence-verified.json');assert quiet['verifiedActualNativeMasterLevelsZero']and quiet['nativePid']==run['pid']
    assert quiet['processStartSha256']==SHA(raw(N/'process-start.json'))
    assert len(quiet['samples'])==2 and all(all(x[k]==0 for k in ['musicConfig','effectsConfig','musicMaster','effectsMaster'])for x in quiet['samples'])
    rows=[json.loads(x)for x in raw(N/'controlled-schedule-events.jsonl').decode().splitlines()]
    assert rows==run['controlledScheduleEvents']and len(rows)==6
    assert[x['event']for x in rows]==['hold-worker-before-original-sleep','suspend-main-before-nested-initial-instruction','resume-worker-to-execute-original-sleep','seed-restored-while-main-held','globals-copy-complete-before-main-resume','resume-main-after-globals-copy']
    assert all(a['hostMonotonicNs']<b['hostMonotonicNs']for a,b in zip(rows,rows[1:]))
    worker,main,worker_resume,restored,copied,main_resume=rows
    assert worker['pc']==0x435b0f and worker['originalInstructionBytes']=='ffd0'and main['pc']==0x4700a3 and main['originalInstructionBytes']=='0fbf03'
    assert worker['stage']==main['stage']==copied['stage']==plan['stage']==3 and worker['threadId']!=main['threadId']
    for hold,resume in [(worker,worker_resume),(main,main_resume)]:
        assert hold['addedSuspendCount']==1 and resume['ownIncrementOnly']and hold['threadId']==resume['threadId']
        assert resume['previousSuspendCount']==hold['previousSuspendCount']+1 and resume['restoredSuspendCount']==hold['previousSuspendCount']
        assert not hold['gameplayValuesWritten']and hold['schedulerInterventionDeclared']
        assert 0<resume['hostMonotonicNs']-hold['hostMonotonicNs']<=plan['maximumHoldSeconds']*1_000_000_000
    assert plan['maximumHoldSeconds']==5 and plan['oneMainSuspendIncrementOnly']and plan['oneWorkerSuspendIncrementOnly']
    blob=bytes.fromhex(main['rawVmHex']);assert len(blob)==0x5cc
    assert main['vmHandle']==struct.unpack_from('<I',blob,0x540)[0]and main['file']==struct.unpack_from('<H',blob,0x36)[0]and main['script']==struct.unpack_from('<H',blob,0x4aa)[0]
    assert(main['file'],main['script'],main['vmHandle'])==(2,16,0)
    assert main['nestedFactoryCallChainProved']and main['initialUpdateReturnPc']==0x47ef23 and main['factoryReturnPc']==0x471150
    assert main['scriptBegin']==struct.unpack_from('<I',blob,0x38)[0]and main['instruction']==struct.unpack_from('<I',blob,0x28)[0]
    assert main['scriptOffset']==plan['scriptOffset']==0x9c and main['instruction']==main['scriptBegin']+main['scriptOffset']
    parent=bytes.fromhex(main['parentRawVmHex']);assert len(parent)==0x5cc
    assert(struct.unpack_from('<H',parent,0x36)[0],struct.unpack_from('<H',parent,0x4aa)[0])==(2,17)
    ascii_bytes=raw(home/'input/ascii.anm');assert SHA(ascii_bytes)=='fc1c2295fda07140b475b2ddd45d221920534e4a011c529e76578609d69a9284'
    assert bytes.fromhex(main['instructionHex'])==ascii_bytes[0x2393c+0x9c:0x2393c+0x9c+20]
    assert restored['pc']==0x456133 and restored['mainStillHeld']and restored['originalSeedRestoreExecuted']and restored['noSeedOrCounterWriteByObserver']
    assert copied['pc']==0x456135 and copied['originalRepMovsdCompleted']and copied['mainHeldAtPc']==0x4700a3
    assert not copied['observedValuesProvidedToEngine']and len(bytes.fromhex(copied['globalSnapshotHex']))==0x70
    seeds=[json.loads(x)for x in raw(N/'seed-store-instruction-events.jsonl').decode().splitlines()]
    assert len(seeds)==2 and [x['pc']for x in seeds]==[0x456123,0x456129]
    for row in seeds:
        assert row['readOnly']and not row['providedToEngine']and row['mainThreadRegisters']['eip']==0x4700a3
    assert(struct.unpack('<4I',bytes.fromhex(seeds[1]['rngHex']))[0]&65535)==(seeds[1]['registers']['eax']&65535)
    transitions=[json.loads(x)for x in raw(N/'transition-events.jsonl').decode().splitlines()]
    sleep=next(x for x in transitions if x['stage']==3 and x['event']=='sleep60-before-call');returned=next(x for x in transitions if x['stage']==3 and x['event']=='sleep60-returned')
    assert sleep['requestedMilliseconds']==60 and returned['hostMonotonicNs']-sleep['hostMonotonicNs']>=60_000_000
    for name,stride in [('selected-state.u32',128),('world-camera.raw',0x124),('hud-score.u32',8)]:assert len(raw(N/name))==26000*stride
    tool=R/'tools/th14-test-storage.py';raw(tool);spec=importlib.util.spec_from_file_location('controlled_std_budget',tool);storage=importlib.util.module_from_spec(spec);spec.loader.exec_module(storage)
    used=storage.check_budget(N,100*1024**3,128*1024**2)
    for p in home.iterdir():
        if p.is_file():used+=p.stat().st_size
        elif p.is_dir()and p!=N:
            if p.name=='full-regressions':
                budget=load(p/'plan.json');assert budget['maximumCaseBytes']==128*1024**2 and budget['maximumTotalBytes']==1536*1024**2
                storage.check_budget(p,100*1024**3,budget['maximumTotalBytes'])
                continue # Fifteen separately bounded retained-input cases.
            used+=storage.check_budget(p,100*1024**3,128*1024**2)
    assert used<=128*1024**2
    return dict(verifiedControlledOriginalNestedInstructionBoundary=True,diagnosticPrefixOnly=True,capturedCallbacks=26000,stage=3,precedingPlayerCallbacks=main['precedingPlayerCallbacks'],originalMainPc=0x4700a3,originalVmUpdateCallTarget=0x46fe50,targetVmFile=2,targetVmScript=16,targetScriptOffset=0x9c,targetParentFile=2,targetParentScript=17,originalNestedFactory=0x47ee90,originalGlobalsCopyCompletePc=0x456135,globalsCopyCompleteHostNs=copied['hostMonotonicNs'],mainHeldHostNs=main['hostMonotonicNs'],ownSuspendIncrementPerThread=1,workerHoldNanoseconds=worker_resume['hostMonotonicNs']-worker['hostMonotonicNs'],mainHoldNanoseconds=main_resume['hostMonotonicNs']-main['hostMonotonicNs'],originalSleepAndSeedRestoreAndGlobalsCopyExecuted=True,originalInstructionBytesUnmodified=True,gameInstructionRngCounterHealthOrInputWrites=False,nativeObservedValuesProvidedToEngine=False,ordinaryIndependentThreadTimingAcceptance=False,oldInsideVmSeedInterleaveFailureClosed=False,originalNaturalReplayEndAccepted=False,modelEquivalenceAccepted=False,completeGame=False,nativeEquivalent=False,bindings=bindings,verifierSha256=SHA(Path(__file__).read_bytes()))



if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--case',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--check',action='store_true');a=p.parse_args();out=a.output.resolve();assert out.is_relative_to(R/'artifacts/th14')or out.is_relative_to(R/'docs/porting');result=evidence(a.case)
    if a.check:assert json.loads(out.read_bytes())==result
    else:out.write_text(json.dumps(result,indent=2)+'\n',encoding='utf8')
    print(json.dumps({k:v for k,v in result.items()if k!='bindings'}))
