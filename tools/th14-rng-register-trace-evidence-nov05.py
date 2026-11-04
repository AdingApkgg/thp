"""Seal a terminated original prefix and decode stopped-register RNG values.

Output contains counts, instruction addresses and paths/hashes only. Original
registers, RNG seeds, memory and game assets remain in the private raw records.
No native value is provided to the portable engine by this checker.
"""
from pathlib import Path
import argparse, hashlib, importlib, json, struct, sys

R=Path(__file__).resolve().parents[1]
H=R/'artifacts/th14/script-rng-read-generation-nov05'
SHA=lambda b:hashlib.sha256(b).hexdigest()

def verify(native):
    bindings={}
    def raw(path):
        value=path.read_bytes();bindings[path.relative_to(R).as_posix()]=dict(bytes=len(value),sha256=SHA(value));return value
    def load(path):return json.loads(raw(path))
    def rows(path):return [json.loads(line)for line in raw(path).splitlines()if line]
    case=native.parent;end=load(case/'process-end.json');report=load(native/'report.json')
    assert end['guardStop']is None and end['exitCode']==1
    assert report['callbacks']==35000 and report['childExited']and not report['error']and not report['debugErrors']
    assert report['observerTerminationRequested']and not report['observedForcedReplayEndMenu']
    assert report['configuredMusicAndSoundVolumeZero']and report['gameStateWordWrites']==1 and report['rngOrCounterWrites']==0
    assert report['instructionBytesPatched']==0 and not report['inputInjected']
    assert report['sourceSha256']==SHA(raw(native/'observer-source.py'))==SHA(raw(H/'observer-pending-status/observer.py'))=='26727dd09ec942e04e9def563c5ec8b56e6a010912f44e4ed1b28809bb7ce596'
    assert report['sourceFullReplaySha256']=='c48412a95f0fe9f685d97574e8ab0655d41e44ff9c41fda7bf788589b1b29c74'
    for name,key,stride in [('selected-state.u32','selectedSha256',128),('player-host-monotonic.u64','playerHostTimesSha256',8),
            ('world-camera.raw','worldCameraSha256',292),('world-camera-tail.u32','worldCameraTailSha256',8),
            ('replay-cursor.u32','replayCursorSha256',56),('hud-score.u32','hudScoreSha256',8)]:
        data=raw(native/name);assert len(data)==35000*stride and SHA(data)==report[key]
    assert report['scriptRngAccessWatchArmed']and not report['scriptRngAccessWatchStillActive']
    assert report['scriptRngPostRestoreReceiptAccesses']==64 and not report['scriptRngAccessValuesProvidedToEngine']
    accesses=rows(native/'script-rng-access-events.jsonl');assert len(accesses)==report['scriptRngRegisterAccessEvents']<=512
    assert SHA(raw(native/'script-rng-access-events.jsonl'))==report['scriptRngAccessSha256']
    arm=load(native/'script-rng-watch-arm.json');assert arm['stage']==3 and arm['workerPc']==0x435b11
    assert arm['playerAndVmEdgesPreserved']and arm['mainResourcePumpObservationTemporarilyReplaced']
    component=load(H/'component/report.json');assert component['passed']and component['cases']==210
    assert component['toolSha256']==SHA(raw(R/'tools/th14-rng-register-generation-component-nov05.py'))
    sys.path.insert(0,str(R/'tools'));image=importlib.import_module('th12-pe').Image('H:/Games/th/14/th14.exe')
    assert SHA(image.data)==component['originalExecutableSha256']==report['executableSha256']
    contracts={x['after']:x for x in component['instructionCases']};counts={};mismatch={};pending=None;last_store=None
    pairs=0;leading_stores=0;reload_changed=0;unpaired_reloads=0;unknown_pcs={};last_seq=arm['debugEventSequence'];register_values_checked=0
    step=lambda value:((((value^0x9630)-0x6553)&65535)<<2|((((value^0x9630)-0x6553)&65535)>>14))&65535
    for index,row in enumerate(accesses,1):
        assert row['ordinal']==index and row['stage']==3 and row['readOnly']and not row['gameValuesProvidedToEngine']
        assert row['crossThreadInstructionOrderNotAsserted']and not row['exactOriginalScheduleRecovered']
        assert row['debugEventSequence']>last_seq;last_seq=row['debugEventSequence']
        assert row['debugAddresses'][3]==0x4db508 and row['debugStatus']&8 and(row['debugControl']>>28)&15==7
        regs=row['registers'];assert regs['eip']==row['pc']
        contract=contracts.get(row['pc'])if regs['esi']==0x4db508 else None
        if contract is None:
            assert not row['instructionValueDecoded']and row['instructionContract']is None and row['valueRetainedByTrappedInstruction']is None
            key=str(row['pc']);unknown_pcs[key]=unknown_pcs.get(key,0)+1;continue
        c=row['instructionContract'];assert c['kind']==contract['kind']and c['instructionPc']==contract['pc']and c['recovery']==contract['recovery']
        assert c['instructionBytes']==contract['bytes']==image.read(contract['pc'],contract['after']-contract['pc']).hex()
        kind=contract['kind'];recovery=contract['recovery']
        value=((regs['eax']&65535)^0x9630)if recovery=='xorAX'else(regs['eax']if recovery=='AX'else regs['ecx'])&65535
        assert row['instructionValueDecoded']and row['valueRetainedByTrappedInstruction']==value
        register_values_checked+=1;counts[kind]=counts.get(kind,0)+1
        observed=struct.unpack_from('<H',bytes.fromhex(row['rngHexAtObservation']))[0]
        if observed!=value:mismatch[kind]=mismatch.get(kind,0)+1
        if kind.startswith('mix'):
            assert pending is None,'A second native mix was observed without its store; do not discard a missing hardware event'
            pending=dict(width=16 if kind=='mix16'else 32,input=value,ordinal=index)
        elif kind.startswith('store'):
            width=16 if kind=='store16'else 32
            if pending is None:
                assert pairs==0 and leading_stores==0,'Only one leading partial call is supported';leading_stores+=1
            else:
                assert width==pending['width'];expected=step(pending['input']);expected=step(expected)if width==32 else expected
                assert value==expected,'Stopped-register store differs from the original RNG arithmetic';pairs+=1;pending=None
            last_store=dict(width=width,value=value)
        else:
            assert kind=='returnReload16'
            if last_store is None:unpaired_reloads+=1
            else:
                assert last_store['width']==16;reload_changed+=value!=last_store['value']
    assert pairs>0 and register_values_checked==report['scriptRngDecodedRegisterValues']
    assert report['pendingCrossThreadHardwareStatePreserved']and report['unrecognizedExceptionPolicyUnchanged']
    clock=rows(native/'debug-event-clock.jsonl')
    deferred=rows(native/'pending-debug-context-deferrals.jsonl')if report['pendingDebugContextDeferrals']else[]
    assert len(deferred)==report['pendingDebugContextDeferrals']
    if deferred:assert SHA(raw(native/'pending-debug-context-deferrals.jsonl'))==report['pendingDebugContextDeferralsSha256']
    matched=0
    for row in deferred:
        assert row['debugStatus']&15 and not row['contextWritten']and not row['exceptionIgnored']
        matched+=any(x['threadId']==row['threadId']and x['pc']==row['pc']and x['debugEventSequence']>row['debugEventSequence']and(x['debugStatus']&row['debugStatus']&15)for x in clock)
    preflight=load(H/'preflight-pending-status/verified.json');assert preflight['verifiedNativePreflight']and preflight['observerSha256']==report['sourceSha256']
    return dict(schema='th14/rng-register-trace/1',verifiedFiniteOriginalRegisterReadEvidence=True,callbacks=35000,
        nativeDebugExceptions=0,selection=[0,1,1,1],diagnosticPrefixOnly=True,naturalReplayEndAccepted=False,
        accessEvents=len(accesses),decodedRegisterValues=register_values_checked,instructionCaseCounts=counts,
        globalSnapshotMismatchCounts=mismatch,arithmeticPairsEqual=pairs,leadingPartialStores=leading_stores,
        trailingPartialRead=bool(pending),unpairedReturnReloads=unpaired_reloads,returnReloadsDifferentFromOwnEarlierStore=reload_changed,
        unclassifiedAccessPcs=unknown_pcs,unclassifiedAccessValuesAccepted=False,
        pendingContextUpdatesDeferred=len(deferred),laterOwnHardwareEventsMatched=matched,
        nativeValuesProvidedToEngine=False,portableValuesCompared=False,mainResourcePumpObservationHasDeclaredGap=True,
        exactOriginalScheduleRecovered=False,ordinaryIndependentTimingAccepted=False,originalStartupCauseProven=False,
        completeGame=False,nativeEquivalent=False,observerSha256=report['sourceSha256'],bindings=bindings,
        verifierSha256=SHA(Path(__file__).read_bytes()))

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--native',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--check',action='store_true');a=p.parse_args()
    native=a.native.resolve();out=a.output.resolve();assert native.is_relative_to(R/'artifacts/th14')and out.is_relative_to(R/'artifacts/th14')
    value=verify(native)
    if a.check:assert json.loads(out.read_bytes())==value
    else:
        assert not out.exists();out.write_text(json.dumps(value,indent=2)+'\n')
    print(json.dumps({k:value[k]for k in ['verifiedFiniteOriginalRegisterReadEvidence','accessEvents','decodedRegisterValues','arithmeticPairsEqual','globalSnapshotMismatchCounts','pendingContextUpdatesDeferred','ordinaryIndependentTimingAccepted']}))
