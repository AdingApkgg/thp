"""Check the same-Wasm before/after Scene-word handoff, preserving old failures."""
from pathlib import Path
import argparse
import array
import hashlib
import json
import struct

ROOT=Path(__file__).resolve().parents[1]
SHA=lambda raw:hashlib.sha256(raw).hexdigest()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--home',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--check',action='store_true')
    args=parser.parse_args();home=args.home.resolve();assert home.is_relative_to(ROOT/'artifacts/th14')
    bindings={}
    def read(path):
        raw=path.read_bytes();bindings[path.relative_to(ROOT).as_posix()]=dict(bytes=len(raw),sha256=SHA(raw));return raw
    def load(path):return json.loads(read(path))
    before=home/'word-step-prefix-model';after=home/'word-step-observed-handoff-model'
    original=ROOT/'artifacts/th14/retail-sakuyab-easy-copy-word-step-prefix-hardware-oct26'
    old,new=load(before/'report.json'),load(after/'report.json');receipt=load(home/'word-step-observed-handoff-verified.json')
    observation=load(ROOT/'docs/porting/th14-scene-copy-word-prefix-oct26.json')
    assert receipt['verifiedFiniteEvidence']and receipt['diagnosticPrefixOnly']and receipt['callbacks']==15000
    assert receipt['verifierSha256']==SHA(read(ROOT/'tools/th14-verify-native-campaign.py'))
    for path,row in receipt['bindings'].items():assert SHA(read(ROOT/path))==row['sha256'],path
    assert new['comparisonToolSha256']==SHA(read(ROOT/'tools/th14-compare-native-campaign.mjs'))
    assert old['wasmSha256']==new['wasmSha256']==receipt['wasmSha256']=='b46bea539bc6346c7af8e4d1ac20b90d0c342056044549afeecb0fae1d236880'
    assert old['sourceReplaySha256']==new['sourceReplaySha256']==receipt['sourceReplaySha256']
    assert old['callbacks']==new['callbacks']==15000 and old['diagnosticPrefixOnly']and new['diagnosticPrefixOnly']
    for key in ['nativeInitialSnapshotSha256','nativeResourceEventsSha256','nativeTimesSha256','actualCookie','actualInitialTimeGetTime','entry']:
        assert old[key]==new[key],key
    assert old['sceneWorkerBeforeDrawBoundaries']==1 and old['sceneWorkerAfterDrawBoundaries']==0
    assert new['sceneWorkerBeforeDrawBoundaries']==0 and new['sceneWorkerAfterDrawBoundaries']==1
    assert len(new['sceneCopyWordHandoffs'])==1
    assert new['sceneCopyObservationSha256']==SHA(read(ROOT/'docs/porting/th14-scene-copy-word-prefix-oct26.json'))
    assert observation['verifiedFiniteOriginalSceneCopyObservation']and observation['actualRightWordObservations']==3
    for key in ['noNativePublicationValuesProvidedToEngine','noPerFrameStateOverrides']:
        assert old[key]and new[key]
    assert read(before/'selected-state.u32')==read(after/'selected-state.u32')==read(original/'selected-state.u32')
    assert read(before/'portable-hud.u32')==read(after/'portable-hud.u32')==read(original/'hud-score.u32')
    for path in before.glob('portable-live-*.json'):assert read(path)==read(after/path.name)
    combat=0
    for path in before.glob('combat-*.json'):
        if not path.stem.split('-')[-1].isdigit():continue
        assert read(path)==read(after/path.name);combat+=1
    assert combat==228
    assert read(before/'portable-allocations-initial-through-1000.json')==read(after/'portable-allocations-initial-through-1000.json')
    a=array.array('I');a.frombytes(read(before/'portable-camera.u32'));b=array.array('I');b.frombytes(read(after/'portable-camera.u32'))
    camera=read(original/'world-camera.raw');offsets=[*range(0,88,4),0x104,0x108,0x10c]
    expected=array.array('I',(struct.unpack_from('<I',camera,frame*0x124+offset)[0]for frame in range(15000)for offset in offsets))
    assert b==expected and len(a)==len(b)==15000*25
    changed=[index for index,(left,right)in enumerate(zip(a,b))if left!=right]
    assert changed==[frame*25+12 for frame in range(13714,15000)]
    assert all(a[index]==0 and b[index]==0xbf800000 for index in changed)
    assert load(before/'camera-report.json')['counts']=={'12':1286}
    assert load(after/'camera-report.json')['allCameraWordsEqual']
    negative=read(home/'corrupted-camera-negative/rejection.txt').decode();assert 'expected.tobytes()==read' in negative
    legacy=load(home/'legacy-easy-verifier-regression.json');assert legacy['verifiedFiniteEvidence']and legacy['callbacks']==107233
    assert all(legacy[key]and receipt[key]for key in ['allSelected32Equal','allCamera25Equal','allHud2Equal','allVm303AndRegistryOrderEqual','allCapturedCombatWordsEqual'])
    result=dict(verifiedFiniteSceneWordHandoff=True,diagnosticPrefixOnly=True,callbacks=15000,stagesObserved=[1,2],
        sameProductionWasm=True,productionEngineChanged=False,deliveryInputs='Observed instruction boundaries and timestamps only',nativeCameraValuesProvidedToEngine=False,
        beforeCameraField12DifferentCallbacks=1286,afterAllCamera25Equal=True,changedCameraFields=[12],firstChangedIndex=13714,
        selected32AndHudUnchanged=True,animationRows=receipt['vm303Rows'],animationRegistryAndWordsUnchanged=True,
        combatCheckpoints=228,combatOutputWordsUnchanged=True,initialOrderedPublications=receipt['orderedPublications'],
        corruptedCameraNegativeRejected=True,legacyClassicHardwareFullRegressionCallbacks=107233,
        observerInstrumentationCheckedSeparately=True,historicalMixedStoreCasesStillOpen=True,
        actualGpuOrPcm=False,originalOrdinaryMenuEquivalence=False,browserAcceptance=False,completeGame=False,nativeEquivalent=False,
        wasmSha256=new['wasmSha256'],comparisonToolSha256=new['comparisonToolSha256'],verifierSha256=SHA(Path(__file__).read_bytes()),bindings=bindings,
        scope='Same frozen game Wasm and same original15000-callback TF diagnostic record. Host Scene readiness moves from whole-copy-start to an explicitly observed right-word/post-perspective boundary. Every selected camera word remains required, and all other retained outputs are compared. No proof that three word samples identify simultaneous main execution, no inferred historical schedule, no full-mode, ordinary UI, GPU/PCM or browser acceptance.')
    output=args.output.resolve();assert output.is_relative_to(ROOT/'artifacts/th14')or output.is_relative_to(ROOT/'docs/porting')
    if args.check:assert json.loads(output.read_bytes())==result
    else:output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    print(json.dumps({key:result[key]for key in ['verifiedFiniteSceneWordHandoff','callbacks','beforeCameraField12DifferentCallbacks','afterAllCamera25Equal','animationRows','combatCheckpoints','historicalMixedStoreCasesStillOpen']}))


if __name__=='__main__':main()
