"""Bind worker readiness to an observed normal-VM return in one stopped event."""
from pathlib import Path
import argparse, hashlib, json, struct
R=Path(__file__).resolve().parents[1];sha=lambda raw:hashlib.sha256(raw).hexdigest()


def verify(native):
    native=native.resolve(strict=True);assert native.is_relative_to(R/'artifacts/th14');bindings={}
    def read(path):
        raw=path.read_bytes();bindings[path.relative_to(R).as_posix()]=dict(bytes=len(raw),sha256=sha(raw));return raw
    def load(path):return json.loads(read(path))
    report=load(native/'report.json');home=native.parent;prepared=load(home/'prepared.json');end=load(home/'process-end.json')
    assert report['childExited'] and not report['error'] and not report['debugErrors'] and report['callbacks']==35000
    assert end['guardStop']is None and end['exitCode']==1 and report['diagnosticPrefixOnly']
    assert report['hardwareBreakpointsOnly'] and report['instructionBytesPatched']==report['rngOrCounterWrites']==0
    assert report['gameStateWordWrites']==1 and report['caseInitialization']['attractBitClearOnly'] and not report['inputInjected']
    assert bytes.fromhex(report['configHex'])[0x22:0x24]==bytes(2)
    assert report['sourceSha256']==prepared['observerSha256']==sha(read(native/'observer-source.py'))==sha(read(home/'observer.py'))
    assert prepared['preparerSha256']==sha(read(R/'tools/th14-prepare-replay-rng-store-vm-observer-nov04.py'))
    assert prepared['parentPreparerSha256']==sha(read(R/'tools/th14-prepare-replay-rng-store-observer-nov04.py'))
    assert report['executableSha256']=='f08e885e28d2e0fc8c579e88034dd7de8f2a648d8f08ce781cf08eadc9ffe353'
    source=(native/'observer-source.py').read_text(encoding='utf8')
    helper=source[source.index('def replay_store_snapshot('):source.index('def event_snapshot(')]
    assert 'ContinueDebugEvent'not in helper and 'SuspendThread'not in source and 'ResumeThread'not in source
    events_raw=read(native/'normal-vm-window-events.jsonl');assert sha(events_raw)==report['normalVmWindowEventsSha256']
    edges=[json.loads(line)for line in events_raw.splitlines()];assert len(edges)==report['normalVmWindowEvents']==4244
    assert [x['ordinal']for x in edges]==list(range(1,len(edges)+1))
    for first,last in zip(edges[::2],edges[1::2],strict=True):
        assert (first['pc'],last['pc'])==(0x47e65b,0x47e660) and last['callEntryOrdinal']==first['ordinal'] and first['vm']==last['vm']
        assert first['hostMonotonicNs']<last['hostMonotonicNs']
        for row in (first,last):
            blob=bytes.fromhex(row['rawVmHexAtCallEdge']);assert len(blob)==0x5cc
            assert (row['file'],row['script'],row['handle'])==(struct.unpack_from('<H',blob,0x36)[0],struct.unpack_from('<H',blob,0x4aa)[0],struct.unpack_from('<I',blob,0x540)[0])
    stores_raw=read(native/'replay-rng-store-events.jsonl');assert sha(stores_raw)==report['replayRngStoreEventsSha256']
    stores=[json.loads(line)for line in stores_raw.splitlines()];assert len(stores)==8
    transitions=[json.loads(line)for line in read(native/'transition-events.jsonl').splitlines()]
    times=read(native/'player-host-monotonic.u64');assert len(times)==35000*8 and sha(times)==report['playerHostTimesSha256']
    inputs=[]
    for stage in (2,3):
        group=[row for row in stores if row['stage']==stage];assert len(group)==4 and [row['pc']for row in group]==[0x45610f,0x456123,0x456129,0x456133]
        snapshot=group[-1];canonical=next(row for row in transitions if row['stage']==stage and row['pc']==0x456133)
        assert snapshot['threadId']==canonical['threadId'] and snapshot['precedingPlayerCallbacks']==canonical['precedingPlayerCallbacks']
        assert snapshot['rngHex']==canonical['rngHex'] and snapshot['registers']==canonical['registers']
        assert snapshot['mainThreadContextAtWorkerDebugEvent']['registers']==canonical['mainThreadContextAtWorkerEvent']['registers']
        assert snapshot['mainThreadContextAtWorkerDebugEvent']['stackHex']==canonical['mainThreadContextAtWorkerEvent']['stackHex']
        assert snapshot['mainThreadContextAtWorkerDebugEvent']['registers']['eip']==0x47e660
        assert snapshot['hostMonotonicNs']<=canonical['hostMonotonicNs']
        assert not any(snapshot['hostMonotonicNs']<row['hostMonotonicNs']<canonical['hostMonotonicNs']for row in edges)
        callback=snapshot['precedingPlayerCallbacks'];assert 1<=callback<35000
        assert struct.unpack_from('<Q',times,(callback-1)*8)[0]<snapshot['hostMonotonicNs']<=canonical['hostMonotonicNs']<struct.unpack_from('<Q',times,callback*8)[0]
        active=snapshot['normalVmCallAtWorkerStore']['observedCall']
        if active is not None:
            assert active==edges[active['ordinal']-1]
            returned=next(row for row in edges if row['pc']==0x47e660 and row['callEntryOrdinal']==active['ordinal'])
            assert active['hostMonotonicNs']<snapshot['hostMonotonicNs']<returned['hostMonotonicNs']
            identity=snapshot['normalVmCallAtWorkerStore']['snapshot'];assert identity['callIdentityStillMatches']
            assert identity['identity']=={key:active[key]for key in ('handle','file','script')}
            mode='return-edge-delivery-pending'
        else:
            returned=next(row for row in reversed(edges)if row['pc']==0x47e660 and row['hostMonotonicNs']<snapshot['hostMonotonicNs'])
            assert not any(returned['hostMonotonicNs']<row['hostMonotonicNs']<snapshot['hostMonotonicNs']for row in edges)
            mode='return-edge-already-delivered'
        entry=edges[returned['callEntryOrdinal']-1]
        assert returned['stage']==stage and returned['precedingPlayerCallbacks']==callback
        assert all(returned[key]==entry[key]for key in ('vm','handle','file','script'))
        rng=[struct.unpack('<HHIHHI',bytes.fromhex(row['rngHex']))for row in group]
        assert len({words[2]for words in rng})==1 and len({words[5]for words in rng[:3]})==1 and rng[-1][5]==0
        assert rng[0][0]==rng[1][0] and rng[2][0]==rng[3][0]==snapshot['replaySeedWord']
        inputs.append(dict(stage=stage,callback=callback,file=returned['file'],script=returned['script'],handle=returned['handle'],point=1,
            readyNs=canonical['hostMonotonicNs'],storeSnapshotNs=snapshot['hostMonotonicNs'],observationLatencyNs=canonical['hostMonotonicNs']-snapshot['hostMonotonicNs'],
            sourcePc=0x456133,mainPc=0x47e660,sourceCallOrdinal=entry['ordinal'],sourceReturnOrdinal=returned['ordinal'],returnEdgeState=mode,
            sameStoppedCpuAndRngState=True,noScriptRngDrawsWithinObservedStores=True,gameplayCounterResetOnlyAtFinalStore=True))
    assert [(x['stage'],x['callback'],x['file'],x['script'],x['handle'])for x in inputs]==[(2,14082,5,16,720865),(3,30749,5,4,696286)]
    return dict(verifiedObservedNormalVmReturnInputs=True,native=str(native.relative_to(R)),callbacks=35000,inputs=inputs,
        nativeVmIdentityUsedOnlyAsMatcher=True,nativeRngOrSerialStateOverridden=False,canonicalClockIsObservationTime=True,
        debuggerPausesAffectTiming=True,ordinaryIndependentThreadTimingAccepted=False,completeGame=False,nativeEquivalent=False,
        bindings=bindings,verifierSha256=sha(Path(__file__).read_bytes()))


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--native',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--check',action='store_true');a=p.parse_args()
    result=verify(a.native);out=a.output.resolve();assert out.is_relative_to(R/'artifacts/th14')or out.is_relative_to(R/'docs/porting')
    data=(json.dumps(result,indent=2)+'\n').encode()
    if a.check:assert out.read_bytes()==data
    else:assert not out.exists();out.write_bytes(data)
    print(json.dumps({key:value for key,value in result.items()if key not in('bindings','inputs')}))


if __name__=='__main__':main()
