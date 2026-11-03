"""Verify original per-store observations without inferring an earlier thread PC."""
from pathlib import Path
import argparse, hashlib, json, struct

R=Path(__file__).resolve().parents[1]
sha=lambda raw:hashlib.sha256(raw).hexdigest()
PCS=[0x45610f,0x456123,0x456129,0x456133]
SIGNATURES=['66a310b54d00','66a308b54d00','c70514b54d0000000000','f3a5']


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--home',type=Path,default=R/'artifacts/th14/replay-rng-store-trace-nov04')
    parser.add_argument('--output',type=Path,default=R/'docs/porting/th14-replay-rng-store-trace-nov04.json')
    parser.add_argument('--check',action='store_true');args=parser.parse_args()
    home=args.home.resolve(strict=True);assert home.is_relative_to(R/'artifacts/th14');native=home/'native';bindings={}

    def read(path):
        raw=path.read_bytes();bindings[path.relative_to(R).as_posix()]=dict(bytes=len(raw),sha256=sha(raw));return raw

    def load(path):return json.loads(read(path))
    prepared=load(home/'prepared.json');plan=load(home/'plan.json');end=load(home/'process-end.json');report=load(native/'report.json')
    assert prepared['prepared'] and prepared['workerExecutionBreakpointPcs']==PCS
    assert prepared['preparerSha256']==sha(read(R/'tools/th14-prepare-replay-rng-store-observer-nov04.py'))
    assert prepared['baseObserverSha256']==sha(read(R/'tools/th14-native-campaign-observer-oct25.py'))
    source=read(home/'observer.py');assert sha(source)==prepared['observerSha256']==plan['sourceSha256']==report['sourceSha256']
    assert source==read(native/'observer-source.py') and b'SuspendThread'not in source and b'ResumeThread'not in source
    assert end['guardStop']is None and end['exitCode']==1
    assert report['childExited'] and not report['error'] and not report['debugErrors']
    assert report['diagnosticPrefixOnly'] and not report['observedForcedReplayEndMenu']
    assert report['callbacks']==plan['maximumCallbacks']==40000
    assert plan['selection']==[0,1,1,1] and report['hardwareBreakpointsOnly'] and report['instructionBytesPatched']==report['rngOrCounterWrites']==0
    assert report['gameStateWordWrites']==1 and report['caseInitialization']['attractBitClearOnly'] and not report['inputInjected']
    assert report['configuredMusicAndSoundVolumeZero'] and bytes.fromhex(report['configHex'])[0x22:0x24]==bytes(2)
    assert not report['actualAudioPcmMeasured'] and report['debuggerPausesAffectTiming']
    assert report['executableSha256']=='f08e885e28d2e0fc8c579e88034dd7de8f2a648d8f08ce781cf08eadc9ffe353'
    assert not report['replayRngStoreValuesProvidedToEngine'] and not report['replayRngStoreThreadSchedulingControlled']
    assert report['replayRngStoreAllInstructionsObservedBeforeExecution'] and report['replayRngStoreInstructionPcs']==PCS
    assert not report['originalOldRecordingOrderRecovered']
    selected=read(native/'selected-state.u32');assert len(selected)==40000*128 and sha(selected)==report['selectedSha256']
    stages=sorted({row[30]for row in struct.iter_unpack('<32I',selected)});assert stages==report['recordedStages'] and 2 in stages
    initial=load(native/'untouched-first-player.json');assert initial['words'][27:31]==plan['selection']
    rows_raw=read(native/'replay-rng-store-events.jsonl');assert sha(rows_raw)==report['replayRngStoreEventsSha256']
    rows=[json.loads(line)for line in rows_raw.splitlines()];assert len(rows)==report['replayRngStoreEvents'] and len(rows)>=4 and len(rows)%4==0
    groups=[]
    for start in range(0,len(rows),4):
        group=rows[start:start+4];stage=group[0]['stage'];assert 2<=stage<=6
        assert [row['pc']for row in group]==PCS and [row['ordinal']for row in group]==list(range(start+1,start+5))
        assert len({row['threadId']for row in group})==len({row['stage']for row in group})==len({row['replaySeedWord']for row in group})==1
        assert all(group[i]['hostMonotonicNs']<group[i+1]['hostMonotonicNs']for i in range(3))
        values=[]
        for index,row in enumerate(group):
            assert row['originalInstructionBytes']==SIGNATURES[index] and row['registers']['eip']==row['pc']
            assert row['workerInstructionStillPending'] and row['workerPriorStoresCompleted']==PCS[:index]
            assert row['hardwareExecutionBreakpoint'] and row['readOnly'] and not row['threadSchedulingControlled'] and not row['providedToEngine']
            assert row['debuggerPausesAffectTiming'] and row['mainThreadContextAtWorkerDebugEvent']['instructionPcAtEarlierStoreNotProven']
            main=row['mainThreadContextAtWorkerDebugEvent'];assert len(bytes.fromhex(main['stackHex']))==main['stackBytes']<=64 and not main['unwoundCallStack']
            words=struct.unpack('<HHIHHI',bytes.fromhex(row['rngHex']));values.append(dict(scriptSeed=words[0],scriptCalls=words[2],gameplaySeed=words[3],gameplayCalls=words[5]))
        final=[row for row in report['transitionEvents']if row['pc']==PCS[-1]and row['stage']==stage and row['threadId']==group[-1]['threadId']]
        assert len(final)==1 and final[0]['rngHex']==group[-1]['rngHex'] and final[0]['restoredReplaySeed']==group[-1]['replaySeedWord']
        groups.append(dict(stage=stage,replaySeed=group[0]['replaySeedWord'],precedingPlayerCallbacks=[row['precedingPlayerCallbacks']for row in group],
            mainPcsAtDebugEvents=[row['mainThreadContextAtWorkerDebugEvent']['registers']['eip']for row in group],rngAtBeforeStoreEvents=values))
    assert len({group['stage']for group in groups})==len(groups)
    comparison=load(home/'comparison/end.json');comparison_plan=load(home/'comparison/plan.json')
    assert comparison['diagnosticPrefixOnly'] and comparison['callbacks']==40000
    assert comparison['model']['guardStop']is None and comparison['verifier']is not None and comparison['verifier']['guardStop']is None
    assert comparison_plan['originalStoreEventClocksNotSubstituted'] and not comparison_plan['nativeRngOrStateValuesProvidedToEngine']
    model=home/'comparison/model';modeled=load(model/'report.json')
    assert modeled['callbacks']==40000 and modeled['diagnosticPrefixOnly']
    assert modeled['wasmSha256']=='1e15bb751d12dac304d3d48ec5f70c4a222221c6f4ce444ebb3507773e0e239d'
    assert modeled['comparisonToolSha256']==sha(read(R/'tools/th14-compare-native-campaign-retained-camera-nov01.mjs'))
    portable=read(model/'selected-state.u32');copied_native=read(model/'native-selected-state.u32');assert copied_native==selected and len(portable)==len(selected)
    counts=[0]*32;first_differences={}
    for callback,(left,right)in enumerate(zip(struct.iter_unpack('<32I',selected),struct.iter_unpack('<32I',portable),strict=True),1):
        for index in range(32):
            if left[index]!=right[index]:
                counts[index]+=1
                first_differences.setdefault(str(index),dict(callback=callback,stage=left[30],stageFrame=left[0],native=left[index],portable=right[index]))
    assert counts==[modeled['differenceCounts'].get(str(index),0)for index in range(32)]
    assert counts[21:23]==[9228,615] and counts[26]==77 and sum(counts)==9920
    first=first_differences['21'];assert first['callback']==30773 and first['stage']==3 and first['native']==45887 and first['portable']==44160
    final=next(group for group in groups if group['stage']==3)['rngAtBeforeStoreEvents'][-1]
    original_player=struct.unpack_from('<32I',selected,(first['callback']-1)*128)
    portable_player=struct.unpack_from('<32I',portable,(first['callback']-1)*128)
    advances=(original_player[22]-final['scriptCalls'])&0xffffffff;assert advances==24
    value=final['scriptSeed'];read(R/'runtimes/th12/th12_web/cpp/game/Rng.hpp')
    for _ in range(advances):
        mixed=((value^0x9630)-0x6553)&0xffff;value=((mixed<<2)|(mixed>>14))&0xffff
    assert value==original_player[21] and portable_player[21]==final['scriptSeed'] and original_player[22]==portable_player[22]
    passed_gates=[]
    for name in ('exceptions','timing','scene'):
        path=home/'comparison'/(name+'.json')
        if path.exists():
            receipt=load(path);assert receipt['passed'];passed_gates.append(name)
    if comparison['strictAndIndependentPassed']:
        assert comparison['model']['exitCode']==comparison['verifier']['exitCode']==0 and sum(counts)==0
        finite=load(home/'comparison/raw-verified.json')
        assert finite['verifiedFiniteEvidence'] and finite['diagnosticPrefixOnly'] and finite['callbacks']==40000
        assert finite['wasmSha256']==modeled['wasmSha256'] and passed_gates==['exceptions','timing','scene']
    result=dict(verifiedOriginalReplayRngIndividualStoreObservations=True,callbacks=40000,selection=plan['selection'],stagesObserved=stages,
        observedStoreBoundaryEvents=len(rows),workerBoundaryPcs=PCS,transitions=groups,allWorkerInstructionsStillPendingAtTheirEvents=True,
        configuredMusicAndSoundVolumeZero=True,actualAudioPcmMeasured=False,threadSchedulingControlled=False,debuggerPausesAffectTiming=True,
        instructionBytesPatched=0,rngValuesProvidedToEngine=False,mainPcAtEarlierStoreRecovered=False,oldRecordingOrderRecovered=False,
        currentCoreObservedPrefixStrictAndIndependentPassed=comparison['strictAndIndependentPassed'],
        currentCoreObservedPrefixSelected32DifferenceCounts=counts,currentCoreObservedPrefixPassedGates=passed_gates,
        currentCoreObservedPrefixFirstDifferences=first_differences,
        scriptRngAtObservedCounterClear=dict(seed=final['scriptSeed'],calls=final['scriptCalls']),
        firstDifferentPlayerScriptRng=dict(callback=30773,nativeSeed=original_player[21],portableSeed=portable_player[21],callsBoth=original_player[22]),
        scriptRngAdvancesBetweenCounterClearObservationAndPlayer=advances,scriptRngRecurrenceAfter24AdvancesMatchesOriginal=True,
        currentCoreObservedPrefixOnly=True,newStoreEventClocksSubstitutedIntoEngine=False,
        replayOrOrdinaryGameEquivalenceAccepted=False,oldRngOrBulletFailuresClosed=False,completeGame=False,nativeEquivalent=False,
        bindings=bindings,verifierSha256=sha(Path(__file__).read_bytes()))
    output=args.output.resolve();assert output.is_relative_to(R/'docs/porting')or output.is_relative_to(home)
    data=(json.dumps(result,indent=2)+'\n').encode()
    if args.check:assert output.read_bytes()==data
    else:assert not output.exists();output.write_bytes(data)
    print(json.dumps({key:value for key,value in result.items()if key not in('bindings','transitions')}))


if __name__=='__main__':main()
