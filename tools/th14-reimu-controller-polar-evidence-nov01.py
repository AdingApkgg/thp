"""Verify controller stack producers, a retained strict failure and fresh candidate regressions."""
from pathlib import Path
import argparse,array,ast,gzip,hashlib,importlib.util,json,struct
R=Path(__file__).resolve().parents[1];SHA=lambda b:hashlib.sha256(b).hexdigest()


def evidence(home):
    home=home.resolve(strict=True);assert home.is_relative_to(R/'artifacts/th14');bindings={}
    def raw(p):
        p=p.resolve(strict=True);assert p.is_relative_to(R)
        b=p.read_bytes();bindings[p.relative_to(R).as_posix()]=dict(bytes=len(b),sha256=SHA(b));return b
    def load(p):return json.loads(raw(p))
    def module(name,path):
        raw(path);spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
    def pe(data):
        base=struct.unpack_from('<I',data,0x3c)[0];assert data[base:base+4]==b'PE\0\0'
        count=struct.unpack_from('<H',data,base+6)[0];size=struct.unpack_from('<H',data,base+20)[0];opt=base+24
        assert struct.unpack_from('<H',data,opt)[0]==0x10b
        sections=[struct.unpack_from('<IIII',data,opt+size+i*40+8)for i in range(count)]
        def offset(rva):
            for virtual_size,address,raw_size,start in sections:
                if address<=rva<address+max(virtual_size,raw_size):return start+rva-address
            assert rva<struct.unpack_from('<I',data,opt+60)[0];return rva
        return opt,offset
    # The extra native observer changes observation only. Its game writes and
    # explicit thread suspend/resume calls must be identical ASTs to the base.
    source=raw(R/'tools/th14-reimu-controller-z-context-live-observer-nov01.py')
    normal=raw(R/'tools/th14-native-campaign-observer-oct25.py')
    assert SHA(normal)=='ce533a0503163d69a6b93f3a132b950ba96b40cc24bc1f9bbabd9b33b6ca2da7'
    def calls(text,name):return [ast.dump(x,include_attributes=False)for x in ast.walk(ast.parse(text))if isinstance(x,ast.Call)and isinstance(x.func,ast.Attribute)and x.func.attr==name]
    for name in ['WriteProcessMemory','SuspendThread','ResumeThread']:assert calls(source,name)==calls(normal,name)
    N=R/'artifacts/th14/reimu-controller-z-live-context-nov01/native';original=load(N/'report.json')
    assert original['sourceSha256']==SHA(source)and original['childExited']and not original['error']and not original['debugErrors']
    assert original['hardwareBreakpointsOnly']and original['instructionBytesPatched']==original['rngOrCounterWrites']==0
    assert not original['inputInjected']and original['gameStateWordWrites']==1 and original['caseInitialization']['attractBitClearOnly']
    assert original['diagnosticPrefixOnly']and not original['fullReplayAccepted']and original['callbacks']==36826
    assert original['controllerProbeDone']and original['controllerProbeReads']==23 and original['controllerProbeWrites']==13027
    events=raw(N/'controller-polar-z-stack-events.jsonl');assert SHA(events)==original['controllerProbeEventsSha256']
    events=[json.loads(x)for x in events.decode().splitlines()];reads=[];previous=None;writes=0
    for row in events:
        assert row['readOnly']and not row['providedToEngine']and row['address']==original['controllerProbeSlot']
        if row['event']=='scratch-write-completed':previous=row;writes+=1
        else:
            assert row['event']=='polar-z-before-read'and row['pc']==0x4138ca and row['originalInstructionBytes'].startswith('f30f5845d4')
            assert row['lastObservedWrite']==previous and row['address']==row['registers']['ebp']-0x2c
            if previous:assert previous['word']==row['word']and previous['hostMonotonicNs']<row['hostMonotonicNs']
            reads.append(row)
    assert writes==13027 and len(reads)==23 and [r['bombElapsed']for r in reads]==list(range(18,41))
    modules=load(N/'controller-live-modules.json');assert modules['readOnly']
    dlls=[r for r in modules['rows']if r['name'].lower()=='ntdll.dll'and r['base']<2**32];assert len(dlls)==1
    dll=dlls[0];dll_path=Path(dll['path']);data=dll_path.read_bytes();dll_sha=SHA(data)
    assert dll_sha=='23d7772221e7a763ccf3f3fe39592086eb3091603554c4981f0ab430fa2ca686'
    opt,offset=pe(data);assert struct.unpack_from('<I',data,opt+56)[0]==dll['bytes']
    table=offset(struct.unpack_from('<I',data,opt+96)[0]);count=struct.unpack_from('<I',data,table+24)[0]
    functions,names,ordinals=struct.unpack_from('<III',data,table+28);exports={}
    for i in range(count):
        p=offset(struct.unpack_from('<I',data,offset(names)+i*4)[0]);name=data[p:data.index(0,p)].decode('ascii')
        ordinal=struct.unpack_from('<H',data,offset(ordinals)+i*2)[0];exports[name]=struct.unpack_from('<I',data,offset(functions)+ordinal*4)[0]
    rva=exports['RtlLeaveCriticalSection'];assert rva==333408
    prefix=data[offset(rva):offset(rva)+18];assert prefix.hex()=='8bff558bec83ec0853568b750857834608ff'
    pc=dll['base']+rva+10;classified=[];counts={'initialLastWriterUnobserved':0,'overlayTail':0,'shakeScriptRng':0,'opaqueRetirement':0}
    words=load(home/'controller-context/controller-polar-words.json');assert len(words)==original['callbacks']
    for r in reads:
        w=r['lastObservedWrite'];callback=r['precedingPlayerCallbacks'];actual=words[callback-1];assert actual[0]==callback
        if w is None:kind='initialLastWriterUnobserved';assert r['bombElapsed']==18
        else:
            assert w['pc']==pc and w['registers']['esp']==w['address']and w['registers']['esi']==w['word']
            assert w['originalInstructionBytes']==prefix[10:18].hex()and struct.unpack_from('<I',bytes.fromhex(w['stackHex']))[0]==w['word']
            frame=struct.unpack('<16I',bytes.fromhex(w['frameHex']))
            if frame[1]==0x47e7a0:kind='overlayTail';assert w['word']==0
            elif frame[1]==0x40338a:kind='shakeScriptRng';assert frame[6]==0x46cecf and w['word']==0x4db508
            else:kind='opaqueRetirement';assert frame[1]==0x46d4a7 and frame[8]==0x46d18c and w['word']not in (0,0x4db508)
        counts[kind]+=1;known=bool(actual[2]);equal=r['word']==actual[1]
        if kind=='opaqueRetirement':assert not known and not equal and actual[1]==0
        else:assert known and equal
        classified.append(dict(callback=callback,bombElapsed=r['bombElapsed'],producer=kind,known=known,wordEqual=equal))
    assert counts==dict(initialLastWriterUnobserved=1,overlayTail=14,shakeScriptRng=7,opaqueRetirement=1)
    # Bind the full immutable candidate sources and object graph; the sole
    # fixture additions and derived driver additions are read-only exports.
    B=home/'candidate-v2/observer-build.json';build=load(B);old_path=R/'artifacts/th14/reimu-bomb-z-producer-nov01/production-core/observer-build.json';old=load(old_path)
    assert build['isolatedPrototypeOnly']and not build['rootProductionSourcesModified']and build['all141ObjectsRecompiledForChangedClassLayout']
    assert build['readOnlyObserver']and not build['nativeRngCounterInputOrPointerValuesProvided']and not build['vmCallbackPointersWrapped']
    assert build['wasmSha256']==SHA(raw(B.parent/'observer.wasm'))=='9b9a2045fb31217fb823ed4f2910cae22938ecc3d8cfb4196aec5812ed9fab3b'
    changed=[]
    for inventory in ['sourceHashes','headerHashes']:
        assert build[inventory].keys()==old[inventory].keys()
        for name,digest in build[inventory].items():
            assert SHA(raw(B.parent/'source'/name))==digest
            if digest!=old[inventory][name]:changed.append(name)
    assert set(changed)=={'th12_web/cpp/game/'+x for x in ['NativeStackTh14.hpp','AnmManager.cpp','BombController.cpp','ScreenShake.hpp','GameBattle.cpp']}
    assert len(build['objectBindings'])==141
    for row in build['objectBindings']:assert SHA(raw(Path(row['path'])))==row['sha256']
    assert SHA(raw(home/'build-candidate-v2.py'))==build['buildToolSha256']
    fixture=raw(Path(build['fixtureGraphRoot'])).decode().replace('\r\n','\n')
    assert fixture=='#include "H:/code/thp/runtimes/th12/th12_web/tests/cpp/th14-initialization-clock-fixture-nov01.cpp"\nAPI(observed_controller_polar_word) u32 observed_controller_polar_word(){return session.animations.th14_native_stack.controller_scratch;}\nAPI(observed_controller_polar_known) u32 observed_controller_polar_known(){return session.animations.th14_native_stack.controller_scratch_known;}\n'
    for path,digest in build['fixtureDependencyHashes'].items():assert SHA(raw(Path(path)))==digest
    driver=raw(R/'tools/th14-controller-polar-candidate-compare-nov01.mjs').decode();base=raw(R/'tools/th14-compare-native-campaign-retained-camera-nov01.mjs').decode()
    base=base.replace('function compare(index){','const controllerWords=[];\nfunction compare(index){\n controllerWords.push([index+1,c.observed_controller_polar_word()>>>0,c.observed_controller_polar_known()>>>0]);',1)
    marker="write(resolve(out,'report.json')"
    base=base.replace(marker,"report.controllerPolarDiagnosticOnly=true;report.opaqueControllerRetirementAddressStillUnresolved=true;\nwrite(resolve(out,'controller-polar-words.json'),JSON.stringify(controllerWords)+'\\n',{flag:'wx'});\n"+marker,1)
    assert driver==base
    # The new context trace fails at an earlier initialization-RNG boundary in
    # both old and new core. No delivery boundary is inferred to turn it green.
    context=home/'controller-context';baseline=home/'baseline-controller-context'
    report=load(context/'report.json');previous=load(baseline/'report.json')
    assert report['differenceCounts']==previous['differenceCounts']=={'21':14403,'22':1702}
    for name in ['selected-state.u32','portable-camera.u32','portable-hud.u32','portable-allocations-initial-through-1000.json',*[p.name for p in context.glob('portable-live-*.json')],*[p.name for p in context.glob('combat-*.json')]]:assert raw(context/name)==raw(baseline/name)
    assert load(home/'controller-context-process-end.json')['exitCode']==load(home/'baseline-controller-context-process-end.json')['exitCode']==1
    # Recompute every stage6 VM and combat field from original raw bytes.
    N=R/'artifacts/th14/focused-hit-live-writer-nov01/native';M=home/'stage6';previous=R/'artifacts/th14/focused-hit-live-writer-nov01/current-compare-v2'
    report=load(M/'report.json');assert report['callbacks']==90012 and report['wasmSha256']==build['wasmSha256']and report['diagnosticPrefixOnly']
    assert report['noPerFrameStateOverrides']and report['noNativePublicationValuesProvidedToEngine']and report['normalVmBoundaryObservation']is None
    assert raw(N/'selected-state.u32')==raw(M/'selected-state.u32')==raw(previous/'selected-state.u32')
    camera=raw(N/'world-camera.raw');expected=array.array('I',(struct.unpack_from('<I',camera,n*0x124+off)[0]for n in range(90012)for off in [*range(0,88,4),0x104,0x108,0x10c])).tobytes()
    assert expected==raw(M/'portable-camera.u32')and raw(N/'hud-score.u32')==raw(M/'portable-hud.u32')
    pubs=[json.loads(x)for x in raw(N/'allocation-events.jsonl').decode().splitlines()];actual=load(M/'portable-allocations-initial-through-1000.json')
    assert [(r['handle'],r['file'],r['script'])for r in pubs]==[(r['handle'],r['file'],r['script'])for r in actual]
    decoder=module('controller_vm_words',R/'tools/th14-hud-completion-evidence-check-oct25.py');fields=load(M/'live-report.json')['fields'];vm_rows=0;diffs=[]
    for path in sorted(N.glob('live-vms-callback-*.json')):
        callback=int(path.stem.rsplit('-',1)[1]);rows=load(path)['rows'];values=load(M/f'portable-live-{callback}.json');assert values==load(previous/f'portable-live-{callback}.json')
        blobs=[bytes.fromhex(r['rawVmHex'])for r in rows];handles={struct.unpack_from('<I',b,0x570)[0]:struct.unpack_from('<I',b,0x540)[0]for b in blobs}
        assert len(handles)==len(rows)and [r['handle']for r in rows]==[r[0]for r in values]
        for row,blob,got in zip(rows,blobs,values,strict=True):
            want=decoder.vm_words(blob,handles);assert len(want)==len(got)==303
            for i,(a,b)in enumerate(zip(want,got,strict=True)):
                if a!=b:assert(row['file'],row['script'],fields[i],b)==(8,149,'worldZ',0);diffs.append(dict(callback=callback,handle=row['handle'],field=fields[i]))
        vm_rows+=len(rows)
    assert vm_rows==2021 and len(diffs)==22
    schema=module('controller_combat_v3',R/'tools/th14-combat-pool-readonly-v3-oct25.py');index=load(N/'combat-pool-index.json');assert index['fields']==json.loads(json.dumps(schema.SCHEMA))
    changed_combat=[]
    for entry in index['snapshots']:
        b=raw(N/'combat-pools'/entry['file']);assert SHA(b)==entry['sha256'];obs=json.loads(gzip.decompress(b));actual=load(M/f"combat-{entry['callback']}.json");old_actual=load(previous/f"combat-{entry['callback']}.json")
        assert(obs['callback'],obs['stage'],obs['stageFrame'])==(actual['callback'],actual['stage'],actual['stageFrame'])
        for family,layout in index['fields'].items():
            expected=[[row['slot']if off is None else struct.unpack_from('<H'if family=='bullets'and name=='state'else'<I',bytes.fromhex(row['rawHex']),off)[0]for name,off in layout]for row in obs['original'][family]]
            assert expected==actual['rows'][family]
            for row_idx,(before,after)in enumerate(zip(old_actual['rows'][family],expected,strict=True)):
                for field,(a,b)in enumerate(zip(before,after,strict=True)):
                    if a!=b:changed_combat.append(dict(callback=entry['callback'],family=family,row=row_idx,field=layout[field][0],before=a,after=b))
    assert len(index['snapshots'])==936 and changed_combat==[dict(callback=89730,family='areas',row=2,field='z',before=0,after=0x4db508)]
    assert load(home/'stage6-process-end.json')['exitCode']==1 and not load(M/'live-report.json')['allLiveValuesEqual']
    regressions=home/'full-regressions';end=load(regressions/'end.json');assert end['allCasesActuallyExecuted']and end['strictPasses']==end['independentPasses']==11
    plan=load(regressions/'plan.json');assert plan['originalProcessesStarted']==0 and plan['previousPassesNotInherited']and plan['wasmSha256']==build['wasmSha256']
    results=[]
    for case in end['results']:
        C=regressions/case['key'];p=load(C/'plan.json');v=load(C/'raw-verified.json');terminal=load(C/'process-end.json')
        assert terminal['exitCode']==0 and terminal['guardStop']is None and terminal['strictPassed']and case['independentVerifierExitCode']==0
        assert v['verifiedFiniteEvidence']and not v['diagnosticPrefixOnly']and v['originalNaturalReplayEndObserved']and v['wasmSha256']==build['wasmSha256']
        for name,binding in v['bindings'].items():assert SHA(raw(R/name))==binding['sha256']
        report=load(C/'model/report.json');assert report['stableMenuAfter90Ticks'][0]==2 and report['stableMenuAfter90Ticks'][5]==3
        assert sum(q.stat().st_size for q in C.rglob('*')if q.is_file())<=128*1024**2
        results.append(dict(key=case['key'],callbacks=case['callbacks'],selection=p['selection'],vmRows=v['vm303Rows'],combatCheckpoints=v['combatCheckpoints'],strictPassed=True,independentRawVerified=True))
    return dict(verifiedFiniteControllerStackProducerCandidate=True,candidateWasmSha256=build['wasmSha256'],baselineProductionWasmSha256=old['wasmSha256'],rootProductionSourcesModifiedAtCandidateBuild=False,compiledCoreObjects=141,changedGameFiles=sorted(changed),nativeDiagnosticCallbacks=36826,nativeStackReadSamples=23,knownStackSamplesEqual=22,unresolvedRetirementStackSamples=1,producerCounts=counts,stackSampleResults=classified,ntdll=dict(sha256=dll_sha,loadedModuleMapVerified=True,export='RtlLeaveCriticalSection',exportRva=rva,postPushEsiOffset=10),initialFirstReadLastWriterNotObserved=True,contextBaselineAndCandidateStrictFailed=True,contextInitializationRngFailureUnchanged=True,contextSelectedCameraHudVmCombatAndInitialPublicationsUnchanged=True,stage6Callbacks=90012,stage6VmRows=vm_rows,stage6VmFields=303,stage6VmDifferentWordsStill22=True,stage6StrictPassed=False,stage6CombatCheckpoints=936,stage6AllCapturedCombatWordsNowEqual=True,stage6OnlyChangedCombatWord=changed_combat[0],freshCompleteFiniteRegressions=results,regressionCallbacks=sum(r['callbacks']for r in results),allElevenStrictAndIndependentRawPassed=True,nativeValuesProvidedToEngine=False,opaqueRetirementAndEnemyAddressesStillUnresolved=True,phasedShakeStackProducerUnproved=True,wholeModeEquivalenceAccepted=False,ordinaryOriginalMenuAccepted=False,independentSchedulingAccepted=False,originalWholePixelsOrPcmAccepted=False,browserAcceptance=False,completeGame=False,nativeEquivalent=False,bindings=bindings,verifierSha256=SHA(Path(__file__).read_bytes()))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--case',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--check',action='store_true');a=p.parse_args();out=a.output.resolve();assert out.is_relative_to(R/'artifacts/th14')or out.is_relative_to(R/'docs/porting');result=evidence(a.case)
    if a.check:assert json.loads(out.read_bytes())==result
    else:out.write_text(json.dumps(result,indent=2)+'\n',encoding='utf8')
    print(json.dumps({k:v for k,v in result.items()if k not in ['bindings','stackSampleResults','freshCompleteFiniteRegressions']}))
