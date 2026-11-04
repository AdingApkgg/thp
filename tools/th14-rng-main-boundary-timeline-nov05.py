"""Describe directly observed same-thread pump/Player/RNG receipt ordering.

Player counts label intervals; they do not identify a physical game frame.
Do not infer that a recorded earlier pump is the last actual pump, or that
absence of a watched event proves the corresponding instruction did not run.
"""
from pathlib import Path
import argparse,bisect,hashlib,json,struct

R=Path(__file__).resolve().parents[1]
SHA=lambda b:hashlib.sha256(b).hexdigest()

def verify(native):
    bindings={}
    def raw(p):
        p=p.resolve();assert p.is_relative_to(R);b=p.read_bytes();bindings[p.relative_to(R).as_posix()]=dict(bytes=len(b),sha256=SHA(b));return b
    def load(p):return json.loads(raw(p))
    def rows(p):return [json.loads(x)for x in raw(p).splitlines()if x]
    report=load(native/'report.json');end=load(native.parent/'process-end.json')
    assert end['guardStop']is None and report['childExited']and not report['error']and not report['debugErrors']
    assert SHA(raw(native/'observer-source.py'))==report['sourceSha256']
    accesses=rows(native/'script-rng-access-events.jsonl');assert accesses and len(accesses)==report['scriptRngRegisterAccessEvents']
    tids={a['threadId']for a in accesses};assert len(tids)==1;tid=next(iter(tids))
    clock=rows(native/'debug-event-clock.jsonl');assert SHA(raw(native/'debug-event-clock.jsonl'))==report['debugEventClockSha256']
    clock=[e for e in clock if e['threadId']==tid]
    assert all(e['hostClockSharedAtDebugEventReceipt']and e['hostMonotonicNs']==e['debugEventReceiptHostNs']for e in clock)
    assert all(a['debugEventSequence']<b['debugEventSequence']and a['hostMonotonicNs']<=b['hostMonotonicNs']for a,b in zip(clock,clock[1:]))
    players=[e for e in clock if e['pc']==0x44dbd0];pumps=[e for e in clock if e['pc']==0x47d720]
    times=raw(native/'player-host-monotonic.u64')
    assert len(players)==report['callbacks']and len(times)==report['callbacks']*8 and SHA(times)==report['playerHostTimesSha256']
    for i,e in enumerate(players):
        assert e['precedingPlayerCallbacks']==i and e['hostMonotonicNs']==struct.unpack_from('<Q',times,i*8)[0]
    first=accesses[0];assert first['pc']==0x403339 and first['instructionContract']['kind']=='mix32'
    assert first['hostClockSharedAtDebugEventReceipt']
    event=next(e for e in clock if e['debugEventSequence']==first['debugEventSequence'])
    assert event['pc']==first['pc']and event['hostMonotonicNs']==first['hostMonotonicNs']
    before_players=[e for e in players if e['debugEventSequence']<first['debugEventSequence']]
    assert len(before_players)==first['precedingPlayerCallbacks']and before_players
    previous=before_players[-1]
    before_pumps=[e for e in pumps if e['debugEventSequence']<first['debugEventSequence']]
    assert before_pumps
    pump=before_pumps[-1]
    intervening=[e for e in players if pump['debugEventSequence']<e['debugEventSequence']<first['debugEventSequence']]
    since_previous=[e for e in before_pumps if e['debugEventSequence']>previous['debugEventSequence']]
    actual_mux=rows(native/'player-pump-mux-events.jsonl')if report.get('playerPumpMuxEvents')else[]
    if actual_mux:
        assert len(actual_mux)==report['playerPumpMuxEvents']and SHA(raw(native/'player-pump-mux-events.jsonl'))==report['playerPumpMuxSha256']
        by_sequence={e['debugEventSequence']:e for e in clock}
        for row in actual_mux:
            original=by_sequence[row['debugEventSequence']]
            assert row['pc']in (0x44dbd0,0x47d720)and row['pc']==original['pc']and row['hostMonotonicNs']==original['hostMonotonicNs']
            assert row['readOnly']and not row['providedToEngine']
            assert row['debugStatus']&row['matchingHardwareBits']
    return dict(schema='th14/rng-main-boundary-timeline/1',verifiedReceiptTimeline=True,
        callbacks=report['callbacks'],nativeDebugExceptions=0,scriptInstructionAccesses=len(accesses),
        watchedPumpPc=0x47d720,watchedPlayerPc=0x44dbd0,firstReadAfterInstructionPc=first['pc'],
        firstReadPrecedingPlayerCallbacks=first['precedingPlayerCallbacks'],
        latestRecordedPumpPrecedingPlayerCallbacks=pump['precedingPlayerCallbacks'],
        playerReceiptsBetweenLatestRecordedPumpAndFirstRead=len(intervening),
        actualRecordedPumpsAfterLastPlayerAndBeforeFirstRead=len(since_previous),
        latestRecordedPumpBeforeLastPlayer=pump['debugEventSequence']<previous['debugEventSequence'],
        pumpToFirstReadReceiptNanoseconds=first['hostMonotonicNs']-pump['hostMonotonicNs'],
        muxBoundaryRows=len(actual_mux),playerCountsUsedToInferPhysicalFrame=False,
        sameMainThreadInstructionOrderObserved=True,crossThreadInstructionOrderProven=False,
        originalInstructionExecutionTimestampsRecovered=False,latestRecordedPumpProvenLastActualPump=False,
        nativePhysicalFrameEntryRecovered=False,absenceOfPumpNotProofOfNoExecution=True,
        originalStateValuesProvidedToEngine=False,ordinaryIndependentTimingAccepted=False,completeGame=False,
        verifierSha256=SHA(Path(__file__).read_bytes()),bindings=bindings)

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--native',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();native=a.native.resolve();out=a.output.resolve()
    assert native.is_relative_to(R/'artifacts/th14')and out.is_relative_to(R/'artifacts/th14')and not out.exists()
    v=verify(native);out.write_text(json.dumps(v,indent=2)+'\n')
    print(json.dumps({k:v[k]for k in ['verifiedReceiptTimeline','firstReadPrecedingPlayerCallbacks','latestRecordedPumpPrecedingPlayerCallbacks','playerReceiptsBetweenLatestRecordedPumpAndFirstRead','actualRecordedPumpsAfterLastPlayerAndBeforeFirstRead','muxBoundaryRows','nativePhysicalFrameEntryRecovered']}))
