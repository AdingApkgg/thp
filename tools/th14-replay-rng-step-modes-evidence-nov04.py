"""Bind current-core mode passes and keep the independently recounted old failure."""
from pathlib import Path
import argparse, hashlib, json

R=Path(__file__).resolve().parents[1];H=R/'artifacts/th14/replay-rng-restore-nov04'
sha=lambda raw:hashlib.sha256(raw).hexdigest()


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--check',action='store_true')
    parser.add_argument('--output',type=Path,default=R/'docs/porting/th14-replay-rng-step-modes-nov04.json');args=parser.parse_args();bindings={}
    def read(path):
        raw=path.read_bytes();bindings[path.relative_to(R).as_posix()]=dict(bytes=len(raw),sha256=sha(raw));return raw
    def load(path):return json.loads(read(path))
    end=load(H/'current-modes/end.json');plan=load(H/'current-modes/plan.json');build=load(H/'step-candidate/core/observer-build.json')
    assert end['casesCompleted']==16 and end['newModelRuns']==13 and not end['newOriginalProcessesLaunched']
    assert sha((H/'step-candidate/core/observer-build.json').read_bytes())==plan['buildSha256']
    assert build['wasmSha256']==end['sourceWasmSha256']==plan['coreWasmSha256']=='1e15bb751d12dac304d3d48ec5f70c4a222221c6f4ce444ebb3507773e0e239d'
    app_build=load(H/'gles-build/build.json');original_build_bytes=read(H/'production-core/build-before-publication-label.json')
    original_build=json.loads(original_build_bytes)
    assert sha(original_build_bytes)==app_build['coreBuildSha256']
    assert app_build['coreWasmSha256']==original_build['wasmSha256']==build['wasmSha256']
    assert app_build['coreObjects']==original_build['objectBindings']==build['objectBindings']
    read(H/'check-current-modes.py');cases=[];pairs=set();entries=set();failed=[]
    for row,case in zip(end['cases'],plan['cases'],strict=True):
        assert row['key']==case['key'] and row['selection']==case['selection']
        report=load(R/case['native']/'report.json');assert row['nativeReportSha256']==sha((R/case['native']/'report.json').read_bytes())
        assert report['callbacks']==row['callbacks']
        if not row['strictV4Passed']:
            # Exception rejection is explicit; any additional failure must be
            # audited and represented before this finite summary can publish.
            assert row['key']=='reimub-easy' and row['notRunOnCurrentCore'] and len(report['debugErrors'])==12
            failed.append(dict(key=row['key'],selection=row['selection'],callbacks=row['callbacks'],reportedDebugExceptions=12,currentCoreModelNotRun=True));continue
        assert not report['debugErrors']
        if row.get('newModelRun'):
            assert row['model']['exitCode']==row['verifier']['exitCode']==0 and row['model']['guardStop']is row['verifier']['guardStop']is None
            directory=H/'current-modes'/row['key'];raw=load(directory/'raw-verified.json')
        else:
            path=R/row['reusedCurrentCoreReceipt'];raw=load(path);assert sha(path.read_bytes())==row['reusedCurrentCoreReceiptSha256'];directory=path.parent
        assert raw['verifiedFiniteEvidence'] and raw['wasmSha256']==build['wasmSha256'] and raw['callbacks']==row['callbacks'] and raw['selection']==row['selection']
        for field in ('allSelected32Equal','allCamera25Equal','allHud2Equal','allVm303AndRegistryOrderEqual','allCapturedCombatWordsEqual'):assert raw[field]
        for name in ('exceptions','timing','scene'):
            receipt=load(directory/(name+'.json'));assert receipt['passed'] and receipt['nativeReportSha256']==row['nativeReportSha256']
        covered=set([7]if row['selection'][2]==4 else range(1,7))<=set(raw['stagesObserved'])
        pair=tuple(row['selection'][:3]);pairs.add(pair)
        if covered:entries.add(pair)
        cases.append(dict(key=row['key'],selection=row['selection'],callbacks=row['callbacks'],stagesObserved=raw['stagesObserved'],allTargetStageEntriesObserved=covered,vm303Rows=raw['vm303Rows'],combatCheckpoints=raw['combatCheckpoints'],newModelRun=row.get('newModelRun',False)))
    # Additional current-core Extra record already bound by the step-core proof.
    extra=load(H/'step-candidate/regressions/sakuyaa-extra/raw-verified.json')
    assert extra['verifiedFiniteEvidence'] and extra['wasmSha256']==build['wasmSha256'] and extra['selection']==[2,0,4,7] and extra['callbacks']==38977
    for name in ('exceptions','timing','scene'):assert load(H/'step-candidate/regressions/sakuyaa-extra'/(name+'.json'))['passed']
    pairs.add((2,0,4));entries.add((2,0,4))
    failure=load(H/'current-retained-36826/raw-failure-recount.json');failure_end=load(H/'current-retained-36826/process-end.json')
    assert failure_end['exitCode']==1 and failure_end['guardStop']is None and failure['coreWasmSha256']==build['wasmSha256']
    import struct
    a=read(H/'current-retained-36826/model/native-selected-state.u32');b=read(H/'current-retained-36826/model/selected-state.u32')
    assert len(a)==len(b)==36826*128 and sha(a)==failure['nativeRawSha256'] and sha(b)==failure['portableRawSha256']
    source=read(R/'artifacts/th14/reimu-controller-z-live-context-nov01/native/selected-state.u32');assert a==source[:len(a)]
    counts=[0]*32;first=None
    for callback,(x,y)in enumerate(zip(struct.iter_unpack('<32I',a),struct.iter_unpack('<32I',b),strict=True),1):
        for field in range(32):
            if x[field]!=y[field]:
                counts[field]+=1
                if first is None:first=dict(callback=callback,field=field,native=x[field],portable=y[field])
    assert counts==failure['fieldDifferences'] and counts[21:23]==[14403,1702] and sum(counts)==16105 and first==failure['firstDifference']
    result=dict(verifiedCurrentStepCoreModeEvidence=True,sourceGameplayCommit=plan['sourceCommit'],coreWasmSha256=build['wasmSha256'],
        retainedCasesAudited=16,newModelRuns=13,currentCoreReusedModeRuns=2,strictV4Passes=len(cases),cases=cases,rejectedOriginalRecords=failed,
        additionalSakuyaAExtraCallbacks=38977,totalPassedRecordsIncludingAdditionalExtra=len(cases)+1,
        totalPassedCallbacksIncludingAdditionalExtra=sum(case['callbacks']for case in cases)+38977,
        distinctModePairsWithV4PassIncludingAdditionalExtra=len(pairs),distinctModePairsWithV4PassAndAllTargetEntriesIncludingAdditionalExtra=len(entries),
        retainedOldFailureCallbacks=36826,retainedOldFailureRngSeedDifferences=14403,retainedOldFailureRngCounterDifferences=1702,
        retainedOldFailureFirstDifferentCallback=first['callback'],retainedOldFailureIndependentlyRecounted=True,
        applicationCoreBuildOriginalMetadataVerified=True,
        noNewOriginalProcessesForModeRegressions=True,physicalAudioDevicesOpened=0,oldRngOrBulletFailuresClosed=False,
        allModeEquivalenceAccepted=False,completeGame=False,nativeEquivalent=False,bindings=bindings,verifierSha256=sha(Path(__file__).read_bytes()))
    output=args.output.resolve();assert output.is_relative_to(R/'docs/porting')or output.is_relative_to(H)
    data=(json.dumps(result,indent=2)+'\n').encode()
    if args.check:assert output.read_bytes()==data
    else:assert not output.exists();output.write_bytes(data)
    print(json.dumps({k:v for k,v in result.items()if k not in('bindings','cases','rejectedOriginalRecords')}))


if __name__=='__main__':main()
