"""Observe completed replay RNG/snapshot writes and drain the last real Stage VM return."""
from pathlib import Path
import argparse,hashlib,importlib,json,subprocess,sys
R=Path(__file__).resolve().parents[1];sha=lambda raw:hashlib.sha256(raw).hexdigest()

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);a=p.parse_args();out=a.output.resolve()
    assert out.is_relative_to(R/'artifacts/th14') and not out.exists()
    parent=R/'tools/th14-prepare-replay-rng-stage-object-observer-nov04.py'
    subprocess.run([sys.executable,'-X','utf8',str(parent),'--output',str(out)],cwd=R,check=True,capture_output=True)
    prior=(out/'prepared.json').read_bytes();prepared=json.loads(prior);(out/'stage-prewrite-parent-prepared.json').write_bytes(prior)
    source=out/'observer.py';text=source.read_text(encoding='utf8');assert sha(source.read_bytes())==prepared['observerSha256']
    sys.path.insert(0,str(R/'tools'));img=importlib.import_module('th12-pe').Image('H:/Games/th/14/th14.exe')
    assert sha(img.data)=='f08e885e28d2e0fc8c579e88034dd7de8f2a648d8f08ce781cf08eadc9ffe353'
    signatures={pc:img.read(pc,6).hex() for pc in (0x456115,0x456129,0x456133,0x456135)}
    def replace(old,new):
        nonlocal text
        assert text.count(old)==1,(old,text.count(old));text=text.replace(old,new)
    replace("store_signatures={0x45610f:'66a310b54d00',0x456123:'66a308b54d00',0x456129:'c70514b54d0000000000',0x456133:'f3a5'}",'store_signatures='+repr(signatures))
    replace('store_next={0x45610f:0x456123,0x456123:0x456129,0x456129:0x456133}','store_next={0x456115:0x456129,0x456129:0x456133,0x456133:0x456135}')
    text=text.replace('worker_store_pc.get(tid,0x45610f)','worker_store_pc.get(tid,0x456115)')
    replace("targets.update({0x45610f:'replay-before-gameplay-seed-store',0x456123:'replay-before-script-seed-store',0x456129:'replay-before-gameplay-counter-clear'})", "targets.update({0x456115:'replay-after-gameplay-seed-store',0x456129:'replay-after-script-seed-store',0x456135:'replay-after-globals-copy'})")
    replace("replaySeedWord=struct.unpack('<H',read(regs['esi']-0x12,2))[0]", "replaySeedWord=struct.unpack('<H',read(regs['esi']-0x12-(112 if pc==0x456135 else 0),2))[0]")
    replace('workerInstructionStillPending=True,workerPriorStoresCompleted=[0x45610f,0x456123,0x456129][:list(store_signatures).index(pc)]', 'currentInstructionStillPending=True,completedWritePc={0x456115:0x45610f,0x456129:0x456123,0x456133:0x456129,0x456135:0x456133}[pc],workerPriorStoresCompleted=[0x45610f,0x456123,0x456129,0x456133][:list(store_signatures).index(pc)+1]')
    start=text.index('            if opt.stage_object_vm_window_events and stage_object_vm_window_tid==tid:',text.index("row['restoredReplaySeed']"))
    end=text.index('        transition_events.append(row)',start)
    block=text[start:end]
    # Preserve the old Initialize boundary event at456133, but close the Stage watches only after REP has completed at456135.
    text=text[:start]+text[end:]
    block='\n'.join(line[8:] if line else line for line in block.splitlines())+'\n'
    block=block.replace("    if opt.stage_object_vm_window_events", "    if opt.stage_object_vm_window_events",1)
    marker='                else:\n                    stage_object_vm_window_tid=None;stage_object_vm_active=None'
    # Original block is now dedented by eight columns.
    marker=marker[8:].replace('\n        ','\n') if False else '        else:\n            stage_object_vm_window_tid=None;stage_object_vm_active=None'
    assert block.count(marker)==1
    block=block.replace(marker,"        elif stage_object_vm_active is not None:\n            stage_object_vm_closing_restore=dict(boundary='vm-method-in-progress',hostMonotonicNs=row['hostMonotonicNs'])\n"+marker)
    helper="def finish_stage_object_window(row,tid):\n    global stage_object_vm_window_tid,stage_object_vm_active,stage_object_vm_closing_restore\n"+block+'\n'
    replace('def replay_store_snapshot(pc,tid,b):',helper+'def replay_store_snapshot(pc,tid,b):')
    marker="    replay_store_events.append(row)"
    extra="""    if pc==0x456135:
        row['mainThreadPcAtWorkerEvent']=main_regs['eip']
        row['mainThreadContextAtWorkerEvent']=dict(registers=main_regs,debugRegisters=dict(status=struct.unpack_from('<I',main,20)[0]))
        finish_stage_object_window(row,tid)
        pending_worker_rng.discard(tid)
"""
    replace(marker,extra+marker)
    replace('            pending_worker_rng.discard(tid)\n','')
    old="""                closing_call=isinstance(stage_object_vm_closing_restore,dict)
                row.update(returnPcAlreadyObservedAtSeedRestore=not closing_call,callEntryPendingAtSeedRestore=closing_call,restoreEventDeliveredEarlier=True,
                    restoreObservationHostNs=stage_object_vm_closing_restore['hostMonotonicNs']if closing_call else stage_object_vm_closing_restore)"""
    new="""                closing_dict=isinstance(stage_object_vm_closing_restore,dict)
                closing_kind=stage_object_vm_closing_restore['boundary']if closing_dict else'return-edge-pending'
                row.update(returnPcAlreadyObservedAtSeedRestore=closing_kind=='return-edge-pending',callEntryPendingAtSeedRestore=closing_kind=='call-entry-pending',
                    vmMethodInProgressAtSnapshotCompletion=closing_kind=='vm-method-in-progress',restoreEventDeliveredEarlier=True,
                    restoreObservationHostNs=stage_object_vm_closing_restore['hostMonotonicNs']if closing_dict else stage_object_vm_closing_restore)"""
    replace(old,new)
    replace("report['stageObjectVmCallEntryPendingAtEnd']=isinstance(stage_object_vm_closing_restore,dict)","report['stageObjectVmCallEntryPendingAtEnd']=isinstance(stage_object_vm_closing_restore,dict)and stage_object_vm_closing_restore['boundary']=='call-entry-pending'\n    report['stageObjectVmMethodInProgressAtEnd']=isinstance(stage_object_vm_closing_restore,dict)and stage_object_vm_closing_restore['boundary']=='vm-method-in-progress'")
    replace('replayRngStoreAllInstructionsObservedBeforeExecution=True','replayRngStoreAllInstructionsObservedBeforeExecution=False,replayRngWritesObservedAfterCompletion=True,replayGlobalsCopyCompletionObserved=True')
    compile(text,str(source),'exec');assert 'SuspendThread'not in text and 'ResumeThread'not in text;source.write_bytes(text.encode())
    prepared.update(observerSha256=sha(text.encode()),preparerSha256=sha(Path(__file__).read_bytes()),completionParentPreparerSha256=sha(parent.read_bytes()),workerExecutionBreakpointPcs=list(signatures),completedWritePcs=[0x45610f,0x456123,0x456129,0x456133],finalActiveVmReturnWatchRetained=True,replaySeedAddressAdjustedAfterRepAdvance=True)
    (out/'prepared.json').write_bytes((json.dumps(prepared,indent=2)+'\n').encode());print(json.dumps(prepared))
if __name__=='__main__':main()
