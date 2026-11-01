"""Recompute a finite Z-producer repair without accepting the remaining strict failure."""
from pathlib import Path
import argparse,array,gzip,hashlib,importlib.util,json,struct,subprocess,sys
R=Path(__file__).resolve().parents[1];SHA=lambda b:hashlib.sha256(b).hexdigest()

def evidence(home):
    home=home.resolve(strict=True);assert home.is_relative_to(R/'artifacts/th14');bindings={}
    def raw(p):
        p=p.resolve(strict=True);assert p.is_relative_to(R)
        b=p.read_bytes();bindings[p.relative_to(R).as_posix()]=dict(bytes=len(b),sha256=SHA(b));return b
    def load(p):return json.loads(raw(p))
    def module(name,path):
        raw(path);spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
    build_path=home/'production-core/observer-build.json';build=load(build_path);wasm=raw(build_path.parent/'observer.wasm')
    assert len(build['objectBindings'])==141 and build['all141ObjectsRecompiledForChangedClassLayout']
    assert SHA(wasm)==build['wasmSha256']=='31e86f11380950643cac3f7382c52c2f2a0704f4978836277982c22aa637d287'
    assert wasm==raw(home/'candidate/observer.wasm')
    for row in build['objectBindings']:assert SHA(raw(Path(row['path'])))==row['sha256']
    for name,digest in {**build['sourceHashes'],**build['headerHashes']}.items():
        p=R/'runtimes/th12'/name
        if name=='th12_web/cpp/game/ResourceCrypt.cpp':p=R/'tools/tmp/github-source-release/runtimes/th12'/name
        assert SHA(raw(p))==digest,name
    for name,digest in build['fixtureDependencyHashes'].items():assert SHA(raw(Path(name)))==digest
    integrated=load(home/'integrated.json');assert integrated['exactTestedSourceBytesIntegrated']and len(integrated['changes'])==5
    for row in integrated['changes']:assert SHA(raw(R/row['path']))==row['sha256']
    native=load(home/'public-native/report.json');assert len(native['cases'])==64
    assert native['originalInstructionBytesPatched']==0 and native['polarZNeverWrittenByObserverDuringExecution']
    assert native['actualCollectorAndGeometryAndBombCallbackExecuted']and native['factoryIsDeclaredRecordedReturnBoundary']
    assert native['toolSha256']==SHA(raw(home/'public-native/run-tool.py'))==SHA(raw(R/'tools/th14-reimu-bomb-polar-native-nov01.py'))
    assert native['originalExecutableSha256']=='f08e885e28d2e0fc8c579e88034dd7de8f2a648d8f08ce781cf08eadc9ffe353'
    for row in native['cases']:
        assert row['factory']['script']==58 and row['factory']['position'][2]==row['firstZRead']['value']
        if row['alignment']!=4:continue
        last=row['firstZRead']['lastOriginalWriter']
        if not row['areaCircle']and row['targetRectangle']:
            assert last['pc']==0x451543 and row['firstZRead']['value']==0x451548
        elif row['areaCircle']and not row['targetRectangle']:
            assert last is None and row['firstZRead']['value']==row['priorScratch']
        else:assert last['pc']==0x404d70
    component=home/'public-component-v3';cb=load(component/'build.json')
    assert cb['coreBuildSha256']==SHA(raw(build_path))and cb['fixtureSha256']==SHA(raw(R/cb['fixture']))
    assert cb['toolSha256']==SHA(raw(R/'tools/th14-build-reimu-bomb-polar-nov01.py'))
    assert cb['wasmSha256']==SHA(raw(component/'stack.wasm'))
    checker=R/'tools/th14-reimu-bomb-polar-check-nov01.mjs';raw(checker)
    subprocess.run(['C:/nvm4w/nodejs/node.exe',str(checker),'--native',str(home/'public-native'),'--build',str(component),'--output',str(component/'verified.json')],check=True,capture_output=True)
    control=load(component/'verified.json');assert control['nativeCasesCompared']==32 and control['oldZeroZControlsFailed']==20 and control['otherAlignmentNotAccepted']
    vm=module('polar_vm_fields',R/'tools/th14-hud-completion-evidence-check-oct25.py')
    N=R/'artifacts/th14/reimua-easy-current-natural-nov01/native';original=load(N/'report.json');count=original['callbacks'];assert count==100311
    assert original['childExited']and not original['error']and original['observedForcedReplayEndMenu']
    assert original['hardwareBreakpointsOnly']and original['instructionBytesPatched']==original['rngOrCounterWrites']==0
    assert original['gameStateWordWrites']==1 and original['caseInitialization']['attractBitClearOnly']and not original['inputInjected']
    assert original['sourceSha256']==SHA(raw(N/'observer-source.py'))==SHA(raw(R/'tools/th14-native-campaign-observer-oct25.py'))
    camera=raw(N/'world-camera.raw');assert len(camera)==count*0x124
    offsets=[*range(0,88,4),0x104,0x108,0x10c]
    expected_camera=array.array('I',(struct.unpack_from('<I',camera,n*0x124+o)[0]for n in range(count)for o in offsets)).tobytes()
    schema=module('polar_combat_schema',R/'tools/th14-combat-pool-readonly-v3-oct25.py');index=load(N/'combat-pool-index.json');assert index['fields']==json.loads(json.dumps(schema.SCHEMA))
    fields=load(home/'candidate-current-reimua/live-report.json')['fields'];assert len(fields)==303
    differences=[];snapshots=[]
    for model in [R/'artifacts/th14/reimua-easy-current-natural-nov01/current-compare/model',home/'candidate-current-reimua']:
        report=load(model/'report.json');assert report['completed']and report['callbacks']==count and report['selection']==[0,0,0,1]
        assert report['hostNormalBoundaryMode']=='none'and report['normalBoundaryObservation']is report['normalVmBoundaryObservation']is None
        assert report['noNativePublicationValuesProvidedToEngine']and report['noPerFrameStateOverrides']
        assert report['comparisonToolSha256']==SHA(raw(R/'tools/th14-compare-native-campaign.mjs'))
        assert not report['completeGame']and not report['nativeEquivalent']
        assert raw(N/'selected-state.u32')==raw(model/'selected-state.u32')
        assert expected_camera==raw(model/'portable-camera.u32')and raw(N/'hud-score.u32')==raw(model/'portable-hud.u32')
        diff=[];snapshot_rows=0
        for path in sorted(N.glob('live-vms-callback-*.json')):
            callback=int(path.stem.rsplit('-',1)[1]);rows=load(path)['rows'];actual=load(model/f'portable-live-{callback}.json')
            blobs=[bytes.fromhex(row['rawVmHex'])for row in rows];handles={struct.unpack_from('<I',b,0x570)[0]:struct.unpack_from('<I',b,0x540)[0]for b in blobs}
            assert len(handles)==len(rows)and [r['handle']for r in rows]==[r[0]for r in actual]
            for row,blob,values in zip(rows,blobs,actual,strict=True):
                expected=vm.vm_words(blob,handles);assert len(expected)==len(values)==303
                for i,(a,b)in enumerate(zip(expected,values,strict=True)):
                    if a!=b:diff.append(dict(callback=callback,handle=row['handle'],file=row['file'],script=row['script'],field=fields[i],native=a,portable=b))
            snapshot_rows+=len(rows)
        differences.append(diff);snapshots.append(snapshot_rows)
        for entry in index['snapshots']:
            compressed=raw(N/'combat-pools'/entry['file']);assert SHA(compressed)==entry['sha256']
            observed=json.loads(gzip.decompress(compressed));actual=load(model/f"combat-{entry['callback']}.json")
            assert (observed['callback'],observed['stage'],observed['stageFrame'])==(actual['callback'],actual['stage'],actual['stageFrame'])
            for family,layout in index['fields'].items():
                expected=[[row['slot']if offset is None else struct.unpack_from('<H'if family=='bullets'and name=='state'else'<I',bytes.fromhex(row['rawHex']),offset)[0]for name,offset in layout]for row in observed['original'][family]]
                assert expected==actual['rows'][family]
        pubs=[json.loads(line)for line in raw(N/'allocation-events.jsonl').decode().splitlines()];actual=load(model/'portable-allocations-initial-through-1000.json')
        assert [(r['handle'],r['file'],r['script'])for r in pubs]==[(r['handle'],r['file'],r['script'])for r in actual]
    assert snapshots==[983,983]and len(index['snapshots'])==976
    assert len(differences[0])==42 and len(differences[1])==1
    remaining=dict(callback=90000,handle=2396479310,file=8,script=149,field='worldZ',native=371563684,portable=0)
    assert differences[1]==[remaining]and remaining in differences[0]
    assert all(d['field']=='worldZ'and d['script']in[42,145,58,149]for d in differences[0])
    strict_end=load(home/'candidate-process-end.json');assert strict_end['exitCode']==1 and not strict_end['strictPassed']
    regressions=[];generic=R/'tools/th14-verify-native-campaign.py';raw(generic)
    cases=[('marisaa-natural','artifacts/th14/marisaa-easy-passive-full-nov01/native',80594),('reimub-full','artifacts/th14/reimub-normal-construction-current-oct30',122537),('reimua-extra','artifacts/th14/extra-current-natural-nov01/native',38403)]
    # Resolve the retained Reimu B native home from the actual declared plan.
    plan=load(R/cases[1][1]/'plan.json');cases[1]=(cases[1][0],plan['native'],cases[1][2])
    for name,native_home,callbacks in cases:
        model=home/('regression-'+name);end=load(home/('regression-'+name+'-process-end.json'));start=load(home/('regression-'+name+'-process-start.json'));report=load(model/'report.json')
        assert end['strictPassed']and end['exitCode']==0 and end['guardStop']is None
        assert report['callbacks']==callbacks and report['wasmSha256']==build['wasmSha256']
        assert report['comparisonToolSha256']==SHA(raw(Path(start['argv'][1])))
        if name=='reimua-extra':
            erratum=load(home/'regression-driver-binding-erratum.json');assert erratum['originalReceiptUnmodified']and erratum['strictResultUnchanged']
            assert erratum['originalReceiptSha256']==SHA(raw(home/erratum['receipt']))and erratum['actualDriverSha256']==report['comparisonToolSha256']
        else:assert end['driverSha256']==report['comparisonToolSha256']
        output=home/('regression-'+name+'-raw-verified.json')
        run=subprocess.run([sys.executable,'-X','utf8',str(generic),'--native',str(R/native_home),'--model',str(model),'--build',str(build_path),'--output',str(output)],capture_output=True)
        assert run.returncode==0,run.stderr.decode(errors='replace')[-2000:]
        verified=load(output);assert verified['verifiedFiniteEvidence']and not verified['diagnosticPrefixOnly']and verified['originalNaturalReplayEndObserved']
        for name2,binding in verified['bindings'].items():assert SHA(raw(R/name2))==binding['sha256']
        regressions.append(dict(name=name,callbacks=callbacks,vmRows=verified['vm303Rows'],combatCheckpoints=verified['combatCheckpoints'],strictPassed=True))
    return dict(verifiedFinitePolarZProducerRepair=True,parentCoreCommit='9b4201204405e1d7f6d5f28d6c71faf603b2836d',testedWasmSha256=build['wasmSha256'],all141ProductionObjectsRecompiled=True,privateAndPublicBuildByteIdentical=True,originalComponentCases=64,acceptedReferenceAlignment=4,componentCasesCompared=32,oldZeroZControlsFailed=20,otherAlignmentNotAccepted=True,reimuaEasyCallbacks=count,vmRows=983,vmFields=303,vmDifferencesBefore=42,vmDifferencesAfter=1,correctedVmWords=41,remainingDifference=remaining,strictReimuaEasyPassed=False,allSelectedCameraHudCombatAndInitialPublicationsExact=True,combatCheckpoints=976,regressions=regressions,nativeValuesProvidedToEngine=False,independentSchedulingAccepted=False,originalWholePixelsOrPcmAccepted=False,browserAcceptance=False,completeGame=False,nativeEquivalent=False,bindings=bindings,verifierSha256=SHA(Path(__file__).read_bytes()))

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--case',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--check',action='store_true');a=p.parse_args();out=a.output.resolve();assert out.is_relative_to(R/'artifacts/th14')or out.is_relative_to(R/'docs/porting')
    result=evidence(a.case)
    if a.check:assert json.loads(out.read_bytes())==result
    else:out.write_text(json.dumps(result,indent=2)+'\n',encoding='utf8')
    print(json.dumps({k:v for k,v in result.items()if k!='bindings'}))
