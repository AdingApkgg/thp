"""Freeze a read-only original observer at each next-stage replay RNG store."""
from pathlib import Path
import argparse, hashlib, json

R=Path(__file__).resolve().parents[1]
BASE='ce533a0503163d69a6b93f3a132b950ba96b40cc24bc1f9bbabd9b33b6ca2da7'
sha=lambda raw:hashlib.sha256(raw).hexdigest()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();out=args.output.resolve()
    assert out.is_relative_to(R/'artifacts/th14') and not out.exists()
    base=R/'tools/th14-native-campaign-observer-oct25.py';raw=base.read_bytes();assert sha(raw)==BASE
    text=raw.decode().replace('\r\n','\n')

    def replace(old,new):
        nonlocal text
        assert text.count(old)==1,(old,text.count(old));text=text.replace(old,new)

    replace('root=Path(__file__).resolve().parents[1]',f'root=Path({str(R)!r})')
    replace('opt=parser.parse_args()',
            'opt=parser.parse_args()\nassert opt.worker_rng_events and opt.worker_main_context and not opt.normal_vm_window_events')
    replace('pending_worker_rng=set()',
            'pending_worker_rng=set()\nworker_store_pc={};replay_store_events=[]\n'+
            "store_signatures={0x45610f:'66a310b54d00',0x456123:'66a308b54d00',0x456129:'c70514b54d0000000000',0x456133:'f3a5'}\n"+
            'store_next={0x45610f:0x456123,0x456123:0x456129,0x456129:0x456133}\n')
    replace("targets.update({0x40dae9:'controller-camera-published'",
            "targets.update({0x45610f:'replay-before-gameplay-seed-store',0x456123:'replay-before-script-seed-store',0x456129:'replay-before-gameplay-counter-clear'})\n"+
            "targets.update({0x40dae9:'controller-camera-published'")
    replace('if first_snapshot is not None and not trace_publications and tid!=pi.tid and tid in pending_worker_rng:addresses[2]=0x456133',
            'if first_snapshot is not None and not trace_publications and tid!=pi.tid and tid in pending_worker_rng:addresses[2]=worker_store_pc.get(tid,0x45610f)')
    helper='''def replay_store_snapshot(pc,tid,b):
    assert tid!=pi.tid and tid in pending_worker_rng and worker_store_pc.get(tid,0x45610f)==pc
    signature=store_signatures[pc];assert read(pc,len(signature)//2).hex()==signature
    regs=dict(zip(['edi','esi','ebx','edx','ecx','eax','ebp','eip','cs','eflags','esp'],struct.unpack_from('<11I',b,156)))
    main=context(threads[pi.tid]);main_regs=dict(zip(['edi','esi','ebx','edx','ecx','eax','ebp','eip','cs','eflags','esp'],struct.unpack_from('<11I',main,156)))
    count=min(opt.worker_main_stack_bytes,4096-(main_regs['esp']&4095));assert count%4==0
    control=u32(0x4db558)
    row=dict(event=targets[pc],pc=pc,threadId=tid,ordinal=len(replay_store_events)+1,
        hostMonotonicNs=time.monotonic_ns(),precedingPlayerCallbacks=callback_count,stage=u32(0x4f58a4),
        stageFrame=u32(control+0x14)if control else None,registers=regs,originalInstructionBytes=signature,
        rngHex=read(0x4db508,16).hex(),replaySeedWord=struct.unpack('<H',read(regs['esi']-0x12,2))[0],
        workerInstructionStillPending=True,workerPriorStoresCompleted=[0x45610f,0x456123,0x456129][:list(store_signatures).index(pc)],
        mainThreadContextAtWorkerDebugEvent=dict(registers=main_regs,stackHex=read(main_regs['esp'],count).hex(),
            stackBytes=count,debugStatus=struct.unpack_from('<I',main,20)[0],
            instructionPcAtEarlierStoreNotProven=True,unwoundCallStack=False),
        hardwareExecutionBreakpoint=True,readOnly=True,threadSchedulingControlled=False,
        debuggerPausesAffectTiming=True,providedToEngine=False)
    replay_store_events.append(row)
    with(home/'replay-rng-store-events.jsonl').open('a',encoding='utf8')as stream:stream.write(json.dumps(row)+'\\n')
    if pc in store_next:worker_store_pc[tid]=store_next[pc]
    else:worker_store_pc.pop(tid,None)
    print(json.dumps(dict(replayRngStorePc=pc,stage=row['stage'],callbacks=callback_count,mainPcAtDebugEvent=main_regs['eip'])),flush=True)

'''
    replace('def event_snapshot(pc,tid,b):',helper+'def event_snapshot(pc,tid,b):')
    replace('    if pc in (0x47e65b,0x47e660):',
            '    if pc in store_signatures and tid!=pi.tid and tid in pending_worker_rng:\n'+
            '        replay_store_snapshot(pc,tid,b)\n'+
            '        if pc!=0x456133:return\n'+
            '    if pc in (0x47e65b,0x47e660):')
    replace("    (home/'report.json').write_text(json.dumps(report,indent=2)+'\\n');print(",
            "    report.update(replayRngStoreEvents=len(replay_store_events),replayRngStoreEventsSha256=sha((home/'replay-rng-store-events.jsonl').read_bytes())if replay_store_events else None,replayRngStoreInstructionPcs=list(store_signatures),replayRngStoreValuesProvidedToEngine=False,replayRngStoreThreadSchedulingControlled=False,replayRngStoreAllInstructionsObservedBeforeExecution=True,originalOldRecordingOrderRecovered=False)\n"+
            "    (home/'report.json').write_text(json.dumps(report,indent=2)+'\\n');print(")
    assert 'SuspendThread' not in text and 'ResumeThread' not in text
    compile(text,'observer.py','exec');out.mkdir()
    (out/'observer.py').write_bytes(text.encode())
    result=dict(prepared=True,baseObserver=str(base.relative_to(R)),baseObserverSha256=BASE,
                observerSha256=sha(text.encode()),preparerSha256=sha(Path(__file__).read_bytes()),
                workerExecutionBreakpointPcs=[0x45610f,0x456123,0x456129,0x456133],
                gameInstructionBytesPatched=0,nativeRngValuesProvidedToEngine=False,
                threadSchedulingControlled=False,debuggerPausesAffectTiming=True,
                oldRecordingExactMainPcAtEarlierStoresProven=False,completeGame=False,nativeEquivalent=False)
    (out/'prepared.json').write_bytes((json.dumps(result,indent=2)+'\n').encode());print(json.dumps(result))


if __name__=='__main__':main()
