"""Verify a declared original thread-scheduling experiment at normal ANM entry.

This accepts an explicitly controlled diagnostic case, never ordinary timing.
The observer adds and removes one main-thread suspend increment while the
original worker executes its own Replay restore and globals copy.
"""
from pathlib import Path
import argparse,hashlib,json,struct
ROOT=Path(__file__).resolve().parents[1]
SHA=lambda raw:hashlib.sha256(raw).hexdigest()

def evidence(native):
    native=native.resolve(strict=True);assert native.is_relative_to(ROOT/'artifacts/th14')
    bindings={}
    def raw(path):
        data=path.read_bytes();bindings[path.relative_to(ROOT).as_posix()]=dict(bytes=len(data),sha256=SHA(data));return data
    def load(path):return json.loads(raw(path))
    report=load(native/'report.json');plan=load(native/'controlled-schedule-plan.json')
    assert report['childExited']and not report['error']and not report['observedForcedReplayEndMenu']
    assert report['threadSchedulingControlled']and report['controlledScheduleComplete']and report['hardwareBreakpointsAndDeclaredThreadScheduling']
    assert not report['hardwareBreakpointsOnly']and not report['ordinaryIndependentThreadTimingAcceptance']
    assert report['instructionBytesPatched']==report['rngOrCounterWrites']==0
    assert not report['inputInjected']and report['gameStateWordWrites']==1 and report['caseInitialization']['attractBitClearOnly']
    assert report['controlledExactMainCallbackPc']==plan['mainHoldEntryPc']==0x47e5e0
    assert report['controlledExactGlobalsCopyCompletePc']==plan['workerGlobalsCopyCompletePc']==0x456135
    assert plan['oneMainSuspendIncrementOnly']and not plan['ordinaryIndependentTiming']and not plan['gameInstructionOrRngOrCounterOrHealthWrites']
    assert 0<plan['maximumHoldSeconds']<=2
    captured_source=raw(native/'observer-source.py')
    assert b'SuspendThread'in captured_source and b'ResumeThread'in captured_source and b'0x47e5e0'in captured_source
    exe=raw(native/'work/th14.exe')
    assert SHA(exe)==report['executableSha256']=='f08e885e28d2e0fc8c579e88034dd7de8f2a648d8f08ce781cf08eadc9ffe353'
    pe=struct.unpack_from('<I',exe,0x3c)[0];opt=pe+24;base=struct.unpack_from('<I',exe,opt+28)[0]
    sections=opt+struct.unpack_from('<H',exe,pe+20)[0];section_count=struct.unpack_from('<H',exe,pe+6)[0]
    def instruction(address,size):
        rva=address-base
        for at in range(sections,sections+section_count*40,40):
            virtual_size,virtual_address,length,offset=struct.unpack_from('<IIII',exe,at+8)
            if virtual_address<=rva<virtual_address+max(length,virtual_size):return exe[offset+rva-virtual_address:offset+rva-virtual_address+size]
        raise AssertionError(hex(address))
    # Verify the normal update walk and its VM-update call, rather than a draw
    # wrapper whose PC happens to be nearby. Layer35 drawing uses47e810.
    assert instruction(0x47e5e0,12).hex()=='558bec83e4f881ec94000000'
    assert instruction(0x47e63a,6).hex()=='8bb70882fe00'
    call=instruction(0x47e65b,5);assert call[0]==0xe8 and 0x47e660+struct.unpack_from('<i',call,1)[0]==0x46fe50
    assert instruction(0x456133,8).hex()=='f3a55f5e8be55dc3'
    events=[json.loads(line)for line in raw(native/'controlled-schedule-events.jsonl').decode().splitlines()]
    assert events==report['controlledScheduleEvents']and len(events)==4
    assert [row['event']for row in events]==['suspend-main-before-normal-registry','seed-restored-while-main-held','globals-copy-complete-before-main-resume','resume-main-after-globals-copy']
    hold,seed,copied,resumed=events
    assert hold['pc']==copied['mainHeldAtPc']==0x47e5e0 and seed['pc']==0x456133 and copied['pc']==0x456135
    assert hold['originalInstructionBytes']=='558bec83e4'and hold['instructionBytesUnmodified']and hold['schedulerInterventionDeclared']and not hold['gameplayValuesWritten']
    assert seed['originalSeedRestoreExecuted']and seed['mainStillHeld']and seed['noSeedOrCounterWriteByObserver']
    assert copied['originalRepMovsdCompleted']and not copied['observedValuesProvidedToEngine']
    assert len(bytes.fromhex(copied['globalSnapshotHex']))==0x70
    assert hold['threadId']==resumed['threadId']and seed['threadId']==copied['threadId']and hold['threadId']!=seed['threadId']
    assert hold['addedSuspendCount']==1 and resumed['ownIncrementOnly']
    assert resumed['previousSuspendCount']==hold['previousSuspendCount']+1 and resumed['restoredSuspendCount']==hold['previousSuspendCount']
    assert all(row['stage']==plan['stage']and row['precedingPlayerCallbacks']==hold['precedingPlayerCallbacks']for row in events)
    times=[row['hostMonotonicNs']for row in events];assert times==sorted(set(times))
    assert times[-1]-times[0]<=plan['maximumHoldSeconds']*1_000_000_000
    transition=[json.loads(line)for line in raw(native/'transition-events.jsonl').decode().splitlines()]
    restored=[row for row in transition if row['stage']==plan['stage']and row['event']=='replay-seeds-restored-before-globals-copy']
    assert len(restored)==1;restored=restored[0]
    assert restored['pc']==0x456133 and restored['mainThreadPcAtWorkerEvent']==0x47e5e0
    assert restored['precedingPlayerCallbacks']==hold['precedingPlayerCallbacks']and restored['hostMonotonicNs']==seed['hostMonotonicNs']
    assert restored['controlledMainHoldDeclared']and restored['controlledMainEntryPc']==0x47e5e0
    player_times=raw(native/'player-host-monotonic.u64');callback=hold['precedingPlayerCallbacks']
    assert len(player_times)==report['callbacks']*8 and SHA(player_times)==report['playerHostTimesSha256']
    assert 0<callback<report['callbacks']and struct.unpack_from('<Q',player_times,(callback-1)*8)[0]<times[0]<times[-1]<struct.unpack_from('<Q',player_times,callback*8)[0]
    return dict(verifiedControlledOriginalNormalAnmBoundary=True,diagnosticPrefixOnly=True,
        capturedCallbacks=report['callbacks'],stage=plan['stage'],precedingPlayerCallbacks=callback,
        originalMainHoldPc=0x47e5e0,originalVmUpdateCallTarget=0x46fe50,originalGlobalsCopyCompletePc=0x456135,
        ownSuspendIncrementOnly=True,holdNanoseconds=times[-1]-times[0],originalInstructionBytesUnmodified=True,
        gameInstructionRngCounterHealthOrInputWrites=False,ordinaryIndependentThreadTimingAcceptance=False,
        observerSourceSha256=SHA(captured_source),bindings=bindings,verifierSha256=SHA(Path(__file__).read_bytes()),
        limitations=['Original main-thread timing was deliberately controlled.','One warm Replay transition and a finite prefix; no ordinary menu initialization, natural clear or all-mode acceptance.','Captured RNG and globals bytes are private observations and are not supplied to the independent engine.'],completeGame=False,nativeEquivalent=False)

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--native',type=Path,required=True);parser.add_argument('--output',type=Path,required=True);parser.add_argument('--check',action='store_true')
    args=parser.parse_args();result=evidence(args.native);out=args.output.resolve()
    assert out.is_relative_to(ROOT/'artifacts/th14')or out.is_relative_to(ROOT/'docs/porting')
    if args.check:assert json.loads(out.read_bytes())==result
    else:out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    print(json.dumps({key:result[key]for key in ['verifiedControlledOriginalNormalAnmBoundary','capturedCallbacks','precedingPlayerCallbacks','holdNanoseconds','ordinaryIndependentThreadTimingAcceptance']}))
if __name__=='__main__':main()
