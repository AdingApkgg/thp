"""Recompute the seed-store diagnostic's complete retained fields and five strict VM failures."""
from pathlib import Path
import argparse,array,gzip,hashlib,importlib.util,json,struct
R=Path(__file__).resolve().parents[1];SHA=lambda b:hashlib.sha256(b).hexdigest()


def evidence(home):
    home=home.resolve(strict=True);assert home.is_relative_to(R/'artifacts/th14');N=home/'native';M=home/'current-compare';bindings={}
    def raw(path):
        p=path.resolve(strict=True);assert p.is_relative_to(R);b=p.read_bytes();bindings[p.relative_to(R).as_posix()]=dict(bytes=len(b),sha256=SHA(b));return b
    def load(path):return json.loads(raw(path))
    def module(name,path):
        raw(path);spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
    native_proof=module('seed_store_native',R/'tools/th14-stage3-seed-store-evidence-v3-nov01.py').evidence(home);assert native_proof==load(home/'seed-store-verified-v3.json')
    for name,binding in native_proof['bindings'].items():assert SHA(raw(R/name))==binding['sha256']
    end=load(home/'retained-follower-end.json');report=load(M/'report.json');count=26000
    assert end['exitCode']==1 and end['guardStop']is None and not end['strictPassed']and end['diagnosticPrefixOnly']
    assert report['callbacks']==count and report['diagnosticPrefixOnly']and report['completed']and report['selection']==[0,0,0,1]
    assert report['noNativePublicationValuesProvidedToEngine']and report['noPerFrameStateOverrides']and report['hostNormalBoundaryMode']=='none'
    assert report['normalBoundaryObservation']is report['normalVmBoundaryObservation']is None
    assert report['comparisonToolSha256']==SHA(raw(R/'tools/th14-compare-native-campaign-retained-camera-nov01.mjs'))
    B=R/'artifacts/th14/controller-polar-production-nov01/production-core/observer-build.json';build=load(B)
    assert build['wasmSha256']==report['wasmSha256']==SHA(raw(B.parent/'observer.wasm'))=='af9ec42926395595779d2744868a5cbff22cb9ddb39588e1a76265c395cffd9a'
    for row in build['objectBindings']:assert SHA(raw(Path(row['path'])))==row['sha256']
    for inventory in ['sourceHashes','headerHashes']:
        for name,digest in build[inventory].items():assert SHA(raw(B.parent/'source'/name))==digest
    assert len(raw(N/'selected-state.u32'))==count*128 and raw(N/'selected-state.u32')==raw(M/'selected-state.u32')
    camera=raw(N/'world-camera.raw');assert len(camera)==count*0x124
    expected=array.array('I',(struct.unpack_from('<I',camera,n*0x124+o)[0]for n in range(count)for o in [*range(0,88,4),0x104,0x108,0x10c])).tobytes()
    assert expected==raw(M/'portable-camera.u32')and raw(N/'hud-score.u32')==raw(M/'portable-hud.u32')
    decoder=module('seed_vm303',R/'tools/th14-hud-completion-evidence-check-oct25.py');fields=load(M/'live-report.json')['fields'];assert len(fields)==303;rows_total=0;diffs=[]
    for path in sorted(N.glob('live-vms-callback-*.json')):
        callback=int(path.stem.rsplit('-',1)[1]);rows=load(path)['rows'];got=load(M/f'portable-live-{callback}.json');blobs=[bytes.fromhex(r['rawVmHex'])for r in rows]
        handles={struct.unpack_from('<I',b,0x570)[0]:struct.unpack_from('<I',b,0x540)[0]for b in blobs}
        assert len(handles)==len(rows)and[r['handle']for r in rows]==[r[0]for r in got]
        for row,blob,values in zip(rows,blobs,got,strict=True):
            want=decoder.vm_words(blob,handles);assert len(want)==len(values)==303
            for field,(a,b)in enumerate(zip(want,values,strict=True)):
                if a!=b:
                    assert(row['file'],row['script'],fields[field],b)==(8,149,'worldZ',0)
                    diffs.append(dict(callback=callback,handle=row['handle'],field=fields[field],file=8,script=149,native=a,portable=b))
        rows_total+=len(rows)
    assert rows_total==1111 and len(diffs)==5
    schema=module('seed_combat_v3',R/'tools/th14-combat-pool-readonly-v3-oct25.py');index=load(N/'combat-pool-index.json');assert index['fields']==json.loads(json.dumps(schema.SCHEMA))
    for entry in index['snapshots']:
        b=raw(N/'combat-pools'/entry['file']);assert SHA(b)==entry['sha256'];obs=json.loads(gzip.decompress(b));got=load(M/f"combat-{entry['callback']}.json")
        assert(obs['callback'],obs['stage'],obs['stageFrame'])==(got['callback'],got['stage'],got['stageFrame'])
        for family,layout in index['fields'].items():
            expected=[[r['slot']if offset is None else struct.unpack_from('<H'if family=='bullets'and name=='state'else'<I',bytes.fromhex(r['rawHex']),offset)[0]for name,offset in layout]for r in obs['original'][family]]
            assert expected==got['rows'][family]
    pubs=[json.loads(x)for x in raw(N/'allocation-events.jsonl').decode().splitlines()];got=load(M/'portable-allocations-initial-through-1000.json')
    assert[(x['handle'],x['file'],x['script'])for x in pubs]==[(x['handle'],x['file'],x['script'])for x in got]
    events=[json.loads(x)for x in raw(N/'seed-store-instruction-events.jsonl').decode().splitlines()];before,after=events
    assert before['mainThreadRegisters']['eip']==0x47e660 and after['mainThreadRegisters']['eip']==0x47e65b
    assert before['activeVmSnapshot']['callIdentityStillMatches']and before['activeVmSnapshot']['identity']['file']==5 and before['activeVmSnapshot']['identity']['script']==2
    assert not after['activeVmSnapshot']['observedCallActive']
    return dict(verifiedFiniteSeedStoreAndRetainedPrefixFailure=True,sourceCoreCommit='85811ecb5f4a6e4bb3a2add3c0c6aebb31813dd6',wasmSha256=build['wasmSha256'],callbacks=count,diagnosticPrefixOnly=True,actualWorkerSeedStoreObservedBeforeAndAfter=True,mainObservedAtVmReturnBeforeStoreAndNextCallAfterStore=True,normalVmWindowEdges=native_proof['normalVmWindowEdges'],allSelected32Camera25Hud2AndInitialPublicationsExact=True,vmRows=rows_total,vmFields=303,rawHandlesAndRegistryOrderExact=True,vmDifferentWords=5,remainingDifferences=diffs,allDifferentWordsScript149WorldZ=True,actualEnemyIdentityAtTheseBirthsNotObserved=True,allCapturedCombatWordsEqual=True,combatCheckpoints=len(index['snapshots']),initialPublications=len(pubs),strictPassed=False,noExtraVmBoundaryClockSupplied=True,noNativeValuesProvidedToEngine=True,preciseEarlierMainRngReadOrderAccepted=False,oldInsideVmSeedInterleaveFailureClosed=False,firstObserverAndCheckerFailuresRetained=True,observationBudgetBytes=128*1024**2,immutableInputCacheExcludedByExistingCapturePolicy=True,originalNaturalReplayEndAccepted=False,ordinaryOriginalMenuAccepted=False,independentSchedulingAccepted=False,completeGame=False,nativeEquivalent=False,bindings=bindings,verifierSha256=SHA(Path(__file__).read_bytes()))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--case',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--check',action='store_true');a=p.parse_args();out=a.output.resolve();assert out.is_relative_to(R/'artifacts/th14')or out.is_relative_to(R/'docs/porting');result=evidence(a.case)
    if a.check:assert json.loads(out.read_bytes())==result
    else:out.write_text(json.dumps(result,indent=2)+'\n',encoding='utf8')
    print(json.dumps({k:v for k,v in result.items()if k not in ['bindings','remainingDifferences']}))
