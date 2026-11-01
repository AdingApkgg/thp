"""Recompute one passive original run through its naturally observed stage5 GameOver."""
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
    native=home/'native';n=load(native/'report.json');opt=n['observerOptions']
    assert n['childExited']and not n['error']and n['observedForcedReplayEndMenu']and not n['diagnosticPrefixOnly']
    assert n['observerTerminationRequested']and n['callbacks']==80594<opt['maximum_callbacks']==100000
    assert n['hardwareBreakpointsOnly']and not opt['normal_vm_window_events']and opt['worker_rng_events']and opt['worker_main_context']
    assert n['gameStateWordWrites']==1 and n['caseInitialization']['attractBitClearOnly']and n['rngOrCounterWrites']==n['instructionBytesPatched']==0
    assert not n['inputInjected']and not n['ordinaryMenuReplayInitialization']and not n['replayTerminalMarkerObservationImplemented']
    assert n['recordedStages']==[1,2,3,4,5]and opt['minimum_free_gib']>=100 and opt['maximum_capture_gib']<=.125
    assert S(raw(native/'observer-source.py'))==n['sourceSha256']==S(raw(R/'tools/th14-native-campaign-observer-oct25.py'))
    assert S(raw(native/'work/th14.exe'))==n['executableSha256']=='f08e885e28d2e0fc8c579e88034dd7de8f2a648d8f08ce781cf08eadc9ffe353'
    transition=[json.loads(line)for line in raw(native/'transition-events.jsonl').decode().splitlines()];assert transition==n['transitionEvents']
    terminals=n['terminalMenuSamples'];assert len(terminals)>=3
    for sample in terminals[-3:]:
        assert sample['stage']==5 and sample['pauseWords']==[2,3]and sample['callbacks']==80594
        assert sample['score']==sample['hudDisplayedScoreUnits']==26014792 and sample['lives']==0xffffffff and sample['controlFrame']==7565
    vm=module('vm_decoder',R/'tools/th14-passive-entry-clock-evidence-oct30.py');combat=module('combat_decoder',R/'tools/th14-combat-pool-readonly-v3-oct25.py')
    native=home/'native';model=home/'current-compare/model';report=load(model/'report.json');end=load(home/'current-compare/process-end.json')
    assert end['exitCode']==0 and end['guardStop']is None and end['strictPassed']
    assert report['completed']and report['callbacks']==report['nativeCallbacks']==80594 and not report['diagnosticPrefixOnly']
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
    assert len(state)==len(original)==80594*128 and state==original and S(state)==report['selectedSha256']==report['nativeSelectedSha256']
    camera=raw(native/'world-camera.raw');assert len(camera)==80594*0x124
    expected=b''.join(camera[i*0x124+off:i*0x124+off+4]for i in range(80594)for off in [*range(0,88,4),0x104,0x108,0x10c])
    assert raw(model/'portable-camera.u32')==expected
    hud=raw(native/'hud-score.u32');assert len(hud)==80594*8 and raw(model/'portable-hud.u32')==hud
    live=load(model/'live-report.json');assert live['allLiveValuesEqual']and live['comparedValues']==303
    rows=0
    for snapshot in live['snapshots']:
        frame=snapshot['frame'];nr=load(native/f'live-vms-callback-{frame}.json')['rows'];pr=load(model/f'portable-live-{frame}.json')
        addresses={struct.unpack_from('<I',bytes.fromhex(n['rawVmHex']),0x570)[0]:n['handle']for n in nr}
        assert [vm.vm_values(n,addresses)for n in nr]==pr;rows+=len(nr)
    assert [s['frame']for s in live['snapshots']]==[1,30000,60000,80000]and rows==680
    cp=load(model/'combat-snapshots.json');index=load(native/'combat-pool-index.json');by_callback={x['callback']:x for x in index['snapshots']}
    assert len(cp['snapshots'])==907 and not cp['differences']
    for checkpoint in cp['snapshots']:
        callback=checkpoint['callback'];binding=by_callback[callback];compressed=raw(native/'combat-pools'/binding['file']);assert S(compressed)==binding['sha256']
        n=json.loads(gzip.decompress(compressed));p=load(model/f'combat-{callback}.json')
        assert n['callback']==p['callback']==callback and n['stage']==p['stage']and n['stageFrame']==p['stageFrame']
        for family,fields in combat.SCHEMA.items():assert [combat.selected(bytes.fromhex(obj['rawHex']),fields,obj['slot'])for obj in n['original'][family]]==p['rows'][family]
    allocations=[json.loads(s)for s in raw(native/'allocation-events.jsonl').decode().splitlines()]
    allocations=[n for n in allocations if n['precedingPlayerCallbacks']<1000];portable=load(model/'portable-allocations-initial-through-1000.json')
    assert len(allocations)==len(portable)==2870
    assert [[n[k]for k in ['handle','file','script']]for n in allocations]==[[n[k]for k in ['handle','file','script']]for n in portable]
    end=report['end'];stable=report['stableMenuAfter90Ticks'];assert end and stable
    assert stable[0]==2 and stable[1]==5 and stable[3]==80594 and stable[5]==3
    assert stable[11]==26014792 and stable[12]==-1 and stable[13]==2 and stable[14]==7565
    assert end['state'][11:15]==stable[11:15]
    ui_home=R/'artifacts/th14/original-ordinary-ui-consoleless-nov01';ui=load(ui_home/'observation.json');prepared=load(ui_home/'prepared.json')
    assert ui['originalTitleMenuActuallyObserved']and ui['originalNaturalAttractFrameActuallyObserved']and not ui['ordinaryReplayEntryAccepted']
    assert not ui['menuSelectionChangeConfirmed']and ui['inputFailureCauseNotEstablished']and not ui['manualActionRequested']
    assert ui['retailChildStoppedAtDeclared300Seconds']and prepared['configuredMusicAndSoundVolumeZero']and not prepared['userOriginalProfileUsed']
    assert ui['sourcePreparedSha256']==S(raw(ui_home/'prepared.json'))
    assert S(raw(ui_home/'work/th14.exe'))=='f08e885e28d2e0fc8c579e88034dd7de8f2a648d8f08ce781cf08eadc9ffe353'
    assert S(raw(ui_home/'work/th14.dat'))=='57d84a5cbe82460931cca26f090a0fde7aef180889ce5bfe8315851fc97b0233'
    for name,binding in ui['screenshots'].items():
        data=raw(ui_home/name);assert data.startswith(b'\xff\xd8')and len(data)==binding['bytes']and S(data)==binding['sha256']
    status=raw(ui_home/'native-process.txt').decode();assert 'terminatedAtDeclaredBudget=True'in status and 'maximumSeconds=300'in status
    return dict(verifiedFinitePassiveNaturalGameOver=True,callbacks=80594,stagesObserved=[1,2,3,4,5],
        naturalGameOverStage=5,naturalGameOverControllerFrame=7565,internalScoreUnits=26014792,lives=-1,
        nativeTerminalMenuSamples=3,portableTerminalMenuStableTicks=90,replayEofMarkerNotObserved=True,sixStageClearNotAccepted=True,
        declaredWarmAttractBitClearCount=1,selectedWordsPerCallback=32,allSelectedWordsByteEqual=True,
        vmSnapshots=4,vmRowsRecomputed=680,vmFieldsPerRow=303,combatCheckpointsRecomputed=907,combatFieldDifferences=0,
        cameraWordsPerCallback=25,hudWordsPerCallback=2,initialPublications=2870,noExtraVmBoundaryClock=True,
        normalRegistryEntryProjection=False,unchangedComparisonDriver=True,currentGameObjectsVerified=141,
        productionGameplayModified=False,productionWasmChanged=False,originalDebuggerPausesAffectTiming=True,
        originalOrdinaryMenuAccepted=False,originalTitleAndAttractVisuallyObserved=True,ordinaryReplayInputConfirmed=False,
        independentThreadSchedulingAccepted=False,old80324FailureClosed=False,
        completeGame=False,nativeEquivalent=False,bindings=bindings,verifierSha256=S(Path(__file__).read_bytes()))

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--case',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--check',action='store_true');a=p.parse_args()
    target=a.output.resolve();assert target.is_relative_to(R/'artifacts/th14')or target.is_relative_to(R/'docs/porting')
    result=evidence(a.case)
    if a.check:assert json.loads(target.read_bytes())==result
    else:target.write_text(json.dumps(result,indent=2)+'\n',encoding='utf8')
    print(json.dumps({k:v for k,v in result.items()if k!='bindings'}))
if __name__=='__main__':main()
