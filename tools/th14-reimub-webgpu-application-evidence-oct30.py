"""Verify a terminal current WebGPU replay and its version-bound GLES peer.

No live prefix, earlier core or wall-budget failure can pass this gate.
Both are declared native hosts, not original GUI or browser acceptance.
"""
from pathlib import Path
import argparse, hashlib, importlib.util, json, shutil
ROOT=Path(__file__).resolve().parents[1]
SHA=lambda b:hashlib.sha256(b).hexdigest()

def verify(home):
    bindings={}
    def read(path):
        raw=path.read_bytes();bindings[path.relative_to(ROOT).as_posix()]={'bytes':len(raw),'sha256':SHA(raw)};return raw
    def load(path):return json.loads(read(path))
    run=load(home/'webgpu/report.json')
    assert run['completed']and not run['error'],'Require terminal successful actual WebGPU Application run'
    end=load(home/'process-end.json')
    assert end['exitCode']==0 and end['guardStop']is None
    assert run['backend']=='webgpu'and run['actualProductionApplicationAndDevices']
    assert run['platformClockAndIoDeclared']and run['physicalAudioDevicesOpened']==0
    assert not run['browserRun']and not run['browserAcceptance']and not run['completeGame']and not run['nativeEquivalent']
    plan=load(home/'plan.json');peer_home=ROOT/plan['comparisonGlesHome']
    module_path=ROOT/'tools/th14-reimub-ordinary-application-evidence-oct30.py';read(module_path)
    spec=importlib.util.spec_from_file_location('strict_gles_peer',module_path)
    checker=importlib.util.module_from_spec(spec);spec.loader.exec_module(checker)
    peer_proof=checker.verify(peer_home)
    assert peer_proof==load(peer_home/'verified.json')
    peer=load(peer_home/'gles/report.json')
    assert plan['sourceCommit']==peer_proof['sourceCommit']=='57a544191704e0ce64cd46de85fe648a3e152097'
    build_home=ROOT/plan['build'];build=load(build_home/'build.json')
    peer_build=load(ROOT/json.loads(read(peer_home/'plan.json'))['build']/'build.json')
    assert build['backend']=='webgpu'and build['compiled']and build['productionSourceFilesUnmodified']
    assert build['coreObjects']==peer_build['coreObjects']and len(build['coreObjects'])==141
    assert build['coreSourceHashes']==peer_build['coreSourceHashes']
    assert build['coreBuildSha256']==peer_build['coreBuildSha256']
    assert build['compilerSha256']==peer_build['compilerSha256']
    for row in build['coreObjects']:assert SHA(read(Path(row['path'])))==row['sha256']
    for name,digest in build['newObjects'].items():assert SHA(read(build_home/name))==digest
    for name,row in build['sourceBindings'].items():assert SHA(read(ROOT/name))==row['sha256'],name
    for name in ['Th14WebGpu.wgsl','Th14WebGpuResample.wgsl']:
        assert read(build_home/'shaders'/name)==read(ROOT/'runtimes/th12/portable/sdl'/name)
    assert SHA(read(build_home/'application.wasm'))==build['wasmSha256']==plan['wasmSha256']==run['wasmSha256']
    assert SHA(read(build_home/'build.json'))==run['buildReportSha256']
    assert plan['runnerSha256']==run['toolSha256']==SHA(read(home/'webgpu/run-tool.py'))==SHA(read(ROOT/plan['runner']))
    assert run['hostToolSha256']==SHA(read(ROOT/'tools/th14-native-webgpu-context.py'))
    assert plan['maximumFrames']==150000 and plan['maximumWallSeconds']==6000
    assert end['elapsedSeconds']<=6060
    assert plan['minimumFreeBytes']==100*1024**3 and plan['maximumOutputBytes']==128*1024**2
    assert plan['priorWallBudgetFailurePreserved']and not plan['previousCompleteResultInherited']
    prior_budget=load(ROOT/'docs/porting/th14-current-full-budget-oct30.json')
    assert prior_budget['budgetFailure']and not prior_budget['completed']
    assert prior_budget['frames']==108875 and prior_budget['maximumWallSecondsUnchanged']==3600
    assert prior_budget['strictVerifierRejected']and prior_budget['naturalEndNotObserved']
    assert not plan['automaticNextCase']
    assert read(home/'scenario.json')==read(peer_home/'scenario.json')
    assert run['scenarioSha256']==peer['scenarioSha256']==plan['scenarioSha256']
    assert run['frames']==peer['frames']==122622
    for key in ['actions','checks','rows','initialSave','finalSave','pcmFrames','pcmSha256',
                'pendingAsyncCallbacks','deliveredCallbackSequence','declaredInitialGameTicks','metadataEpochAtFrameZero']:
        assert run[key]==peer[key],key
    assert len(run['checks'])==45 and len(run['actions'])==25
    assert run['actions'][-2]['endFrame']==122562
    assert run['actions'][-1]['endFrame']-run['actions'][-2]['endFrame']==60
    assert run['actions'][-1]['state'][7]==8 and run['actions'][-1]['state'][9]==91452576
    assert load(home/'webgpu/declared-process-entropy.json')==load(peer_home/'gles/declared-process-entropy.json')
    replay=read(home/'initial-save/replay/th14_01.rpy')
    assert replay==read(home/'webgpu/save/replay/th14_01.rpy')==read(peer_home/'initial-save/replay/th14_01.rpy')
    assert SHA(replay)==plan['sourceReplaySha256']==peer_proof['replaySha256']
    assert len(run['captures'])==len(peer['captures'])==8
    for actual,expected in zip(run['captures'],peer['captures'],strict=True):
        for key in ['frame','label','referenceState']:assert actual[key]==expected[key]
        left,right=read(home/'webgpu'/actual['file']),read(peer_home/'gles'/expected['file'])
        assert len(left)==640*480*4 and SHA(left)==actual['sha256']
        assert SHA(right)==expected['sha256']and left==right,actual['label']
    observed=sum(p.stat().st_size for p in home.rglob('*')if p.is_file())
    assert observed<=128*1024**2 and shutil.disk_usage(home).free>=100*1024**3
    return dict(schema='th14/current-webgpu-normal-application/1',verifiedFiniteApplicationFullReplay=True,
                sourceCommit=plan['sourceCommit'],wasmSha256=run['wasmSha256'],frames=122622,assertions=45,
                naturalReplayEndFrame=122562,stableEndFrames=60,stageCount=6,coreObjectsVerified=141,
                completeSelectedJournalEqualsCurrentGles=True,wholeCapturedBuffersEqualCurrentGles=8,
                silentPcmFrames=run['pcmFrames'],silentPcmSha256=run['pcmSha256'],
                inputFileUnchanged=True,sourceReplaySha256=SHA(replay),finalScoreUnits=91452576,finalLivingStock=8,
                originalWholeApplicationPixelsOrPcmCompared=False,ordinaryOriginalGuiAccepted=False,
                declaredHostClockEntropyAndAsyncDelivery=True,nativeApplicationWorkerFeatureOff=True,
                physicalAudioDevicesOpened=0,browserAcceptance=False,productionChanged=False,
                completeGame=False,nativeEquivalent=False,verifierSha256=SHA(Path(__file__).read_bytes()),bindings=bindings)

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--home',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True);parser.add_argument('--check',action='store_true');args=parser.parse_args()
    home=args.home.resolve();output=args.output.resolve()
    assert home.is_relative_to(ROOT/'artifacts/th14')
    assert output.is_relative_to(ROOT/'artifacts/th14')or output.is_relative_to(ROOT/'docs/porting')
    result=verify(home)
    if args.check:assert json.loads(output.read_bytes())==result
    else:output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:result[k]for k in ['verifiedFiniteApplicationFullReplay','frames','assertions','wholeCapturedBuffersEqualCurrentGles','browserAcceptance']}))
