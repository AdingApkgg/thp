"""Recheck the integrated finite RNG boundary repair without accepting whole-game equivalence."""
from pathlib import Path
import argparse,hashlib,importlib.util,json,subprocess,sys,tempfile
R=Path(__file__).resolve().parents[1];H=R/'artifacts/th14/rng-store-boundary-nov02'
SHA=lambda b:hashlib.sha256(b).hexdigest()

def module(path):
    spec=importlib.util.spec_from_file_location(path.stem,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m

def evidence(require_integrated=False):
    bindings={}
    def bind(path):
        path=path.resolve(strict=True);assert path.is_relative_to(R)
        name=path.relative_to(R).as_posix()
        if name not in bindings:
            with path.open('rb')as stream:digest=hashlib.file_digest(stream,'sha256').hexdigest()
            bindings[name]=dict(bytes=path.stat().st_size,sha256=digest)
        return bindings[name]
    def raw(path):bind(path);return path.read_bytes()
    def load(path):return json.loads(raw(path))
    def bound_report(path):
        report=load(path)
        for name,row in report.get('bindings',{}).items():assert bind(R/name)==row,name
        return report
    integration=load(H/'integration-v2.json');assert integration['productionIntegrated']and integration['nativeLockModesSupported']==[0,1]
    changed=integration['files'];assert len(changed)==4
    integrated=True
    for row in changed:
        assert bind(R/row['candidate'])['sha256']==row['newSha256']
        assert bind(R/row['backup'])['sha256']==row['oldSha256']
        integrated&=bind(R/row['path'])['sha256']==row['newSha256']
    if require_integrated:assert integrated
    assert bind(R/'runtimes/th12/th12_web/cpp/game/ResourceCrypt.cpp')['sha256']=='a291010053963e25dadef2be15ddb3c217110cd2377fc495402ef375150f8c45'
    assert bind(R/'artifacts/th14/vm-return-worker-oct29/work-state.json')['sha256']=='2236db52bee27439486e69216333cd88ddc27d1dcc28233f87bacdcaadc1f33c'
    builds=[load(H/name/'observer-build.json')for name in ['game-candidate-v2','legacy-instruction-clock-core-v2','regular-core-v2']]
    base=builds[0]
    assert len(base['objectBindings'])==141 and base['all141CoreObjectsRecompiled']
    for name,digest in {**base['sourceHashes'],**base['headerHashes']}.items():assert bind(Path(base['sourceSnapshotRoot'])/name)['sha256']==digest,name
    for obj in base['objectBindings']:assert bind(Path(obj['path']))['sha256']==obj['sha256']
    for build in builds:
        assert build['objectBindings']==base['objectBindings']and build['sourceHashes']==base['sourceHashes']and build['headerHashes']==base['headerHashes']
        for name,digest in build['fixtureDependencyHashes'].items():assert bind(Path(name))['sha256']==digest,name
    for name,build in zip(['game-candidate-v2','legacy-instruction-clock-core-v2','regular-core-v2'],builds):assert bind(H/name/'observer.wasm')['sha256']==build['wasmSha256']
    original_fixture=load(R/'artifacts/th14/nested-initialization-checkpoint-nov02/regular-core/observer-build.json')
    assert builds[2]['fixtureGraphRoot']==original_fixture['fixtureGraphRoot']and builds[2]['expandedFixtureSha256']==original_fixture['expandedFixtureSha256']
    public_fixture=R/'runtimes/th12/th12_web/tests/cpp/th14-rng-initialization-clock-fixture-nov02.cpp'
    public_text=raw(public_fixture).decode().replace('\r\n','\n')
    used_text=raw(H/'ribbon-rng-clock-fixture.cpp').decode().replace('\r\n','\n')
    assert public_text==used_text.replace('H:/code/thp/runtimes/th12/th12_web/tests/cpp/th14-initialization-clock-fixture-nov01.cpp','th14-initialization-clock-fixture-nov01.cpp')
    component=bound_report(H/'integrated-components-v3/component-verified.json');cb=bound_report(H/'integrated-components-v3/build.json')
    assert component['verifiedFiniteInstructionStoreComponent']and component['cases']==800 and component['scopedObserverLifetimeFailureAndReentryControlsPassed']
    assert component['wrongBeforeReadInsteadOfBeforeStoreRejected']==144
    assert bind(H/'integrated-components-v3/fixture.wasm')['sha256']==cb['wasmSha256']==component['wasmSha256']
    assert component['candidateBuildSha256']==bind(H/'integrated-components-v3/build.json')['sha256']
    assert component['toolSha256']==bind(R/'tools/th14-rng-store-boundary-component-check-nov02.mjs')['sha256']
    native_component=load(H/'integrated-components-v3/native.json')
    oracle=module(R/'tools/th14-rng-store-boundary-native-nov02.py').observe()
    assert json.loads(json.dumps(oracle))==native_component
    assert component['nativeReportSha256']==bind(H/'integrated-components-v3/native.json')['sha256']
    rejected=load(H/'v1-lock-mode-negative.json');assert rejected['rejectedInsufficientV1Prototype']and rejected['cases']==800 and rejected['returnValueDifferences']==40 and rejected['allFailuresAtEnabledNext16PostStoreReturnReload']
    syntax=load(H/'syntax-checks-v2/report.json');assert syntax['allPassed']and len(syntax['checks'])==12 and all(x['exitCode']==0 for x in syntax['checks'])
    assert syntax['buildSha256']==bind(H/'game-candidate-v2/observer-build.json')['sha256']
    native_tool=R/'tools/th14-controlled-rng-store-evidence-nov02.py';native_proof=module(native_tool).evidence(H/'live-control')
    assert native_proof==bound_report(H/'live-control/controlled-verified.json')
    bind(native_tool);assert native_proof['verifiedControlledOriginalRngStoreBoundary']and native_proof['originalRibbonPreUpdateCallChainProved']

    def recheck(native,model,build,proof_path,output,prefix=0,flag=None):
        expected=bound_report(output)
        tool=R/'tools'/('th14-verify-rng-store-campaign-nov02.py'if flag=='--controlled-rng-observation'else 'th14-verify-nested-instruction-campaign-nov02.py'if flag else'th14-verify-native-campaign.py')
        bind(tool)
        with tempfile.NamedTemporaryFile(dir=H,prefix='raw-proof-recheck-',suffix='.json',delete=False)as stream:temporary=Path(stream.name)
        try:
            argv=[sys.executable,'-X','utf8',str(tool),'--native',str(native),'--model',str(model),'--build',str(build),'--output',str(temporary)]
            if prefix:argv+=['--prefix',str(prefix)]
            if flag:argv+=[flag,str(proof_path)]
            result=subprocess.run(argv,cwd=R,capture_output=True,timeout=180)
            assert result.returncode==0,result.stderr.decode(errors='replace')[-1600:]
            assert json.loads(temporary.read_bytes())==expected
        finally:temporary.unlink(missing_ok=True)
        assert expected['allSelected32Equal']and expected['allCamera25Equal']and expected['allHud2Equal']and expected['allVm303AndRegistryOrderEqual']and expected['allCapturedCombatWordsEqual']
        return expected

    controlled=recheck(H/'live-control/native',H/'controlled-v2-model',H/'game-candidate-v2/observer-build.json',H/'live-control/controlled-verified.json',H/'controlled-v2-raw-verified.json',34000,'--controlled-rng-observation')
    old=R/'artifacts/th14/nested-instruction-reimub-v2-nov02'
    prior=recheck(old/'native',H/'legacy-instruction-v2-model',H/'legacy-instruction-clock-core-v2/observer-build.json',old/'controlled-verified.json',H/'legacy-instruction-v2-raw-verified.json',34000,'--controlled-instruction-observation')
    group=R/'artifacts/th14/rng-store-regular-v2-regressions-nov02';end=load(group/'end.json');plan=load(group/'plan.json')
    assert end['allCasesActuallyExecuted']and end['casesCompleted']==end['strictPasses']==end['independentPasses']==16 and end['callbacks']==1579705
    assert plan['buildSha256']==bind(H/'regular-core-v2/observer-build.json')['sha256']
    for case,row in zip(plan['cases'],end['results'],strict=True):
        assert row['key']==case['key']and row['exitCode']==row['independentVerifierExitCode']==0 and row['guardStop']is row['independentGuardStop']is None
        directory=R/row['caseDirectory']
        recheck(R/case['native'],directory/'model',H/'regular-core-v2/observer-build.json',None,directory/'raw-verified.json')
    failed=load(H/'retained36826-v2/model/report.json');fv=load(H/'retained36826-v2/model/live-report.json');fc=load(H/'retained36826-v2/model/combat-snapshots.json');fe=load(H/'retained36826-v2/end.json')
    assert fe['modelExitCode']==1 and fe['guardStop']is None
    assert failed['differenceCounts']=={'21':14403,'22':1702}and sum(x['differenceCount']for x in fv['snapshots'])==719 and len(fc['differences'])==488
    old_publication=load(R/'artifacts/th14/instruction-initialization-applications-nov02/publication/published.json')
    assert old_publication['sourceCommit']=='7acf5ec0c0049e2eb72894987390bbe9c8a964d7'
    for row in changed:
        frozen=subprocess.check_output(['git','-C',str(R/'tools/tmp/github-source-release'),'show','50d212bab4114ecb05472b2ad805873f11840cd2:'+row['path']])
        assert SHA(frozen)==row['oldSha256']
    return dict(verifiedFiniteRngStoreBoundaryRepair=True,productionIntegrated=bool(integrated),changedFiles=[Path(x['path']).name for x in changed],
        basePublishedCommit=old_publication['sourceCommit'],coreWasmSha256=builds[2]['wasmSha256'],controlledWasmSha256=builds[0]['wasmSha256'],
        all141CoreObjectsRecompiled=True,all141GameObjectsIdenticalAcrossFixtures=True,ordinaryFixtureUnchangedAndNoNewRngClockApi=True,
        originalRngInstructionProfiles=800,wrongBoundaryControlsRejected=144,nativeLockModesSupported=[0,1],priorV1RejectedFor40EnabledNext16ReturnFailures=True,scopeLifetimeFailureAndReentryControlsPassed=True,syntaxChecksPassed=12,
        controlledReimubCallbacks=34000,controlledVm303Rows=controlled['vm303Rows'],controlledCombatCheckpoints=controlled['combatCheckpoints'],controlledInitialPublications=controlled['orderedPublications'],
        priorControlledAnmInstructionCallbacks=34000,priorControlledAnmInstructionVm303Rows=prior['vm303Rows'],priorControlledAnmInstructionRegressionPassed=True,
        regularNaturalStrictAndIndependentPasses=16,regularNaturalCallbacks=1579705,
        controlledActualOriginalSeedReadWorkerRestoreThenCachedSeedWriteProved=True,noNativeRngOrVmValuesProvidedToEngine=True,
        startupFirstChanceNoticesRetained=10,coldStartupAccepted=False,exceptionCauseClassified=False,
        old36826StrictFailureClosed=False,independentSchedulingAccepted=False,newCoreFullApplicationAccepted=False,newCoreBrowserAccepted=False,
        wholeModeEquivalent=False,completeGame=False,nativeEquivalent=False,bindings=bindings,verifierSha256=SHA(Path(__file__).read_bytes()))

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--require-integrated',action='store_true');p.add_argument('--output',type=Path,required=True);p.add_argument('--check',action='store_true');a=p.parse_args()
    output=a.output.resolve();assert output.is_relative_to(R/'artifacts/th14')or output.is_relative_to(R/'docs/porting');result=evidence(a.require_integrated)
    if a.check:assert json.loads(output.read_bytes())==result
    else:output.write_text(json.dumps(result,indent=2)+'\n',encoding='utf8')
    print(json.dumps({k:v for k,v in result.items()if k!='bindings'}),flush=True)
