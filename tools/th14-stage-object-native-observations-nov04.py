"""Verify original Stage object edges and four pre-writer observations per stage."""
from pathlib import Path
import argparse,hashlib,json,struct
R=Path(__file__).resolve().parents[1];sha=lambda raw:hashlib.sha256(raw).hexdigest()


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--native',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    native=a.native.resolve(strict=True);assert native.is_relative_to(R/'artifacts/th14');home=native.parent;bindings={}
    def read(path):
        raw=path.read_bytes();bindings[path.relative_to(R).as_posix()]=dict(bytes=len(raw),sha256=sha(raw));return raw
    def load(path):return json.loads(read(path))
    report=load(native/'report.json');prepared=load(home/'prepared.json');end=load(home/'process-end.json')
    assert report['callbacks']==35000 and report['childExited']and not report['error']and not report['debugErrors']
    assert end['exitCode']==1 and end['guardStop']is None and report['diagnosticPrefixOnly']
    assert report['hardwareBreakpointsOnly']and report['instructionBytesPatched']==report['rngOrCounterWrites']==0 and not report['inputInjected']
    assert report['gameStateWordWrites']==1 and report['caseInitialization']['attractBitClearOnly']
    assert bytes.fromhex(report['configHex'])[0x22:0x24]==bytes(2)
    assert report['sourceSha256']==prepared['observerSha256']==sha(read(native/'observer-source.py'))==sha(read(home/'observer.py'))
    assert prepared['preparerSha256']==sha(read(R/'tools/th14-prepare-replay-rng-stage-object-observer-nov04.py'))
    raw=read(native/'stage-object-vm-window-events.jsonl');assert sha(raw)==report['stageObjectVmWindowEventsSha256']
    edges=[json.loads(x)for x in raw.splitlines()];assert len(edges)==report['stageObjectVmWindowEvents']
    assert [x['ordinal']for x in edges]==list(range(1,len(edges)+1))
    active=None;pairs=[];last_time=0
    for edge in edges:
        assert edge['hostMonotonicNs']>last_time;last_time=edge['hostMonotonicNs']
        blob=bytes.fromhex(edge['rawVmHexAtCallEdge']);assert len(blob)==0x5cc
        assert(edge['file'],edge['script'],edge['handle'])==(struct.unpack_from('<H',blob,0x36)[0],struct.unpack_from('<H',blob,0x4aa)[0],struct.unpack_from('<I',blob,0x540)[0])
        context=edge['stageObjectContext'];frame=bytes.fromhex(context['rawCallerFrameHex'])
        assert len(frame)==44 and context['owner']==struct.unpack_from('<I',frame,8)[0]and context['objectIndex']==struct.unpack_from('<I',frame,4)[0]
        assert context['objectAddress']==struct.unpack_from('<I',frame,0)[0]
        assert context['array']+context['animationIndex']*0x5cc==edge['vm']
        assert context['animationIndex']==struct.unpack_from('<h',bytes.fromhex(context['rawPrimitiveHex']),6)[0]
        assert context['actualVmArrayAndPrimitiveIndexAgree']and context['readOnly']and not context['providedToEngine']
        if edge['pc']==0x40f2a2:
            assert active is None;active=edge
        else:
            assert edge['pc']==0x40f2a7 and active and edge['callEntryOrdinal']==active['ordinal']and edge['vm']==active['vm']
            assert edge['stageObjectContext']==active['stageObjectContext'];pairs.append((active,edge));active=None
    # The bounded watcher can close at the next call entry after the worker
    # sequence; that entry is retained without inventing a return observation.
    trailing=active
    if trailing:assert trailing is edges[-1]and trailing['pc']==0x40f2a2
    store_raw=read(native/'replay-rng-store-events.jsonl');assert sha(store_raw)==report['replayRngStoreEventsSha256']
    stores=[json.loads(x)for x in store_raw.splitlines()];assert len(stores)==8
    transitions=[json.loads(x)for x in read(native/'transition-events.jsonl').splitlines()]
    summaries=[]
    for stage in(2,3):
        group=[x for x in stores if x['stage']==stage];assert [x['pc']for x in group]==[0x45610f,0x456123,0x456129,0x456133]
        for row in group:
            call=row['stageObjectVmCallAtWorkerStore']['observedCall'];clock=row['hostMonotonicNs']
            main=row['mainThreadContextAtWorkerDebugEvent'];main_pc=main['registers']['eip'];mode='inside-observed-call'
            if call:
                assert call==edges[call['ordinal']-1]and call['hostMonotonicNs']<clock
                snapshot=row['stageObjectVmCallAtWorkerStore']['snapshot'];assert snapshot and snapshot['callIdentityStillMatches']
                returned=next((y for x,y in pairs if x['ordinal']==call['ordinal']),None)
                if returned:
                    assert clock<returned['hostMonotonicNs']
                    if main_pc==0x40f2a7:mode='return-edge-delivery-pending'
                    elif main_pc==0x40f2a2:mode='call-instruction-still-pending'
                else:
                    assert trailing and call==trailing and row['pc']==0x456133
                    closed=next(x for x in transitions if x['pc']==0x456133 and x['stage']==stage)
                    window=closed['stageObjectVmCallWindowAtSeedRestore']
                    assert window['activeCall']==call and window['withinVmMethodAtRestore']
                    mode='active-method-return-not-observed'
            else:
                if main_pc==0x40f2a2:
                    call=next(x for x in edges if x['pc']==0x40f2a2 and x['hostMonotonicNs']>clock)
                    assert main['registers']['edi']==main['registers']['ecx']==call['vm']
                    frame_offset=main['registers']['ebp']-12-main['registers']['esp']
                    stack=bytes.fromhex(main['stackHex']);assert frame_offset>=0 and frame_offset+44<=len(stack)
                    assert stack[frame_offset:frame_offset+44]==bytes.fromhex(call['stageObjectContext']['rawCallerFrameHex'])
                    assert call.get('callEntryDrainedAfterSeedRestore')and call['restoreObservationHostNs']>=clock
                    returned=next(y for x,y in pairs if x['ordinal']==call['ordinal']);mode='call-entry-delivery-pending'
                else:
                    returned=next(x for x in reversed(edges)if x['pc']==0x40f2a7 and x['hostMonotonicNs']<clock)
                    call=edges[returned['callEntryOrdinal']-1];mode='after-return-observed'
                    assert not any(returned['hostMonotonicNs']<x['hostMonotonicNs']<clock for x in edges)
            ctx=call['stageObjectContext'];rng=struct.unpack('<HHIHHI',bytes.fromhex(row['rngHex']))
            summaries.append(dict(stage=stage,workerPc=row['pc'],precedingCallbacks=row['precedingPlayerCallbacks'],
                mainPc=row['mainThreadContextAtWorkerDebugEvent']['registers']['eip'],callEntryOrdinal=call['ordinal'],returnOrdinal=returned['ordinal']if returned else None,
                mainPhase=mode,file=call['file'],script=call['script'],objectIndex=ctx['objectIndex'],
                primitiveIndex=ctx['primitiveIndex'],animationIndex=ctx['animationIndex'],
                scriptSeed=rng[0],scriptCalls=rng[2],gameplaySeed=rng[3],gameplayCalls=rng[5],
                workerStoreAtThisPcStillPending=True))
    result=dict(verifiedOriginalStageObjectObservations=True,callbacks=35000,pairedStageVmCalls=len(pairs),
        trailingCallEntryWithoutObservedReturn=trailing['ordinal']if trailing else None,workerEvents=summaries,
        preStoreObservationsAreNotStoreCompletionTimes=True,engineInputScheduleAccepted=False,
        oldFailureClosed=False,nativeStateValuesProvidedToEngine=False,completeGame=False,nativeEquivalent=False,
        bindings=bindings,verifierSha256=sha(Path(__file__).read_bytes()))
    output=a.output.resolve();assert output.is_relative_to(home)and not output.exists()
    output.write_bytes((json.dumps(result,indent=2)+'\n').encode());print(json.dumps({k:v for k,v in result.items()if k!='bindings'}),flush=True)


if __name__=='__main__':main()
