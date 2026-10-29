"""Verify a declared two-thread schedule at an original normal-VM return.

The original worker executes Sleep60, Replay restore and globals copy itself.
One suspend increment per thread is added and removed; this is diagnostic.
"""
from pathlib import Path
import argparse,hashlib,json,struct
R=Path(__file__).resolve().parents[1]
SHA=lambda raw:hashlib.sha256(raw).hexdigest()


def evidence(native):
    native=native.resolve(strict=True);assert native.is_relative_to(R/'artifacts/th14')
    bindings={}
    def raw(path):
        data=path.read_bytes();bindings[path.relative_to(R).as_posix()]=dict(bytes=len(data),sha256=SHA(data));return data
    def load(path):return json.loads(raw(path))
    run=load(native/'report.json');plan=load(native/'controlled-schedule-plan.json')
    assert run['childExited']and not run['error']and run['callbacks']==33000 and not run['observedForcedReplayEndMenu']
    assert run['threadSchedulingControlled']and run['controlledScheduleComplete']and not run['hardwareBreakpointsOnly']
    assert run['instructionBytesPatched']==run['rngOrCounterWrites']==0 and run['gameStateWordWrites']==1 and run['caseInitialization']['attractBitClearOnly']and not run['inputInjected']
    assert run['controlledExactMainVmReturnPc']==plan['mainHoldReturnPc']==0x47e660
    assert run['controlledExactGlobalsCopyCompletePc']==plan['workerGlobalsCopyCompletePc']==0x456135
    assert (plan['targetVmFile'],plan['targetVmScript'])==(2,17)and plan['boundaryKind']=='after-original-normal-vm-return'
    assert plan['oneMainSuspendIncrementOnly']and plan['oneWorkerSuspendIncrementOnly']and not plan['ordinaryIndependentTiming']and not plan['gameInstructionOrRngOrCounterOrHealthWrites']
    assert 0<plan['maximumHoldSeconds']<=2
    source=raw(native/'observer-source.py');assert SHA(source)==run['sourceSha256']and b'SuspendThread'in source and b'ResumeThread'in source
    exe=raw(native/'work/th14.exe');assert SHA(exe)==run['executableSha256']=='f08e885e28d2e0fc8c579e88034dd7de8f2a648d8f08ce781cf08eadc9ffe353'
    pe=struct.unpack_from('<I',exe,60)[0];opt=pe+24;base=struct.unpack_from('<I',exe,opt+28)[0];table=opt+struct.unpack_from('<H',exe,pe+20)[0]
    def instruction(pc,size):
        for at in range(table,table+40*struct.unpack_from('<H',exe,pe+6)[0],40):
            vs,va,length,offset=struct.unpack_from('<IIII',exe,at+8)
            if va<=pc-base<va+max(vs,length):return exe[offset+pc-base-va:offset+pc-base-va+size]
        raise AssertionError(hex(pc))
    call=instruction(0x47e65b,7);assert call[0]==0xe8 and 0x47e660+struct.unpack_from('<i',call,1)[0]==0x46fe50 and call[5:]==b'\x85\xc0'
    assert instruction(0x456133,8).hex()=='f3a55f5e8be55dc3'and instruction(0x435b0f,2).hex()=='ffd0'
    rows=[json.loads(line)for line in raw(native/'controlled-schedule-events.jsonl').decode().splitlines()]
    assert rows==run['controlledScheduleEvents']and len(rows)==6
    assert [row['event']for row in rows]==['hold-worker-before-original-sleep','suspend-main-after-ascii17-update','resume-worker-to-execute-original-sleep','seed-restored-while-main-held','globals-copy-complete-before-main-resume','resume-main-after-globals-copy']
    worker,main,worker_resume,seed,copied,main_resume=rows
    assert worker['pc']==0x435b0f and worker['originalInstructionBytes']=='ffd0'
    assert main['pc']==copied['mainHeldAtPc']==0x47e660 and main['originalInstructionBytes']=='85c0'and main['instructionBytesUnmodified']
    assert (main['file'],main['script'])==(2,17)and main['vm']and main['vmHandle']
    for hold,resume in [(worker,worker_resume),(main,main_resume)]:
        assert hold['addedSuspendCount']==1 and resume['ownIncrementOnly']and hold['threadId']==resume['threadId']
        assert resume['previousSuspendCount']==hold['previousSuspendCount']+1 and resume['restoredSuspendCount']==hold['previousSuspendCount']
        assert not hold['gameplayValuesWritten']and hold['schedulerInterventionDeclared']
        assert 0<resume['hostMonotonicNs']-hold['hostMonotonicNs']<=plan['maximumHoldSeconds']*1_000_000_000
    assert worker['threadId']==seed['threadId']==copied['threadId']and worker['threadId']!=main['threadId']
    assert all(row['stage']==plan['stage']==3 for row in rows)
    assert len({row['precedingPlayerCallbacks']for row in rows[1:]})==1
    assert seed['pc']==0x456133 and seed['originalSeedRestoreExecuted']and seed['mainStillHeld']and seed['noSeedOrCounterWriteByObserver']
    assert copied['pc']==0x456135 and copied['originalRepMovsdCompleted']and not copied['observedValuesProvidedToEngine']and len(bytes.fromhex(copied['globalSnapshotHex']))==0x70
    times=[row['hostMonotonicNs']for row in rows];assert times==sorted(set(times))and times[3]-times[2]>=60_000_000
    transition=[json.loads(line)for line in raw(native/'transition-events.jsonl').decode().splitlines()]
    actual=next(row for row in transition if row['stage']==3 and row['pc']==0x456133)
    assert actual['hostMonotonicNs']==seed['hostMonotonicNs']and actual['precedingPlayerCallbacks']==main['precedingPlayerCallbacks']
    assert actual['mainThreadPcAtWorkerEvent']==0x47e660 and actual['mainThreadContextAtWorkerEvent']['registers']['esi']==main['vm']
    return dict(verifiedControlledOriginalNormalVmReturnBoundary=True,diagnosticPrefixOnly=True,capturedCallbacks=33000,
        stage=3,precedingPlayerCallbacks=main['precedingPlayerCallbacks'],originalMainReturnPc=0x47e660,originalVmUpdateCallTarget=0x46fe50,
        targetVmFile=2,targetVmScript=17,targetVmTimer=main['timerCurrent'],targetVmAge=main['ageCurrent'],originalGlobalsCopyCompletePc=0x456135,
        workerHoldNanoseconds=times[2]-times[0],mainHoldNanoseconds=times[5]-times[1],ownSuspendIncrementPerThread=1,
        originalSleepAndReplayRestoreAndGlobalsCopyExecuted=True,originalInstructionBytesUnmodified=True,gameInstructionRngCounterHealthOrInputWrites=False,
        ordinaryIndependentThreadTimingAcceptance=False,oldIndependentTimingFailureClosed=False,bindings=bindings,verifierSha256=SHA(Path(__file__).read_bytes()),
        limitations=['Both thread schedules are explicitly controlled; this is not ordinary independent original timing.',
            'The finite warm Replay prefix does not establish a natural clear, original menu initialization, browser equivalence or all-mode fidelity.',
            'Original RNG and globals bytes remain private observations and are never supplied to the game implementation.'],completeGame=False,nativeEquivalent=False)


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--native',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--check',action='store_true');a=p.parse_args()
    out=a.output.resolve();assert out.is_relative_to(R/'artifacts/th14')or out.is_relative_to(R/'docs/porting')
    result=evidence(a.native)
    if a.check:assert json.loads(out.read_bytes())==result
    else:out.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({key:value for key,value in result.items()if key!='bindings'}))


if __name__=='__main__':main()
