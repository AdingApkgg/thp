"""Require a natural six-stage original and a fresh current-core comparison."""
from pathlib import Path
import argparse,hashlib,json,subprocess
R=Path(__file__).resolve().parents[1]
N=R/'artifacts/th14/marisaa-beam-writer-context-nov02/next-marisaa-easy-kg'
M=R/'artifacts/th14/rgb-acceleration-stack-nov02/new-marisaa-easy-kg'
CORE='54cbc0cd05b5db6d8257ffa14dc1dcaf407a8754'
SHA=lambda b:hashlib.sha256(b).hexdigest()

def evidence():
    bindings={}
    def raw(p):
        p=p.resolve(strict=True);assert p.is_relative_to(R)
        data=p.read_bytes();bindings[p.relative_to(R).as_posix()]=dict(bytes=len(data),sha256=SHA(data));return data
    def load(p):return json.loads(raw(p))
    end=load(M/'process-end.json');original_end=load(N/'process-end.json')
    assert end['strictPassed']and end['exitCode']==end['independentVerifierExitCode']==0 and end['guardStop']is None
    assert original_end['exitCode']==0 and original_end['guardStop']is None
    native=load(N/'native/report.json');plan=load(N/'plan.json');current_plan=load(M/'plan.json')
    assert native['childExited']and not native['error']and native['observedForcedReplayEndMenu']
    assert native['recordedStages']==[1,2,3,4,5,6]and plan['selection']==[1,0,0,1]
    assert native['sourceSha256']==plan['sourceSha256']==SHA(raw(N/'native/observer-source.py'))=='ce533a0503163d69a6b93f3a132b950ba96b40cc24bc1f9bbabd9b33b6ca2da7'
    assert native['instructionBytesPatched']==native['rngOrCounterWrites']==0 and native['caseInitialization']['attractBitClearOnly']
    B=R/'artifacts/th14/rgb-acceleration-stack-nov02/candidate-v5/observer-build.json';b=load(B)
    assert current_plan['sourceCommit']==CORE and current_plan['buildSha256']==SHA(raw(B))
    assert b['wasmSha256']=='1de2cbb429832670d52fde4b398137a66b59a54212426599d13aba957f56eeef'==SHA(raw(B.parent/'observer.wasm'))
    assert len(b['objectBindings'])==141
    for row in b['objectBindings']:assert SHA(raw(Path(row['path'])))==row['sha256']
    for name,digest in {**b['sourceHashes'],**b['headerHashes']}.items():assert SHA(raw(Path(b['sourceSnapshotRoot'])/name))==digest
    committed=[]
    for name in ['AnmInterpreter.cpp','AnmManager.hpp','AnmVm.hpp','EnemyManager.cpp','NativeStackTh14.hpp']:
        path='runtimes/th12/th12_web/cpp/game/'+name
        data=subprocess.check_output(['git','-C',str(R/'tools/tmp/github-source-release'),'show',CORE+':'+path])
        expected={**b['sourceHashes'],**b['headerHashes']}['th12_web/cpp/game/'+name]
        assert SHA(data)==expected;committed.append(dict(commit=CORE,path=path,sha256=expected))
    verified=load(M/'raw-verified.json')
    assert verified['verifiedFiniteEvidence']and not verified['diagnosticPrefixOnly']and verified['originalNaturalReplayEndObserved']
    assert verified['stagesObserved']==[1,2,3,4,5,6]and verified['selection']==[1,0,0,1]
    assert verified['wasmSha256']==b['wasmSha256']and verified['callbacks']==native['callbacks']
    for name,expected in verified['bindings'].items():assert SHA(raw(R/name))==expected['sha256']
    quiet=load(N/'native-silence-verified.json')
    assert quiet['verifiedActualNativeMasterLevelsZero']and quiet['nativePid']==native['pid']
    assert quiet['nativeExecutableSha256']==native['executableSha256']=='f08e885e28d2e0fc8c579e88034dd7de8f2a648d8f08ce781cf08eadc9ffe353'
    assert all((x['musicConfig'],x['effectsConfig'],x['musicMaster'],x['effectsMaster'])==(0,0,0,0)for x in quiet['samples'])
    assets=R/native['observerOptions']['assets'];asset=load(assets/'manifest.json')
    assert asset['passed']and asset['changedEntries']==['demo0.rpy']and asset['unchangedEntries']==226
    replay=Path(asset['replayPath']);meta=load(replay.with_name(replay.stem+'-source.json'))
    assert meta['actualNativeCodecVerified']and meta['expectedSelection']==[1,0,0]
    assert meta['sha256']==asset['replaySha256']==native['sourceFullReplaySha256']==SHA(raw(replay))=='89e6c94c688228e9536bc5fd07caa6bd17c41174061a55d8602a96ed681aba29'
    assert [x['stage']for x in meta['stages']]==[1,2,3,4,5,6]
    assert SHA(raw(assets/'manifest.json'))==plan['assetManifestSha256']
    assert SHA(raw(replay.with_name(replay.stem+'-source.json')))==plan['metadataSha256']
    codec=load(replay.parent/'additional-codec-verified.json')
    assert codec['passed']and next(x for x in codec['rows']if x['sha256']==meta['sha256'])==meta
    assert SHA(raw(replay.parent/'decode-additional-native.py'))==codec['toolSha256']==meta['nativeCodecObserverSha256']
    assert SHA(raw(replay.parent/'source-page.html'))==meta['sourcePageSha256']
    old=load(N/'queue-end.json');raw(Path(__file__))
    return dict(verifiedExpandedFiniteSixStageReplay=True,case='marisaa-easy-kg',selection=[1,0,0,1],
        sourceCoreCommit=CORE,wasmSha256=b['wasmSha256'],callbacks=native['callbacks'],
        originalNaturalReplayEndObserved=True,stagesObserved=[1,2,3,4,5,6],
        allRetainedSelected32Camera25Hud2Vm303CombatAndInitialPublicationsIndependentlyExact=True,
        vmRows=verified['vm303Rows'],combatCheckpoints=verified['combatCheckpoints'],
        actualOriginalMusicAndEffectsMastersZero=True,replaySha256=meta['sha256'],
        nativeInputAttractBitClearOnly=True,originalWarmReplayScopeOnly=True,recordedInputFullyConsumedNotProven=True,
        olderCoreResultRetained=old,oldFailureSamplesNotClosed=True,wholeModeEquivalent=False,
        ordinaryOriginalGuiAccepted=False,originalWholePixelsOrPcmAccepted=False,independentSchedulingAccepted=False,
        completeGame=False,nativeEquivalent=False,committedGameSourceBindings=committed,bindings=bindings)

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);p.add_argument('--check',action='store_true');a=p.parse_args()
    r=evidence();out=a.output.resolve();assert out.is_relative_to(R/'artifacts/th14')or out.is_relative_to(R/'docs/porting')
    if a.check:assert json.loads(out.read_bytes())==r
    else:assert not out.exists();out.write_text(json.dumps(r,indent=2)+'\n')
    print(json.dumps({k:v for k,v in r.items()if k not in ['bindings','committedGameSourceBindings','olderCoreResultRetained']}),flush=True)
