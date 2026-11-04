"""Verify stable hardware pass boundaries against the original debug clock.

Counts never stand in for physical frame identity, and receipt times never
stand in for original execution timestamps. The output contains no RNG values.
"""
from pathlib import Path
import argparse,hashlib,json,struct
R=Path(__file__).resolve().parents[1];SHA=lambda b:hashlib.sha256(b).hexdigest()
def verify(home,output):
    assert home.is_relative_to(R/'artifacts/th14')and output.is_relative_to(R/'artifacts/th14')and not output.exists()
    bindings={}
    def read(name):
        raw=(home/name).read_bytes();bindings[(home/name).relative_to(R).as_posix()]=dict(bytes=len(raw),sha256=SHA(raw));return raw
    report=json.loads(read('report.json'));assert report['childExited']and not report['error']and not report['debugErrors']
    assert report['supervisorPlayerPumpWatchesFixed']and report['supervisorPassBoundaryPc']==0x444890
    assert not report['playerPumpDr0MultiplexedDuringRngWatch']and not report['rotatingVmEdgeHardwareSlot']
    source=read('observer-source.py');assert SHA(source)==report['sourceSha256']
    rows=[json.loads(line)for line in read('supervisor-pass-events.jsonl').splitlines()]
    clock={}
    for line in read('debug-event-clock.jsonl').splitlines():
        item=json.loads(line);assert item['debugEventSequence']not in clock;clock[item['debugEventSequence']]=item
    player=read('player-host-monotonic.u64');assert len(player)==report['callbacks']*8
    current=None;entries=[];pumps=players=unanchored=0;previous_sequence=0;pass_counts={};thread=None
    for row in rows:
        pc=row['pc'];assert pc in (0x444890,0x47d720,0x44dbd0)
        assert row['debugAddresses'][:3]==[0x44dbd0,0x444890,0x47d720]and row['debugAddresses'][3]in (0,0x4db508)
        assert row['debugStatus']&row['matchingHardwareBits']
        seq=row['debugEventSequence'];assert seq>previous_sequence;previous_sequence=seq
        original=clock[seq];assert original['threadId']==row['threadId']and original['pc']==pc
        assert original['hostMonotonicNs']==row['hostMonotonicNs']==row['debugEventReceiptHostNs']
        assert original['precedingPlayerCallbacks']==row['precedingPlayerCallbacks']
        if thread is None:thread=row['threadId']
        assert row['threadId']==thread
        ordinal=row['supervisorPassOrdinal']
        if pc==0x444890:
            assert ordinal==len(entries)+1
            current=row;entries.append(row);pass_counts[ordinal]=dict(pumps=0,players=0)
        elif current is None:
            assert ordinal==0;unanchored+=1;continue
        else:
            assert ordinal==current['supervisorPassOrdinal']and current['debugEventSequence']<seq
            if pc==0x47d720:pumps+=1;pass_counts[ordinal]['pumps']+=1
            else:
                players+=1;pass_counts[ordinal]['players']+=1
                index=row['precedingPlayerCallbacks'];assert 0<=index<report['callbacks']
                assert struct.unpack_from('<Q',player,index*8)[0]==row['hostMonotonicNs']
    assert entries and len(entries)==report['supervisorEntryEvents']
    trapped_entries=[item for item in clock.values()if item['pc']==0x444890]
    assert len(trapped_entries)==len(entries),'An entry exception was not accounted for by a validated hardware observation'
    assert all(item['threadId']==thread and item['debugStatus']&2 for item in trapped_entries)
    # Count unusual pass shapes explicitly. They are not silently treated as
    # one Player == one pass or accepted as physical frames.
    shapes={}
    for values in pass_counts.values():
        key=f"pump{values['pumps']}-player{values['players']}";shapes[key]=shapes.get(key,0)+1
    accesses=[]
    if(home/'script-rng-access-events.jsonl').exists():
        for line in read('script-rng-access-events.jsonl').splitlines():
            row=json.loads(line);boundary=row['latestObservedSupervisorPass'];assert boundary is not None
            entry=entries[boundary['supervisorPassOrdinal']-1]
            for key in boundary:assert entry[key]==boundary[key]
            assert entry['threadId']==row['threadId']and entry['debugEventSequence']<row['debugEventSequence']
            assert entry['hostMonotonicNs']<=row['hostMonotonicNs']
            assert row['instructionValueDecoded']
            accesses.append(dict(ordinal=row['ordinal'],pc=row['pc'],precedingPlayerCallbacks=row['precedingPlayerCallbacks'],
                supervisorPassOrdinal=entry['supervisorPassOrdinal'],supervisorEntryReceiptNs=entry['hostMonotonicNs'],
                readReceiptNs=row['hostMonotonicNs'],debugEventSequence=row['debugEventSequence']))
    result=dict(schema='th14/supervisor-pass-timeline/1',verifiedFixedHardwareBoundaries=True,callbacks=report['callbacks'],
        nativeDebugExceptions=0,entries=len(entries),pumps=pumps,players=players,unanchoredStartupRows=unanchored,
        passShapes=shapes,firstEntryPrecedingPlayerCallbacks=entries[0]['precedingPlayerCallbacks'],
        rngInstructionAccesses=len(accesses),rngAccessBoundaries=accesses,addresses=[0x44dbd0,0x444890,0x47d720],
        mainWatchesNotMultiplexed=True,playerCountsUsedToInferPassIdentity=False,physicalFrameIdentityProven=False,
        originalExecutionTimestampsRecovered=False,ordinaryIndependentTimingAccepted=False,originalValuesProvidedToEngine=False,
        evidenceBindings=bindings,verifierSha256=SHA(Path(__file__).read_bytes()),completeGame=False)
    output.write_text(json.dumps(result,indent=2)+'\n');return {k:result[k]for k in ['verifiedFixedHardwareBoundaries','callbacks','entries','pumps','players','passShapes','rngInstructionAccesses','completeGame']}
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--native',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    print(json.dumps(verify(a.native.resolve(),a.output.resolve())))
