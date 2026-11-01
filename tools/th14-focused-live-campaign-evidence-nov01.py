"""Recompute a finite strict failure and connect every remaining VM Z to its actual birth."""
from pathlib import Path
import argparse,array,gzip,hashlib,importlib.util,json,struct
R=Path(__file__).resolve().parents[1];SHA=lambda b:hashlib.sha256(b).hexdigest()

def evidence(home):
    home=home.resolve(strict=True);assert home.is_relative_to(R/'artifacts/th14');bindings={}
    def raw(p):
        p=p.resolve(strict=True);assert p.is_relative_to(R);b=p.read_bytes();bindings[p.relative_to(R).as_posix()]=dict(bytes=len(b),sha256=SHA(b));return b
    def load(p):return json.loads(raw(p))
    def module(name,path):
        raw(path);spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
    live=module('actual_focused_live_chain',R/'tools/th14-focused-hit-live-evidence-nov01.py').evidence(home)
    assert live==load(home/'verified-v2.json')and live['verifiedBirths']==6 and live['liveEnemyIdentityObservedAtEveryAcceptedBirth']
    for name,binding in live['bindings'].items():assert SHA(raw(R/name))==binding['sha256']
    native=home/'native';model=home/'current-compare-v2';original=load(native/'report.json');report=load(model/'report.json');count=90012
    end=load(home/'comparison-process-end.json');assert end['exitCode']==1 and not end['strictPassed']and end['guardStop']is None and end['diagnosticPrefixOnly']
    assert original['callbacks']==report['callbacks']==count and report['completed']and report['diagnosticPrefixOnly']
    assert report['selection']==report['declaredSelection']==[0,0,0,1]and report['hostNormalBoundaryMode']=='none'
    assert report['normalBoundaryObservation']is report['normalVmBoundaryObservation']is None
    assert report['noNativePublicationValuesProvidedToEngine']and report['noPerFrameStateOverrides']
    assert report['comparisonToolSha256']==SHA(raw(R/'tools/th14-compare-native-campaign.mjs'))
    build_path=R/'artifacts/th14/reimu-bomb-z-producer-nov01/production-core/observer-build.json';build=load(build_path)
    assert build['wasmSha256']==report['wasmSha256']==SHA(raw(build_path.parent/'observer.wasm'))=='31e86f11380950643cac3f7382c52c2f2a0704f4978836277982c22aa637d287'
    for row in build['objectBindings']:assert SHA(raw(Path(row['path'])))==row['sha256']
    for name,digest in {**build['sourceHashes'],**build['headerHashes']}.items():
        p=R/'runtimes/th12'/name
        if name=='th12_web/cpp/game/ResourceCrypt.cpp':p=R/'tools/tmp/github-source-release/runtimes/th12'/name
        assert SHA(raw(p))==digest
    selected=raw(native/'selected-state.u32');assert len(selected)==count*128 and selected==raw(model/'selected-state.u32')and SHA(selected)==original['selectedSha256']
    camera=raw(native/'world-camera.raw');assert len(camera)==count*0x124
    offsets=[*range(0,88,4),0x104,0x108,0x10c];expected=array.array('I',(struct.unpack_from('<I',camera,n*0x124+o)[0]for n in range(count)for o in offsets)).tobytes()
    assert expected==raw(model/'portable-camera.u32')and raw(native/'hud-score.u32')==raw(model/'portable-hud.u32')
    decoder=module('focused_vm303',R/'tools/th14-hud-completion-evidence-check-oct25.py');fields=load(model/'live-report.json')['fields'];assert len(fields)==303
    births={r['handle']:r for r in live['births']};assert len(births)==6;differences=[];snapshots=[]
    for path in sorted(native.glob('live-vms-callback-*.json')):
        callback=int(path.stem.rsplit('-',1)[1]);rows=load(path)['rows'];actual=load(model/f'portable-live-{callback}.json');blobs=[bytes.fromhex(r['rawVmHex'])for r in rows]
        handles={struct.unpack_from('<I',b,0x570)[0]:struct.unpack_from('<I',b,0x540)[0]for b in blobs}
        assert len(handles)==len(rows)and[r['handle']for r in rows]==[r[0]for r in actual]
        for row,blob,values in zip(rows,blobs,actual,strict=True):
            words=decoder.vm_words(blob,handles);assert len(words)==len(values)==303
            for i,(a,b)in enumerate(zip(words,values,strict=True)):
                if a!=b:
                    assert fields[i]=='worldZ'and(row['file'],row['script'])==(8,149)and row['handle']in births
                    birth=births[row['handle']];assert birth['callback']<=callback and a==birth['worldZWord']and b==0
                    differences.append(dict(callback=callback,handle=row['handle'],field=fields[i],native=a,portable=b,birthCallback=birth['callback'],enemyInstance=birth['enemyInstance']))
        snapshots.append(dict(callback=callback,rows=len(rows)))
    assert differences and set(r['handle']for r in differences)==set(births)
    schema=module('focused_combat_v3',R/'tools/th14-combat-pool-readonly-v3-oct25.py');index=load(native/'combat-pool-index.json');assert index['fields']==json.loads(json.dumps(schema.SCHEMA))
    combat_differences=[]
    for entry in index['snapshots']:
        b=raw(native/'combat-pools'/entry['file']);assert SHA(b)==entry['sha256'];obs=json.loads(gzip.decompress(b));actual=load(model/f"combat-{entry['callback']}.json")
        assert(obs['callback'],obs['stage'],obs['stageFrame'])==(actual['callback'],actual['stage'],actual['stageFrame'])
        for family,layout in index['fields'].items():
            expected=[[row['slot']if off is None else struct.unpack_from('<H'if family=='bullets'and name=='state'else'<I',bytes.fromhex(row['rawHex']),off)[0]for name,off in layout]for row in obs['original'][family]]
            values=actual['rows'][family];assert len(expected)==len(values)
            for row_index,(want,got)in enumerate(zip(expected,values,strict=True)):
                assert len(want)==len(got)
                for field_index,(a,b)in enumerate(zip(want,got,strict=True)):
                    if a!=b:combat_differences.append(dict(callback=entry['callback'],stage=entry['stage'],stageFrame=entry['stageFrame'],family=family,row=row_index,field=layout[field_index][0],native=a,portable=b))
    assert combat_differences==[dict(callback=89730,stage=6,stageFrame=13156,family='areas',row=2,field='z',native=0x4db508,portable=0)]
    pubs=[json.loads(line)for line in raw(native/'allocation-events.jsonl').decode().splitlines()];actual=load(model/'portable-allocations-initial-through-1000.json')
    assert [(r['handle'],r['file'],r['script'])for r in pubs]==[(r['handle'],r['file'],r['script'])for r in actual]
    return dict(verifiedFiniteActualBirthAndRetainedStrictFailure=True,sourceCoreCommit='bd70b911a3c6a362331f561407a74b6aca3e031f',callbacks=count,diagnosticPrefixOnly=True,vmFields=303,vmSnapshots=snapshots,vmRows=sum(x['rows']for x in snapshots),vmDifferentWords=len(differences),allDifferentVmWordsExactlyActualScript149BirthPointers=True,actualLiveBirths=6,nonProducingWrappersWithoutEnemyIdentity=live['nonProducingWrappersWithoutEnemyIdentity'],allSelectedCameraHudAndInitialPublicationsExact=True,allCapturedCombatWordsEqual=False,combatDifferentWords=1,combatCheckpoints=len(index['snapshots']),initialPublications=len(pubs),remainingVmDifferences=differences,remainingCombatDifferences=combat_differences,strictPassed=False,originalCodeOrRngWrites=0,extraVmBoundaryClockSupplied=False,nativeValuesProvidedToEngine=False,productionAddressModelImplemented=False,naturalReplayEndAccepted=False,ordinaryOriginalMenuAccepted=False,independentSchedulingAccepted=False,originalWholePixelsOrPcmAccepted=False,browserAcceptance=False,completeGame=False,nativeEquivalent=False,bindings=bindings,verifierSha256=SHA(Path(__file__).read_bytes()))

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--case',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--check',action='store_true');a=p.parse_args();out=a.output.resolve();assert out.is_relative_to(R/'artifacts/th14')or out.is_relative_to(R/'docs/porting');result=evidence(a.case)
    if a.check:assert json.loads(out.read_bytes())==result
    else:out.write_text(json.dumps(result,indent=2)+'\n',encoding='utf8')
    print(json.dumps({k:v for k,v in result.items()if k not in ['bindings','remainingVmDifferences','remainingCombatDifferences']}))
