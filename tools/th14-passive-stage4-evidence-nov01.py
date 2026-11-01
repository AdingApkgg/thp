"""Recompute the current 60000-callback stage4 prefix with no extra VM clock."""
from pathlib import Path
import argparse,gzip,hashlib,importlib.util,json,struct
R=Path(__file__).resolve().parents[1]
S=lambda b:hashlib.sha256(b).hexdigest()

def evidence(home):
    home=home.resolve(strict=True);assert home.is_relative_to(R/'artifacts/th14');bindings={}
    def raw(path):
        path=path.resolve(strict=True);assert path.is_relative_to(R)
        data=path.read_bytes();bindings[path.relative_to(R).as_posix()]=dict(bytes=len(data),sha256=S(data));return data
    def load(path):return json.loads(raw(path))
    def module(name,path):
        raw(path);spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
    window=module('stage4_window',R/'tools/th14-passive-stage4-window-evidence-nov01.py').evidence(home/'native')
    assert window==load(home/'window-observation-public.json');bindings.update(window['bindings'])
    vm=module('vm_decoder',R/'tools/th14-passive-entry-clock-evidence-oct30.py');combat=module('combat_decoder',R/'tools/th14-combat-pool-readonly-v3-oct25.py')
    native=home/'native';model=home/'current-compare/model';report=load(model/'report.json');end=load(home/'current-compare/process-end.json')
    assert end['exitCode']==0 and end['guardStop']is None and end['strictPassed']
    assert report['completed']and report['callbacks']==report['nativeCallbacks']==60000 and report['diagnosticPrefixOnly']
    assert report['hostNormalBoundaryMode']=='none'and report['normalBoundaryObservation']is report['normalVmBoundaryObservation']is None
    assert not report['productionNormalAnmBoundaryPoll']and not report['productionNormalVmReturnPoll']
    assert not report['vmCallbackPointersWrapped']and not report['actualGpuOrAudio']and not report['ordinaryIndependentThreadTimingAcceptance']
    assert report['noPerFrameStateOverrides']and report['noNativePublicationValuesProvidedToEngine']and report['intactOriginalReplay']
    assert report['allRaw32ByteIdentical']and not report['differenceCounts']and not report['completeGame']and not report['nativeEquivalent']
    comparison=raw(R/'tools/th14-compare-native-campaign.mjs');assert S(comparison)==report['comparisonToolSha256']
    build_path=R/'artifacts/th14/reimub-normal-construction-current-oct30/observer/observer-build.json';build=load(build_path)
    assert S(raw(build_path.parent/'observer.wasm'))==build['wasmSha256']==report['wasmSha256']=='7c4c9066a9e8a86fb7db162638ad2d50d73441dad90d2418e5b5aa2b0e84b0ee'
    assert len(build['objectBindings'])==141
    for row in build['objectBindings']:assert S(raw(Path(row['path'])))==row['sha256']
    for name in ['GameSession.cpp','GameBattle.cpp','AnmManager.cpp']:
        key='th12_web/cpp/game/'+name;assert S(raw(R/'runtimes/th12'/key))==build['sourceHashes'][key]
    for name in ['GameSession.hpp','AnmManager.hpp']:
        key='th12_web/cpp/game/'+name;assert S(raw(R/'runtimes/th12'/key))==build['headerHashes'][key]
    state=raw(model/'selected-state.u32');original=raw(native/'selected-state.u32')
    assert len(state)==len(original)==60000*128 and state==original and S(state)==report['selectedSha256']==report['nativeSelectedSha256']
    camera=raw(native/'world-camera.raw');assert len(camera)==60000*0x124
    expected=b''.join(camera[i*0x124+off:i*0x124+off+4]for i in range(60000)for off in [*range(0,88,4),0x104,0x108,0x10c])
    assert raw(model/'portable-camera.u32')==expected
    hud=raw(native/'hud-score.u32');assert len(hud)==60000*8 and raw(model/'portable-hud.u32')==hud
    live=load(model/'live-report.json');assert live['allLiveValuesEqual']and live['comparedValues']==303
    rows=0
    for snapshot in live['snapshots']:
        frame=snapshot['frame'];nr=load(native/f'live-vms-callback-{frame}.json')['rows'];pr=load(model/f'portable-live-{frame}.json')
        addresses={struct.unpack_from('<I',bytes.fromhex(n['rawVmHex']),0x570)[0]:n['handle']for n in nr}
        assert [vm.vm_values(n,addresses)for n in nr]==pr;rows+=len(nr)
    assert [s['frame']for s in live['snapshots']]==[1,30000,60000]and rows==677
    cp=load(model/'combat-snapshots.json');index=load(native/'combat-pool-index.json');by_callback={x['callback']:x for x in index['snapshots']}
    assert len(cp['snapshots'])==555 and not cp['differences']
    for checkpoint in cp['snapshots']:
        callback=checkpoint['callback'];binding=by_callback[callback];compressed=raw(native/'combat-pools'/binding['file']);assert S(compressed)==binding['sha256']
        n=json.loads(gzip.decompress(compressed));p=load(model/f'combat-{callback}.json')
        assert n['callback']==p['callback']==callback and n['stage']==p['stage']and n['stageFrame']==p['stageFrame']
        for family,fields in combat.SCHEMA.items():assert [combat.selected(bytes.fromhex(obj['rawHex']),fields,obj['slot'])for obj in n['original'][family]]==p['rows'][family]
    allocations=[json.loads(s)for s in raw(native/'allocation-events.jsonl').decode().splitlines()]
    allocations=[n for n in allocations if n['precedingPlayerCallbacks']<1000];portable=load(model/'portable-allocations-initial-through-1000.json')
    assert len(allocations)==len(portable)==2870
    assert [[n[k]for k in ['handle','file','script']]for n in allocations]==[[n[k]for k in ['handle','file','script']]for n in portable]
    return dict(verifiedFinitePassiveStage4Prefix=True,callbacks=60000,stagesObserved=[1,2,3,4],nativeCallEdges=6048,nativeCallPairs=3024,
        pendingCallEntriesDrained=2,selectedWordsPerCallback=32,allSelectedWordsByteEqual=True,
        vmSnapshots=3,vmRowsRecomputed=677,vmFieldsPerRow=303,combatCheckpointsRecomputed=555,combatFieldDifferences=0,
        cameraWordsPerCallback=25,hudWordsPerCallback=2,initialPublications=2870,noExtraVmBoundaryClock=True,
        normalRegistryEntryProjection=False,unchangedComparisonDriver=True,currentGameObjectsVerified=141,
        productionGameplayModified=False,productionWasmChanged=False,originalDebuggerPausesAffectTiming=True,
        originalOrdinaryMenuAccepted=False,independentThreadSchedulingAccepted=False,old80324FailureClosed=False,
        completeGame=False,nativeEquivalent=False,bindings=bindings,verifierSha256=S(Path(__file__).read_bytes()))

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--case',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--check',action='store_true');a=p.parse_args()
    target=a.output.resolve();assert target.is_relative_to(R/'artifacts/th14')or target.is_relative_to(R/'docs/porting')
    result=evidence(a.case)
    if a.check:assert json.loads(target.read_bytes())==result
    else:target.write_text(json.dumps(result,indent=2)+'\n',encoding='utf8')
    print(json.dumps({k:v for k,v in result.items()if k!='bindings'}))
if __name__=='__main__':main()
