"""Extend sealed register/VM checks with actual DR0 pump/Player witnesses.

Receipt order is proved for the observed main-thread events. No missing pump,
physical frame entry or cross-thread instruction order is inferred.
"""
from pathlib import Path
import argparse,hashlib,json

R=Path(__file__).resolve().parents[1]
H=R/'artifacts/th14/script-rng-read-generation-nov05'
SHA=lambda b:hashlib.sha256(b).hexdigest()
PARENT_SHA='bebd84d7e0bae59eec80a30e2183bcebcd164b94277f053105d56f996afbe73b'
OBSERVER_SHA='f215b4fae98ac88c1cd94576f99ccb31484d157497cf14e7bfd89e22f79a8884'

def verify(native):
    parent=R/'tools/th14-rng-pump-trace-evidence-nov05.py';raw=parent.read_bytes();assert SHA(raw)==PARENT_SHA
    s=raw.decode()
    substitutions={
        "OBSERVER_SHA='4595cf23b509c917cf881aa420b5629307aacb7f07c793a51482e9b14b254754'":"OBSERVER_SHA='"+OBSERVER_SHA+"'",
        'observer-rotating-pump/':'observer-player-pump/',
        'preflight-rotating-pump/':'preflight-player-pump/',
        "p['debugAddresses'][0]==0x44dbd0":"p['debugAddresses'][0]in (0x44dbd0,0x47d720)"}
    for old,new in substitutions.items():assert s.count(old)>0;s=s.replace(old,new)
    env=dict(__file__=str(Path(__file__).resolve()),__name__='sealed_mux_parent')
    exec(compile(s,str(parent),'exec'),env);proof=env['verify'](native);bindings=proof['bindings']
    def blob(path):
        path=path.resolve();assert path.is_relative_to(R);b=path.read_bytes();bindings[path.relative_to(R).as_posix()]=dict(bytes=len(b),sha256=SHA(b));return b
    def load(path):return json.loads(blob(path))
    def rows(path):return [json.loads(x)for x in blob(path).splitlines()if x]
    blob(parent);report=load(native/'report.json')
    assert report['sourceSha256']==OBSERVER_SHA and report['playerPumpDr0MultiplexedDuringRngWatch']
    assert report['playerPumpMuxOriginalDispatchOrderAssumed']and not report['allPlayerOrPumpCallsProvenObserved']
    mux=rows(native/'player-pump-mux-events.jsonl');assert len(mux)==report['playerPumpMuxEvents']>0
    assert SHA(blob(native/'player-pump-mux-events.jsonl'))==report['playerPumpMuxSha256']
    clock=rows(native/'debug-event-clock.jsonl');by_seq={r['debugEventSequence']:r for r in clock}
    for r in mux:
        assert r['pc']in [0x44dbd0,0x47d720]and r['readOnly']and not r['providedToEngine']
        c=by_seq[r['debugEventSequence']]
        assert c['threadId']==r['threadId']and c['pc']==r['pc']and c['hostMonotonicNs']==r['hostMonotonicNs']
        assert c['debugStatus']==r['debugStatus']
        matching=sum(1<<i for i,a in enumerate(r['debugAddresses'])if a==r['pc'])
        assert matching==r['matchingHardwareBits']and r['debugStatus']&matching
        assert r['originalDispatchOrderAssumed']and r['allUnobservedCallsNotClaimed']
    accesses=rows(native/'script-rng-access-events.jsonl');first=accesses[0]
    actual_pre_read=[r for r in mux if r['pc']==0x47d720 and r['debugEventSequence']<first['debugEventSequence']]
    prior_player=[r for r in clock if r['threadId']==first['threadId']and r['pc']==0x44dbd0 and r['debugEventSequence']<first['debugEventSequence']]
    assert prior_player
    after_player=[r for r in actual_pre_read if r['debugEventSequence']>prior_player[-1]['debugEventSequence']]
    # Keep a failed coverage result false. A pump before the preceding Player
    # is still a real boundary, but is not silently relabeled as one after it.
    proof.update(schema='th14/player-pump-register-trace/1',muxParentVerifierSha256=PARENT_SHA,
        actualMuxBoundaryEvents=len(mux),actualMuxPumpEvents=sum(r['pc']==0x47d720 for r in mux),
        actualMuxPlayerEvents=sum(r['pc']==0x44dbd0 for r in mux),
        actualMuxPumpsBeforeFirstRead=len(actual_pre_read),
        actualMuxPumpsAfterLastPlayerBeforeFirstRead=len(after_player),
        actualPostPlayerPumpBeforeFirstReadObserved=bool(after_player),
        playerCountsUsedToInferPhysicalFrame=False,lastRecordedPumpProvenLastActualPump=False,
        originalDispatchOrderAssumed=True,allPlayerOrPumpCallsProvenObserved=False,
        exactOriginalFrameEntryRecovered=False,ordinaryIndependentTimingAccepted=False,completeGame=False)
    return proof

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--native',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();native=a.native.resolve();out=a.output.resolve()
    assert native.is_relative_to(R/'artifacts/th14')and out.is_relative_to(R/'artifacts/th14')and not out.exists()
    v=verify(native);out.write_text(json.dumps(v,indent=2)+'\n')
    print(json.dumps({k:v[k]for k in ['verifiedFiniteOriginalRegisterReadEvidence','accessEvents','arithmeticPairsEqual','actualMuxBoundaryEvents','actualMuxPumpEvents','actualPostPlayerPumpBeforeFirstReadObserved','ordinaryIndependentTimingAccepted']}))
