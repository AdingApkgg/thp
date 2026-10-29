"""Validate bounded original ANM call edges during the worker Sleep/restore window.

This is diagnostic observation, not a scheduling controller or a fidelity gate.
It does not promote a point inside a VM call to an exact opcode boundary.
"""
from pathlib import Path
import argparse,hashlib,json,struct

R=Path(__file__).resolve().parents[1]
SHA=lambda raw:hashlib.sha256(raw).hexdigest()


def evidence(native):
    native=native.resolve(strict=True);assert native.is_relative_to(R/'artifacts/th14')
    bindings={}
    def raw(path):
        path=path.resolve(strict=True);assert path.is_relative_to(R)
        data=path.read_bytes();bindings[path.relative_to(R).as_posix()]=dict(bytes=len(data),sha256=SHA(data));return data
    def load(path):return json.loads(raw(path))
    run=load(native/'report.json');opt=run['observerOptions']
    assert run['childExited']and not run['error']and run['hardwareBreakpointsOnly']and run['observerTerminationRequested']
    assert not run['observedForcedReplayEndMenu']and run['callbacks']==opt['maximum_callbacks']
    assert run['gameStateWordWrites']==1 and run['caseInitialization']['attractBitClearOnly']and run['rngOrCounterWrites']==run['instructionBytesPatched']==0
    assert not run['inputInjected']and not run['ordinaryMenuReplayInitialization']
    assert opt['normal_vm_window_events']and opt['worker_rng_events']and opt['worker_main_context']and not opt['camera_write_events']
    assert opt['minimum_free_gib']>=100 and opt['maximum_capture_gib']<=.125
    assert run['normalVmWindowReadOnly']and not run['normalVmWindowHasActiveCallAtEnd']and run['normalVmWindowWorkerAtEnd']is None and not run['normalVmReturnEventPendingAtEnd']
    source=raw(native/'observer-source.py');assert SHA(source)==run['sourceSha256']
    assert b'normal-vm-window-events'in source and b'0x47e65b'in source and b'0x47e660'in source
    assert b'SuspendThread('not in source and b'ResumeThread('not in source
    exe=raw(native/'work/th14.exe')
    assert SHA(exe)==run['executableSha256']=='f08e885e28d2e0fc8c579e88034dd7de8f2a648d8f08ce781cf08eadc9ffe353'
    pe=struct.unpack_from('<I',exe,60)[0];opt_at=pe+24;base=struct.unpack_from('<I',exe,opt_at+28)[0]
    table=opt_at+struct.unpack_from('<H',exe,pe+20)[0];count=struct.unpack_from('<H',exe,pe+6)[0]
    def instruction(pc,size):
        for at in range(table,table+40*count,40):
            vs,va,length,offset=struct.unpack_from('<IIII',exe,at+8)
            if va<=pc-base<va+max(vs,length):return exe[offset+pc-base-va:offset+pc-base-va+size]
        raise AssertionError(hex(pc))
    call=instruction(0x47e65b,7)
    assert call[0]==0xe8 and 0x47e660+struct.unpack_from('<i',call,1)[0]==0x46fe50 and call[5:]==b'\x85\xc0'
    assert instruction(0x47e63a,6).hex()=='8bb70882fe00'
    transition=[json.loads(line)for line in raw(native/'transition-events.jsonl').decode().splitlines()]
    assert transition==run['transitionEvents']
    data=raw(native/'normal-vm-window-events.jsonl');assert SHA(data)==run['normalVmWindowEventsSha256']
    rows=[json.loads(line)for line in data.decode().splitlines()];assert 2<=len(rows)==run['normalVmWindowEvents']<=8192
    assert [row['ordinal']for row in rows]==list(range(1,len(rows)+1))
    times=[row['hostMonotonicNs']for row in rows];assert times==sorted(set(times))
    windows=[];used=[];pairs=0;active_restores=0;pending_calls=0;pending_returns=0
    for begin in [row for row in transition if row.get('normalVmCallWindowArmedAtOriginalSleepCall')]:
        assert begin['pc']==0x435b0f and begin['requestedMilliseconds']==60
        restore=next(row for row in transition if row['threadId']==begin['threadId']and row['stage']==begin['stage']and row['pc']==0x456133 and row['hostMonotonicNs']>begin['hostMonotonicNs'])
        assert restore['originalInstructionBytes'].startswith('f3a5')
        subset=[row for row in rows if begin['hostMonotonicNs']<row['hostMonotonicNs']<restore['hostMonotonicNs']]
        active=None;window_pairs=0
        for row in subset:
            assert row['workerThreadId']==begin['threadId']and row['stage']==begin['stage']
            assert row['readOnly']and row['actualOriginalCallEdge']and not row['threadSchedulingControlled']and not row['providedToEngine']
            assert row['threadId']!=row['workerThreadId']
            assert len(bytes.fromhex(row['rngHex']))==16
            if row['pc']==0x47e65b:
                assert row['event']=='normal-vm-before-original-call'and active is None and row['originalInstructionBytes']==call[:5].hex()
                active=row
            else:
                assert row['pc']==0x47e660 and row['event']=='normal-vm-after-original-return'and row['originalInstructionBytes']=='85c0'
                assert active is not None and row['vm']==active['vm']and row['callEntryOrdinal']==active['ordinal']
                active=None;pairs+=1;window_pairs+=1
        result=restore['normalVmCallWindowAtSeedRestore'];context=restore['mainThreadContextAtWorkerEvent']
        assert result['readOnly']and not result['threadSchedulingControlled']and not result['providedToEngine']
        pending_return=bool(active and result['mainPcAtRestore']==0x47e660)
        assert result['activeCall']==active and result['betweenObservedCallAndReturn']==bool(active and not pending_return)
        assert result['mainPcAtRestore']==restore['mainThreadPcAtWorkerEvent']==context['registers']['eip']
        assert result['callInstructionStillPending']==bool(active and result['mainPcAtRestore']==0x47e65b)
        assert result['callReturnEdgeDeliveryPending']==pending_return
        assert result['withinVmMethodAtRestore']==bool(active and result['mainPcAtRestore']not in (0x47e65b,0x47e660))
        assert result['returnWatchStatusBitAtRestore']==bool(context['debugRegisters']['status']&4)
        if pending_return:
            delivered=[row for row in rows if row.get('restoreObservationHostNs')==restore['hostMonotonicNs']]
            assert len(delivered)==1;after=delivered[0]
            assert after['pc']==0x47e660 and after['callEntryOrdinal']==active['ordinal']and after['vm']==active['vm']
            assert after['returnPcAlreadyObservedAtSeedRestore']and after['restoreEventDeliveredEarlier']and after['hostMonotonicNs']>restore['hostMonotonicNs']
            assert after['readOnly']and not after['threadSchedulingControlled']and not after['providedToEngine']
            used.append(after['ordinal']);pairs+=1;window_pairs+=1;pending_returns+=1
        active_restores+=int(result['withinVmMethodAtRestore']);pending_calls+=int(result['callInstructionStillPending'])
        used.extend(row['ordinal']for row in subset)
        windows.append(dict(stage=begin['stage'],precedingPlayerCallbacks=restore['precedingPlayerCallbacks'],
            edges=len(subset)+int(pending_return),completedCalls=window_pairs,activeCallAtRestore=result['withinVmMethodAtRestore'],callInstructionStillPending=result['callInstructionStillPending'],returnEventDeliveredAfterRestore=pending_return,
            activeFile=active['file']if active else None,activeScript=active['script']if active else None,mainPcAtRestore=result['mainPcAtRestore']))
    assert sorted(used)==list(range(1,len(rows)+1))and windows and pairs>0
    return dict(verifiedFinitePassiveNormalVmCallObservation=True,diagnosticPrefixOnly=True,callbacks=run['callbacks'],
        observedCallEdges=len(rows),completedCallPairs=pairs,workerWindows=windows,restoreWithinObservedCallIntervals=active_restores,
        restoreBeforeCallInstructionExecutes=pending_calls,returnEventsDeliveredAfterRestore=pending_returns,threadSchedulingControlled=False,instructionRngOrCounterWrites=False,
        oneDeclaredWarmAttractFlagClear=True,debuggerPausesAffectTiming=True,originalNormalCallPc=0x47e65b,originalNormalReturnPc=0x47e660,
        originalVmUpdateTarget=0x46fe50,exactVmOpcodeOfRestoreAccepted=False,observedValuesProvidedToEngine=False,
        ordinaryMenuInitializationAccepted=False,old80324FailureClosed=False,bindings=bindings,verifierSha256=SHA(Path(__file__).read_bytes()),
        limitations=['Hardware debug events pause the process and affect observed wall time; no explicit thread hold or release is introduced.',
            'Call edges bound a VM invocation, not the exact internal opcode of a concurrent worker restore.',
            'The warm prefix and its observed native values do not establish ordinary menu, whole-game or independently scheduled browser equivalence.'],
        completeGame=False,nativeEquivalent=False)


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--native',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--check',action='store_true');a=p.parse_args()
    target=a.output.resolve();assert target.is_relative_to(R/'artifacts/th14')or target.is_relative_to(R/'docs/porting')
    result=evidence(a.native)
    if a.check:assert json.loads(target.read_bytes())==result
    else:target.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    print(json.dumps({key:value for key,value in result.items()if key!='bindings'}))


if __name__=='__main__':main()
