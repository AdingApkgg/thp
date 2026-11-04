"""Seal the rotating-edge trace with unchanged RNG instruction checks.

Only counts, addresses, paths and hashes are emitted. Pump observations must
come from their actual hardware slot, not an inferred preceding Player clock.
The native executable, register values, seeds and raw payloads stay private.
"""
from pathlib import Path
import argparse,hashlib,json

R=Path(__file__).resolve().parents[1]
H=R/'artifacts/th14/script-rng-read-generation-nov05'
SHA=lambda b:hashlib.sha256(b).hexdigest()
PARENT_SHA='1b4d904ca8e93b1b6bf6158639139426ea3297182006b9ec57fe6308085237dd'
OBSERVER_SHA='4595cf23b509c917cf881aa420b5629307aacb7f07c793a51482e9b14b254754'

def verify(native):
    parent=R/'tools/th14-rng-register-trace-evidence-nov05.py';raw=parent.read_bytes()
    assert SHA(raw)==PARENT_SHA
    source=raw.decode()
    substitutions={
        'observer-pending-status/observer.py':'observer-rotating-pump/observer.py',
        'preflight-pending-status/verified.json':'preflight-rotating-pump/verified.json',
        '26727dd09ec942e04e9def563c5ec8b56e6a010912f44e4ed1b28809bb7ce596':OBSERVER_SHA}
    for old,new in substitutions.items():
        assert source.count(old)==1;source=source.replace(old,new)
    # Keep the common decoder, arithmetic, bounds, exception, payload and
    # register checks intact. The substitutions bind only this new observer.
    env=dict(__file__=str(Path(__file__).resolve()),__name__='sealed_parent_rng_decoder')
    exec(compile(source,str(parent),'exec'),env)
    proof=env['verify'](native)
    bindings=proof['bindings']
    def blob(path):
        p=path.resolve();assert p.is_relative_to(R);b=p.read_bytes()
        bindings[p.relative_to(R).as_posix()]=dict(bytes=len(b),sha256=SHA(b));return b
    def load(path):return json.loads(blob(path))
    def rows(path):return [json.loads(line)for line in blob(path).splitlines()if line]
    blob(parent)
    report=load(native/'report.json');prepared=load(H/'observer-rotating-pump/prepared.json')
    assert report['sourceSha256']==prepared['observerSha256']==OBSERVER_SHA
    assert prepared['criticalMutationCallAstUnchanged']and report['additionalGameMemoryWrites']==0 and report['additionalSuspendOrResumeCalls']==0
    assert report['rotatingVmEdgeHardwareSlot']and report['mainPumpPreservedDuringStageVmWindow']
    assert report['mainPumpOutsideVmWindowMayStillHaveRngWatchGap']
    pumps=rows(native/'rotating-watch-pump-events.jsonl')
    assert len(pumps)==report['rotatingVmWindowPumpEvents']>0
    assert SHA(blob(native/'rotating-watch-pump-events.jsonl'))==report['rotatingVmWindowPumpSha256']
    for p in pumps:
        assert p['pc']==0x47d720 and p['debugAddresses'][1]==0x47d720 and p['debugStatus']&2
        assert p['debugAddresses'][0]==0x44dbd0 and p['readOnly']and not p['providedToEngine']
        assert p['debugAddresses'][2]==(0x40f2a7 if p['vmCallActive']else 0x40f2a2)
        assert not p['scriptRngWatchActive']or p['debugAddresses'][3]==0x4db508
    edges=rows(native/'stage-object-vm-window-events.jsonl');active=None;pairs=0
    for i,e in enumerate(edges,1):
        assert e['ordinal']==i and e['readOnly']and not e['providedToEngine']
        if e['pc']==0x40f2a2:
            assert active is None;active=e
        else:
            assert e['pc']==0x40f2a7 and active is not None
            assert e['vm']==active['vm']and e['callEntryOrdinal']==active['ordinal']and e['stage']==active['stage']
            pairs+=1;active=None
    assert active is None and pairs>0
    for name in ['static-control','rotating']:
        owned=load(H/'rotating-edge-component-retry3'/name/'report.json')
        assert owned['perThreadOrderEqual']and not owned['unknownExceptions']and not owned['error']and owned['exitCode']==0
        assert owned['toolSha256']==SHA(blob(R/'tools/th14-rotating-edge-watch-component-nov05.py'))
    accesses=rows(native/'script-rng-access-events.jsonl')
    stage3=[p for p in pumps if p['stage']==3]
    assert stage3,'The target transition must have actual pump observations'
    arm=load(native/'script-rng-watch-arm.json')
    first=accesses[0]
    actual_before_first=[p for p in stage3 if p['hostMonotonicNs']<first['hostMonotonicNs']and p['precedingPlayerCallbacks']==first['precedingPlayerCallbacks']]
    # Absence is retained as a failed coverage result, never replaced by a
    # guessed time or an invented resource-pump row.
    proof.update(schema='th14/rng-pump-register-trace/1',parentVerifierSha256=PARENT_SHA,
        derivedDecoderChangesOnlyObserverBindings=True,rotatingVmEdgeHardwareSlot=True,
        actualMainPumpEvents=len(pumps),actualStage3MainPumpEvents=len(stage3),
        pairedStageVmCalls=pairs,allObservedVmEdgesPaired=True,
        actualPumpInFirstAccessPlayerInterval=bool(actual_before_first),
        actualPumpsInFirstAccessPlayerInterval=len(actual_before_first),
        rngWatchArmCallback=arm['precedingPlayerCallbacks'],firstAccessCallback=first['precedingPlayerCallbacks'],
        pumpClockInferred=False,mainPumpOutsideVmWindowMayStillHaveGap=True,
        exactOriginalFrameEntryRecovered=False,portableValuesCompared=False,
        ordinaryIndependentTimingAccepted=False,completeGame=False)
    return proof

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--native',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    native=a.native.resolve();out=a.output.resolve();assert native.is_relative_to(R/'artifacts/th14')and out.is_relative_to(R/'artifacts/th14')and not out.exists()
    value=verify(native);out.write_text(json.dumps(value,indent=2)+'\n')
    print(json.dumps({k:value[k]for k in ['verifiedFiniteOriginalRegisterReadEvidence','accessEvents','arithmeticPairsEqual','actualMainPumpEvents','actualStage3MainPumpEvents','actualPumpInFirstAccessPlayerInterval','pairedStageVmCalls','ordinaryIndependentTimingAccepted']}))
