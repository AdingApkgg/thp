"""Bind finite interpolation ABI evidence to the actual tested TH14 objects."""
from pathlib import Path
import argparse,ast,hashlib,json,shutil
R=Path(__file__).resolve().parents[1]
H=R/'artifacts/th14/rgb-acceleration-stack-nov02'
SHA=lambda b:hashlib.sha256(b).hexdigest()

def evidence(require_integrated=False):
    bindings={}
    def raw(p):
        p=p.resolve(strict=True);assert p.is_relative_to(R)
        data=p.read_bytes();bindings[p.relative_to(R).as_posix()]=dict(bytes=len(data),sha256=SHA(data));return data
    def load(p):return json.loads(raw(p))
    build_path=H/'candidate-v5/observer-build.json';build=load(build_path)
    parent=load(H/'candidate-v4/observer-build.json')
    assert build['wasmSha256']=='1de2cbb429832670d52fde4b398137a66b59a54212426599d13aba957f56eeef'
    assert SHA(raw(build_path.parent/'observer.wasm'))==build['wasmSha256']
    assert parent['all141CoreObjectsRecompiledForChangedClassLayout'] and build['reusedExactObjectCount']==140
    assert len(build['objectBindings'])==len(parent['objectBindings'])==141
    for row in build['objectBindings']+parent['objectBindings']:assert SHA(raw(Path(row['path'])))==row['sha256']
    assert build['headerHashes']==parent['headerHashes']
    assert [n for n in build['sourceHashes']if build['sourceHashes'][n]!=parent['sourceHashes'][n]]==['th12_web/cpp/game/AnmInterpreter.cpp']
    for name,digest in {**build['sourceHashes'],**build['headerHashes']}.items():assert SHA(raw(Path(build['sourceSnapshotRoot'])/name))==digest
    for name,digest in build['fixtureDependencyHashes'].items():assert SHA(raw(Path(name)))==digest
    assert SHA(raw(R/'runtimes/th12/tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe'))==build['compilerSha256']
    native_tool=R/'tools/th14-interpolator-stack-native-nov02.py'
    fixture=R/'runtimes/th12/th12_web/tests/cpp/th14-interpolator-stack-fixture-nov02.cpp'
    checker=R/'tools/th14-interpolator-stack-check-nov02.mjs'
    totals=0
    for native_dir,check_dir,count,mixed in [('public-native-single','public-components-v5',8448,False),('public-native-mixed','public-combinations-v5',768,True)]:
        native=load(H/native_dir/'report.json');checked=load(H/check_dir/'verified.json')
        assert len(native['rows'])==count and native['mixedInterpolationCases']==mixed
        assert native['actualOriginalDriverAndBeamExecuted'] and native['syntheticCallFramesDeclared']
        assert native['originalInstructionsPatched']==0 and not native['productionChanged']
        assert native['toolSha256']==SHA(raw(native_tool))==SHA(raw(H/native_dir/'observer-source.py'))
        assert native['originalExecutableSha256']=='f08e885e28d2e0fc8c579e88034dd7de8f2a648d8f08ce781cf08eadc9ffe353'
        assert checked['passed'] and checked['cases']==count and checked['failures']==0
        assert checked['engineBuildSha256']==SHA(raw(build_path)) and checked['nativeProofSha256']==SHA(raw(H/native_dir/'report.json'))
        assert checked['sourceHashes']==build['sourceHashes'] and checked['headerHashes']==build['headerHashes']
        assert checked['fixtureSha256']==SHA(raw(fixture)) and checked['checkerSha256']==SHA(raw(checker))
        assert checked['wasmSha256']==SHA(raw(H/check_dir/'fixture.wasm'))
        assert not checked['nativeValuesProvidedToPortableEngine']
        for row in native['rows']:
            assert row['originalBeamRead']['word']==row['retainedWord']
            assert row['x87ControlWord']in(0x007f,0x037f)
            for w in row['writes']:
                if w['pc']==0x4a8038:assert w['mask']==0xffff and w['word']&0xffff==row['x87ControlWord']
        totals+=count
    baseline=load(H/'public-baseline-single/verified.json')
    assert not baseline['passed'] and baseline['cases']==8448 and baseline['failures']==320
    assert baseline['failureCounts']==dict(color=40,scale=80,extraScale=80,textureScale=80,color2=40)
    order=load(H/'candidate-combinations-v4/verified.json')
    assert not order['passed'] and order['cases']==768 and order['failures']==216
    prior=load(H/'prior-vector-components-v5/verified.json')
    assert prior['passed'] and prior['cases']==1536 and prior['engineBuildSha256']==SHA(raw(build_path))
    assert prior['wasmSha256']==SHA(raw(H/'prior-vector-components-v5/fixture.wasm'))
    syntax=load(H/'shared-syntax/report.json')
    assert syntax['candidateBuildSha256']==SHA(raw(build_path)) and [x['title']for x in syntax['rows']]==[12,13,14,16]
    for row in syntax['rows']:assert row['exitCode']==0 and row['logSha256']==SHA(raw(H/'shared-syntax'/f"th{row['title']}.log"))
    q=H/'native-x87-control';pre=load(q/'preflight.json');quiet=load(q/'native-silence-verified.json')
    end=load(q/'process-end.json');original=load(q/'native/report.json');native_verified=load(q/'verified.json')
    assert end['observerExitCode']==end['expectedDiagnosticPrefixExitCode']==1 and end['guardStop']is None
    assert original['callbacks']==1300 and original['childExited'] and not original['error']
    assert original['diagnosticPrefixOnly'] and not original['observedForcedReplayEndMenu']
    assert original['x87OriginalFnstcwSamples']==16 and original['x87AdditionalProcessWrites']==0
    assert quiet['verifiedActualNativeMasterLevelsZero'] and quiet['nativePid']==original['pid']
    observer=raw(q/'native/observer-source.py');assert SHA(observer)==pre['observerSourceSha256']==original['sourceSha256']
    assert SHA(observer)==SHA(raw(R/'tools/th14-x87-control-observer-nov02.py'))
    base=raw(R/'tools/th14-native-campaign-observer-oct25.py');assert SHA(base)==pre['baseObserverSha256']
    def mutation_calls(code):
        names={'WriteProcessMemory','SuspendThread','ResumeThread','Wow64SetThreadContext'}
        return [ast.dump(n,include_attributes=False)for n in ast.walk(ast.parse(code))if isinstance(n,ast.Call)and isinstance(n.func,ast.Attribute)and n.func.attr in names]
    assert mutation_calls(observer)==mutation_calls(base)
    fp_events=[json.loads(line)for line in raw(q/'native/x87-math-events.jsonl').decode().splitlines()]
    assert len(fp_events)==16 and all(x['originalFnstcwCompleted']and x['originalStoredWord']==0x037f and x['controlWord']==0x037f and not x['floatingPointContextWritten']for x in fp_events)
    assert native_verified['mathEventsSha256']==SHA(raw(q/'native/x87-math-events.jsonl'))
    reg=H/'full-regressions';plan=load(reg/'plan.json');final=load(reg/'end.json')
    assert plan['buildSha256']==SHA(raw(build_path)) and len(plan['cases'])==14
    assert final['casesCompleted']==final['strictPasses']==final['independentPasses']==14
    assert final['callbacks']==1451340 and final['allCasesActuallyExecuted']
    for row in final['results']:
        assert row['strictPassed'] and row['exitCode']==row['independentVerifierExitCode']==0
        assert row['guardStop']is None and row['independentGuardStop']is None
        case=R/row['caseDirectory'];verified=load(case/'raw-verified.json')
        assert verified['verifiedFiniteEvidence'] and not verified['diagnosticPrefixOnly']
        assert verified['wasmSha256']==build['wasmSha256']
        for name,expected in verified['bindings'].items():assert SHA(raw(R/name))==expected['sha256']
    changed=['AnmInterpreter.cpp','AnmManager.hpp','AnmVm.hpp','EnemyManager.cpp','NativeStackTh14.hpp']
    if require_integrated:
        for name in changed:assert raw(R/'runtimes/th12/th12_web/cpp/game'/name)==raw(Path(build['sourceSnapshotRoot'])/'th12_web/cpp/game'/name)
    assert SHA(raw(R/'runtimes/th12/th12_web/cpp/game/ResourceCrypt.cpp'))=='a291010053963e25dadef2be15ddb3c217110cd2377fc495402ef375150f8c45'
    assert SHA(raw(R/'artifacts/th14/vm-return-worker-oct29/work-state.json'))=='2236db52bee27439486e69216333cd88ddc27d1dcc28233f87bacdcaadc1f33c'
    assert shutil.disk_usage(R).free>=100*1024**3
    raw(Path(__file__))
    return dict(verifiedFiniteInterpolatorStackEvidence=True,productionIntegrated=require_integrated,
        candidateWasmSha256=build['wasmSha256'],changedFiles=changed,
        singleFieldCases=8448,mixedOrderCases=768,allNewCases=totals,priorVectorCases=1536,
        baselineSingleFailures=320,candidateSingleFailures=0,priorOrderControlFailures=216,candidateMixedOrderFailures=0,
        fullNaturalSamples=14,fullNaturalCallbacks=1451340,strictAndIndependentPassed=True,
        actualOriginalFnstcwSamples=16,originalFpObservationIsDiagnosticPrefixOnly=True,
        all141ObjectsRecompiledInParent=True,finalInterpolationObjectRecompiled=True,
        naturalModeInventory=30,allTargetStageEntryModeInventory=26,
        unknownConstructorHighBytesAndOtherWritersRemainUnproved=True,otherConstructorDepthsRemainUnproved=True,
        previousCompleteApplicationsRemainVersionBoundToEbba=True,currentCandidateCompleteApplicationsAccepted=False,
        originalWholePixelsOrPcmAccepted=False,independentSchedulingAccepted=False,browserAcceptance=False,
        nativeValuesProvidedToEngine=False,completeGame=False,nativeEquivalent=False,bindings=bindings)

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--require-integrated',action='store_true');p.add_argument('--check',action='store_true');p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    report=evidence(a.require_integrated);out=a.output.resolve()
    assert out.is_relative_to(R/'artifacts/th14')or out.is_relative_to(R/'docs/porting')
    if a.check:assert json.loads(out.read_bytes())==report
    else:assert not out.exists();out.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items()if k!='bindings'}),flush=True)
