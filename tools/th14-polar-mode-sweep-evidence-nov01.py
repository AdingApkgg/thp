"""Collect current complete finite passes while retaining fidelity, protocol and budget failures."""
from pathlib import Path
import argparse,array,hashlib,importlib.util,json
R=Path(__file__).resolve().parents[1];SHA=lambda b:hashlib.sha256(b).hexdigest()

def evidence(home):
    home=home.resolve(strict=True);assert home.is_relative_to(R/'artifacts/th14');bindings={}
    def raw(p):
        p=p.resolve(strict=True);assert p.is_relative_to(R);b=p.read_bytes();bindings[p.relative_to(R).as_posix()]=dict(bytes=len(b),sha256=SHA(b));return b
    def load(p):return json.loads(raw(p))
    def module(name,path):
        raw(path);spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
    mode=module('polar_complete_mode',R/'tools/th14-polar-current-mode-evidence-nov01.py')
    first=home/'current-mode-matrix';second=home/'current-mode-matrix-v2';progress=load(first/'matrix-progress.json');terminal=load(second/'matrix-end.json')
    assert progress['completedCases']==7 and terminal['allCasesActuallyExecuted']and len(terminal['results'])==6
    assert not(first/'matrix-end.json').exists()
    passes=[('sakuyab-hard',home/'sakuyab-hard-current'),('sakuyaa-hard',home/'sakuyaa-hard-current'),*[(k,first/k)for k in ['marisab-easy','marisaa-lunatic','marisab-lunatic','sakuyaa-easy']],('reimub-easy',second/'reimub-easy')]
    accepted=[]
    for key,path in passes:
        proof=mode.evidence(path)
        for name,binding in proof['bindings'].items():assert SHA(raw(R/name))==binding['sha256']
        accepted.append(dict(key=key,selection=proof['selection'],callbacks=proof['callbacks'],stagesObserved=proof['stagesObserved'],vmRows=proof['vmRows'],vmFields=303,combatCheckpoints=proof['combatCheckpoints'],initialPublications=proof['orderedInitialPublications'],strictPassed=True,independentRawPayloadRecheckPassed=True,naturalEndAnd90StableMenuTicks=True))
    assert sum(r['callbacks']for r in accepted)==890105
    budget=first/'reimub-easy';old_end=load(budget/'process-end.json');assert old_end['guardStop']=='observation-budget'and not old_end['strictPassed']and old_end['exitCode']==0
    before=budget/'model';after=second/'reimub-easy/model';native=R/load(budget/'plan.json')['native'];camera=raw(native/'world-camera.raw')
    assert len(camera)==238922*0x124 and raw(before/'native-camera.raw')==camera and not(after/'native-camera.raw').exists()
    for name in ['selected-state.u32','portable-camera.u32','portable-hud.u32','portable-allocations-initial-through-1000.json']:
        assert raw(before/name)==raw(after/name)
    for path in before.glob('portable-live-*.json'):assert raw(path)==raw(after/path.name)
    old_report=load(before/'report.json');new_report=load(after/'report.json')
    assert {k:v for k,v in old_report.items()if k!='comparisonToolSha256'}=={k:v for k,v in new_report.items()if k!='comparisonToolSha256'}
    index=load(native/'combat-pool-index.json');digest=hashlib.sha256()
    for entry in index['snapshots']:
        name=f"combat-{entry['callback']}.json";a=(before/name).read_bytes();b=(after/name).read_bytes();assert a==b;digest.update(name.encode()+b'\0'+a)
    assert sum(p.stat().st_size for p in budget.rglob('*')if p.is_file())>128*1024**2
    assert sum(p.stat().st_size for p in (second/'reimub-easy').rglob('*')if p.is_file())<=128*1024**2
    decoder=module('sweep_vm_words',R/'tools/th14-hud-completion-evidence-check-oct25.py');failed=[]
    failures=[('marisaa-hard',first/'marisaa-hard'),*[(k,second/k)for k in ['reimua-hard','reimua-lunatic','sakuyab-easy','sakuyab-lunatic']]]
    allowed_drivers={SHA(raw(R/'tools/th14-compare-native-campaign.mjs')),SHA(raw(R/'tools/th14-compare-native-campaign-retained-camera-nov01.mjs'))}
    for key,path in failures:
        plan=load(path/'plan.json');end=load(path/'process-end.json');model=path/'model';report=load(model/'report.json');native=R/plan['native']
        assert end['exitCode']==1 and end['guardStop']is None and not end['strictPassed']and report['completed']and report['callbacks']==plan['callbacks']
        assert report['wasmSha256']=='31e86f11380950643cac3f7382c52c2f2a0704f4978836277982c22aa637d287'
        assert report['comparisonToolSha256']==plan['driverSha256']in allowed_drivers
        assert raw(native/'selected-state.u32')==raw(model/'selected-state.u32')and raw(native/'hud-score.u32')==raw(model/'portable-hud.u32')
        a=array.array('I',raw(native/'world-camera.raw'));b=array.array('I',raw(model/'portable-camera.u32'));n=report['callbacks'];assert len(a)==n*73 and len(b)==n*25
        offsets=[*range(22),65,66,67];counts={}
        for k,off in enumerate(offsets):
            total=sum(a[i*73+off]!=b[i*25+k]for i in range(n))
            if total:counts[str(k)]=total
        cr=load(model/'camera-report.json');assert counts==cr['counts']
        live=load(model/'live-report.json');fields=live['fields'];assert len(fields)==303;vm_diffs=[];vm_rows=0
        for p in sorted(native.glob('live-vms-callback-*.json')):
            callback=int(p.stem.rsplit('-',1)[1]);rows=load(p)['rows'];actual=load(model/f'portable-live-{callback}.json');blobs=[bytes.fromhex(r['rawVmHex'])for r in rows]
            import struct
            handles={struct.unpack_from('<I',blob,0x570)[0]:struct.unpack_from('<I',blob,0x540)[0]for blob in blobs}
            assert len(handles)==len(rows)and[r['handle']for r in rows]==[r[0]for r in actual]
            for row,blob,values in zip(rows,blobs,actual,strict=True):
                expected=decoder.vm_words(blob,handles);assert len(expected)==len(values)==303
                for i,(x,y)in enumerate(zip(expected,values,strict=True)):
                    if x!=y:vm_diffs.append(dict(callback=callback,handle=row['handle'],file=row['file'],script=row['script'],field=fields[i],native=x,portable=y))
            vm_rows+=len(rows)
        assert len(vm_diffs)==sum(x['differenceCount']for x in live['snapshots'])and bool(counts or vm_diffs)
        combat=load(model/'combat-snapshots.json')
        failed.append(dict(key=key,callbacks=n,strictPassed=False,selected32AndHudByteEqual=True,cameraDifferenceCounts=counts,vmRows=vm_rows,vmFields=303,vmDifferentWords=len(vm_diffs),vmDifferences=vm_diffs,rawHandlesAndRegistryOrderExact=True,reportedCombatWordsEqual=combat['allCapturedCombatWordsEqual'],reportedCombatDifferenceCount=len(combat['differences']),failureCameraAndVmRecomputedFromRaw=True,combatReportOnlyNotIndependentPassAcceptance=True))
    rejected=[]
    for key,path in [('reimub-hard',first/'reimub-hard'),('reimub-lunatic',second/'reimub-lunatic')]:
        plan=load(path/'plan.json');end=load(path/'process-end.json');log=raw(path/'model.log').decode(errors='replace');native=R/plan['native']
        assert end['exitCode']==1 and not end['strictPassed']and end['guardStop']is None
        assert 'Missing later-stage observation scene-camera-copy-events.jsonl'in log and not(native/'scene-camera-copy-events.jsonl').exists()and not(path/'model/report.json').exists()
        rejected.append(dict(key=key,reason='Missing retained Scene-copy observations; full comparison rejected',fidelityNotAssessed=True,missingGateNotWaived=True))
    assert len(accepted)==7 and len(failed)==5 and len(rejected)==2
    return dict(verifiedFiniteCurrentModeSweep=True,sourceCoreCommit='bd70b911a3c6a362331f561407a74b6aca3e031f',uniqueModeRecordsAssessed=14,actualRunAttempts=15,completeFiniteStrictPasses=accepted,strictPassCases=7,strictPassCallbacks=890105,strictFidelityFailures=failed,fidelityFailureCases=5,protocolRejected=rejected,protocolRejectedCases=2,priorOutputBudgetStoppedCaseRetained=True,outputBudgetBytes=128*1024**2,rawNativeCameraBytesNotDuplicatedOnRerun=len(camera),allRerunSelectedCameraHudVmCombatAndPublicationsByteIdentical=True,rerunCombatPayloadSha256=digest.hexdigest(),productionEngineChanged=False,naturalModeInventoryPairs=30,allStageEntryInventoryPairs=25,wholeModeEquivalenceAccepted=False,ordinaryOriginalMenuAccepted=False,originalWholePixelsOrPcmAccepted=False,browserAcceptance=False,completeGame=False,nativeEquivalent=False,bindings=bindings,verifierSha256=SHA(Path(__file__).read_bytes()))

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--case',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--check',action='store_true');a=p.parse_args();out=a.output.resolve();assert out.is_relative_to(R/'artifacts/th14')or out.is_relative_to(R/'docs/porting');result=evidence(a.case)
    if a.check:assert json.loads(out.read_bytes())==result
    else:out.write_text(json.dumps(result,indent=2)+'\n',encoding='utf8')
    print(json.dumps({k:v for k,v in result.items()if k not in ['bindings','strictFidelityFailures','completeFiniteStrictPasses']}))
