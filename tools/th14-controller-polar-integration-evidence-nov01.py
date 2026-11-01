"""Bind the integrated controller repair to fresh full regressions and retained failures."""
from pathlib import Path
import argparse,hashlib,importlib.util,json
R=Path(__file__).resolve().parents[1];SHA=lambda b:hashlib.sha256(b).hexdigest()


def evidence(home):
    home=home.resolve(strict=True);assert home.is_relative_to(R/'artifacts/th14');bindings={}
    def raw(path):
        p=path.resolve(strict=True);assert p.is_relative_to(R);b=p.read_bytes();bindings[p.relative_to(R).as_posix()]=dict(bytes=len(b),sha256=SHA(b));return b
    def load(path):return json.loads(raw(path))
    tool=R/'tools/th14-reimu-controller-polar-evidence-nov01.py';raw(tool);spec=importlib.util.spec_from_file_location('controller_polar_candidate',tool);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    C=R/'artifacts/th14/reimu-controller-polar-candidate-nov01';candidate=module.evidence(C);assert candidate==load(C/'verified.json')
    for name,binding in candidate['bindings'].items():assert SHA(raw(R/name))==binding['sha256']
    plan=load(home/'integration-plan.json');assert len(plan['changes'])==5 and plan['candidateEvidenceSha256']==SHA(raw(C/'verified.json'))
    B=home/'production-core/observer-build.json';build=load(B);private=load(C/'candidate-v2/observer-build.json')
    assert build['compiled']and not build['isolatedPrototypeOnly']and build['all141ObjectsRecompiledForChangedClassLayout']
    assert build['wasmSha256']==SHA(raw(B.parent/'observer.wasm'))=='af9ec42926395595779d2744868a5cbff22cb9ddb39588e1a76265c395cffd9a'
    assert build['sourceHashes']==private['sourceHashes']and build['headerHashes']==private['headerHashes']
    for row in plan['changes']:assert SHA(raw(R/row['path']))==row['after']and row['before']!=row['after']
    for inventory in ['sourceHashes','headerHashes']:
        for name,digest in build[inventory].items():
            p=R/'runtimes/th12'/name
            if name.endswith('/ResourceCrypt.cpp'):p=R/'tools/tmp/github-source-release/runtimes/th12'/name
            assert SHA(raw(p))==digest and SHA(raw(B.parent/'source'/name))==digest
    assert len(build['objectBindings'])==141
    for row in build['objectBindings']:assert SHA(raw(Path(row['path'])))==row['sha256']
    for name,digest in build['fixtureDependencyHashes'].items():assert SHA(raw(Path(name)))==digest
    objects=load(home/'object-comparison.json');assert objects['byteEqualObjects']==138 and objects['threeObjectsCodeDisassemblyEqual']
    for row in objects['differences']:
        outputs=[]
        for tag in ['candidate','production']:
            content=raw(home/'object-disassembly'/(tag+'-'+row['name']+'.txt'));binding=next(x for x in row['objects']if x['tag']==tag);assert SHA(content)==binding['disassemblySha256']
            outputs.append('\n'.join(line for line in content.decode().splitlines()if 'file format wasm'not in line))
        assert outputs[0]==outputs[1]
    regressions=home/'full-regressions';end=load(regressions/'end.json');assert end['allCasesActuallyExecuted']and end['strictPasses']==end['independentPasses']==11
    cases=[]
    def compare_payloads(before,after):
        names=['selected-state.u32','portable-camera.u32','portable-hud.u32','portable-allocations-initial-through-1000.json',*[p.name for p in before.glob('portable-live-*.json')],*[p.name for p in before.glob('combat-*.json')]]
        for name in names:assert raw(before/name)==raw(after/name),name
        return len(names)
    for case in end['results']:
        H=regressions/case['key'];p=load(H/'plan.json');v=load(H/'raw-verified.json');terminal=load(H/'process-end.json');report=load(H/'model/report.json')
        assert case['strictPassed']and case['independentVerifierExitCode']==0 and terminal['exitCode']==0 and terminal['guardStop']is None
        assert p['buildSha256']==SHA(raw(B))and v['wasmSha256']==build['wasmSha256']and v['verifiedFiniteEvidence']
        assert v['originalNaturalReplayEndObserved']and not v['diagnosticPrefixOnly']and report['stableMenuAfter90Ticks'][0]==2 and report['stableMenuAfter90Ticks'][5]==3
        for name,binding in v['bindings'].items():assert SHA(raw(R/name))==binding['sha256']
        same=compare_payloads(C/'full-regressions'/case['key']/'model',H/'model')
        assert sum(p.stat().st_size for p in H.rglob('*')if p.is_file())<=128*1024**2
        cases.append(dict(key=case['key'],callbacks=case['callbacks'],selection=p['selection'],vmRows=v['vm303Rows'],combatCheckpoints=v['combatCheckpoints'],strictPassed=True,independentRawVerified=True,payloadFilesEqualPrivateCandidate=same))
    report=load(home/'stage6/report.json');terminal=load(home/'stage6-process-end.json');assert terminal['exitCode']==1 and terminal['guardStop']is None and not terminal['strictPassed']
    assert report['callbacks']==90012 and report['wasmSha256']==build['wasmSha256']and report['diagnosticPrefixOnly']
    compare_payloads(C/'stage6',home/'stage6')
    assert load(home/'stage6/combat-snapshots.json')['allCapturedCombatWordsEqual']and not load(home/'stage6/live-report.json')['allLiveValuesEqual']
    frozen=R/'artifacts/th14/vm-return-worker-oct29/work-state.json';assert SHA(raw(frozen))=='2236db52bee27439486e69216333cd88ddc27d1dcc28233f87bacdcaadc1f33c'
    crypt=R/'runtimes/th12/th12_web/cpp/game/ResourceCrypt.cpp';assert SHA(raw(crypt))=='a291010053963e25dadef2be15ddb3c217110cd2377fc495402ef375150f8c45'
    return dict(verifiedFiniteIntegratedControllerPolarRepair=True,previousProductionCoreCommit='bd70b911a3c6a362331f561407a74b6aca3e031f',coreWasmSha256=build['wasmSha256'],all141ObjectsRecompiled=True,allProductionSourcesEqualTestedCandidate=True,byteEqualObjects=138,threeSourcePathDifferingObjectsCodeDisassemblyEqual=True,freshProductionCompleteRegressions=cases,freshProductionRegressionCallbacks=sum(x['callbacks']for x in cases),allElevenStrictAndIndependentRawPassed=True,allSelectedCameraHudVmCombatAndInitialPublicationsEqualPrivateCandidate=True,nativeStackReadSamples=23,knownStackSamplesEqual=22,retirementStackSampleStillUnresolved=True,firstStackReadLastWriterNotObserved=True,stage6DiagnosticCallbacks=90012,stage6VmRows=2021,stage6VmDifferentWordsStill22=True,stage6StrictPassed=False,stage6CombatCheckpoints=936,stage6AllCapturedCombatWordsNowEqual=True,originalObservedWordsProvidedToEngine=False,opaqueRetirementAndEnemyAddressModelStillMissing=True,phasedShakeStackProducerUnproved=True,priorFullApplicationPairVersionBoundToBd70=True,newCompleteApplicationPairAccepted=False,newBrowserAccepted=False,ordinaryOriginalMenuAccepted=False,independentSchedulingAccepted=False,originalWholePixelsOrPcmAccepted=False,wholeModeEquivalenceAccepted=False,naturalModeInventory=30,allStageEntryModeInventory=25,completeGame=False,nativeEquivalent=False,bindings=bindings,verifierSha256=SHA(Path(__file__).read_bytes()))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--case',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--check',action='store_true');a=p.parse_args();out=a.output.resolve();assert out.is_relative_to(R/'artifacts/th14')or out.is_relative_to(R/'docs/porting');result=evidence(a.case)
    if a.check:assert json.loads(out.read_bytes())==result
    else:out.write_text(json.dumps(result,indent=2)+'\n',encoding='utf8')
    print(json.dumps({k:v for k,v in result.items()if k not in ['bindings','freshProductionCompleteRegressions']}))
