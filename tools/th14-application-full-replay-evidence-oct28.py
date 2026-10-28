"""Verify the current initial-decode six-stage Application regression.

This accepts a full declared flow only. It does not turn running, early GameOver,
component image equality or a known input's prior reference run into ordinary
original-menu, browser or whole-game equivalence.
"""
from pathlib import Path
import argparse
import hashlib
import json
import subprocess

ROOT=Path(__file__).resolve().parents[1]
SHA=lambda raw:hashlib.sha256(raw).hexdigest()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--home',type=Path,required=True)
    parser.add_argument('--build',type=Path,required=True)
    parser.add_argument('--backend',choices=['webgpu','gles'],default='webgpu')
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--check',action='store_true')
    args=parser.parse_args();home=args.home.resolve();build_home=args.build.resolve();bindings={}
    assert home.is_relative_to(ROOT/'artifacts/th14')and build_home.is_relative_to(ROOT/'artifacts/th14')
    def read(path):
        raw=path.read_bytes();bindings[path.relative_to(ROOT).as_posix()]=dict(bytes=len(raw),sha256=SHA(raw));return raw
    def load(path):return json.loads(read(path))
    plan=load(home/('plan.json'if args.backend=='webgpu'else'gles-plan.json'));folder=home/args.backend;run=load(folder/'report.json');build=load(build_home/'build.json')
    assert run['completed']and not run['error'],'A terminal successful Application report is required'
    assert run['schema']=='th14/native-application-run/1'and run['backend']==build['backend']==args.backend
    assert run['actualProductionApplicationAndDevices']and run['platformClockAndIoDeclared']
    assert run['physicalAudioDevicesOpened']==0 and not run['appUiControlled']and not run['browserRun']
    assert not run['completeGame']and not run['nativeEquivalent']and not run['browserAcceptance']
    assert build['compiled']and run['wasmSha256']==build['wasmSha256']==SHA(read(build_home/'application.wasm'))
    assert run['buildReportSha256']==SHA(read(build_home/'build.json'))
    assert run['toolSha256']==SHA(read(folder/'run-tool.py'))
    for path,row in build['sourceBindings'].items():assert SHA(read(ROOT/path))==row['sha256'],path
    assert set(build['exports'])=={'component_initialize','component_tick','component_state','component_pixels','component_audio_close','th11_error','th11_last_resource','malloc','free','component_reference_state','component_live_state','component_births'}
    code_commit='6a0a12b4b7a254451ef4e7f888f92118e2c7ef34'
    assert plan['gameplayCodeCommit']==code_commit
    core=load(ROOT/'artifacts/th14/native-frame-readback-oct27/initial-decode-core-v2/observer-build.json')
    assert build['coreBuildSha256']==SHA(read(ROOT/'artifacts/th14/native-frame-readback-oct27/initial-decode-core-v2/observer-build.json'))
    assert build['coreSourceHashes']==core['sourceHashes']and len(build['coreObjects'])==141
    assert build['coreObjects']==core['objectBindings']
    for row in build['coreObjects']:assert SHA(read(Path(row['path'])))==row['sha256']
    courier=ROOT/'tools/tmp/github-source-release'
    for name in ('GameResources.cpp','GameResources.hpp','GameSessionResources.cpp','GameSessionResources.hpp','GameBattle.cpp'):
        path='runtimes/th12/th12_web/cpp/game/'+name
        published=subprocess.check_output(['git','-C',str(courier),'show',code_commit+':'+path])
        assert published==read(ROOT/path)
    scenario_path=ROOT/'runtimes/th12/th12_web/tests/fixtures/th14-native-application-full-replay.json'
    scenario=load(scenario_path);assert run['scenarioSha256']==plan['scenarioSha256']==SHA(read(scenario_path))
    assert run['metadataEpochAtFrameZero']==1793037600
    assert run['archiveSha256']=='57d84a5cbe82460931cca26f090a0fde7aef180889ce5bfe8315851fc97b0233'
    assert plan['maximumFrames']==240000 and plan['maximumWallSeconds']==3600
    assert plan['scenarioUpperBoundFrames']==sum(action.get('frames',0)for action in scenario['actions'])==211982
    assert plan['minimumFreeBytes']==100*1024**3 and plan['maximumOutputBytes']==128*1024**2
    assert plan['automaticNextCase']is False and not plan['productionGameplayChanged']
    expected_replay='866bf6bac02e1c2b9067dacce6705dc71a512eeb2755106474be492a2d23dcdc'
    source=read(ROOT/'artifacts/th14/application-full-replay-oct26/initial-save/replay/th14_01.rpy');assert SHA(source)==plan['replaySha256']==expected_replay
    assert read(folder/'save/replay/th14_01.rpy')==source
    assert run['initialSave']==run['finalSave']=={'replay/th14_01.rpy':dict(bytes=len(source),sha256=expected_replay)}
    metadata=load(ROOT/'artifacts/th14/royalflare-coverage-matrix-oct16/inputs/sakuyab-hard-source.json')
    assert metadata['actualNativeCodecVerified']and metadata['sha256']==expected_replay
    assert [metadata[name]for name in ['character','subtype','difficulty']]==[2,1,2]
    assert [stage['stage']for stage in metadata['stages']]==[1,2,3,4,5,6]
    reference=load(ROOT/'artifacts/th14/retail-sakuyab-hard-exit-boundary-hardware-oct26/report.json')
    assert reference['sourceFullReplaySha256']==expected_replay and reference['callbacks']==122811
    assert reference['childExited']and not reference['error']and reference['observedForcedReplayEndMenu']
    assert reference['instructionBytesPatched']==reference['rngOrCounterWrites']==0
    # This checks reference identity/end only; current Application state,
    # pixels and PCM are not claimed equal to all of that original run.
    assert reference['terminalMenuSamples'][-1]['stage']==6 and reference['terminalMenuSamples'][-1]['lives']==1
    assert len(run['actions'])==len(scenario['actions'])==25
    last=0;checks=[]
    for command,observed in zip(scenario['actions'],run['actions']):
        assert set(command)<={'frames','held','pause','capture','expect','until'}
        assert observed['atFrame']==last and observed['held']==command.get('held',0)and observed['pause']==command.get('pause',0)
        elapsed=observed['endFrame']-last;assert 0<=elapsed<=command.get('frames',0)
        if 'until'in command:
            assert observed['until']==command['until']
            assert observed['state'][command['until']['index']]==command['until']['equals']
            assert command.get('held',0)==command.get('pause',0)==0
        else:assert elapsed==command.get('frames',0)
        for field,wanted in command.get('expect',{}).items():
            actual=observed['state'][int(field)];assert actual==wanted
            checks.append(dict(frame=observed['endFrame'],index=int(field),expected=wanted,actual=actual,passed=True))
        last=observed['endFrame']
    assert checks==run['checks']and run['frames']==last and 12000<last<=plan['maximumFrames']
    stages=[]
    first=run['actions'][12];assert first['state'][0:2]==[1,1]and 0<first['state'][6]<=240
    stages.append(dict(stage=1,readyFrame=first['endFrame'],battleFrame=first['state'][6],music=first['state'][18]))
    for stage in range(2,7):
        entry,ready=run['actions'][13+(stage-2)*2:15+(stage-2)*2]
        assert entry['state'][0:2]==ready['state'][0:2]==[1,stage]
        assert ready['endFrame']-entry['endFrame']==240
        assert entry['state'][6]>1000 and 0<ready['state'][6]<=240,'The actual battle clock must reset and advance after the pending stage marker'
        assert ready['state'][13:16]==[2,1,2]
        stages.append(dict(stage=stage,entryFrame=entry['endFrame'],readyFrame=ready['endFrame'],battleFrame=ready['state'][6],music=ready['state'][18]))
    # Catalog track indices for the six normal stage themes.
    assert [row['music']for row in stages]==[1,3,5,7,9,11]
    end,stable=run['actions'][-2:]
    assert end['state'][0:2]==stable['state'][0:2]==[2,6]
    assert end['state'][7]==stable['state'][7]==1 and stable['state'][11:13]==[3,1]
    assert stable['endFrame']-end['endFrame']==60
    assert stable['state'][6]==end['state'][6]and stable['state'][9]==end['state'][9]
    assert stable['state'][9]==plan['expectedTerminalScoreUnits']==reference['terminalMenuSamples'][-1]['score']==154806314
    journal_stages=[];previous=0
    for row in run['rows']:
        assert previous<row['frame']<=last and row['clockNs']==row['frame']*1000000000//60;previous=row['frame']
        assert len(row['state'])==20 and row['key']==row['state'][:2]+row['state'][3:6]+row['state'][7:16]
        state=row['state']
        if state[0]==1 and state[1]not in journal_stages:journal_stages.append(state[1])
    assert journal_stages==[1,2,3,4,5,6]
    expected_captures=['stage-one-ready',*[f'stage-{stage}-entry'for stage in range(2,7)],'natural-replay-end','stable-replay-end']
    assert [capture['label']for capture in run['captures']]==expected_captures
    for capture in run['captures']:
        raw=read(folder/capture['file']);assert len(raw)==640*480*4 and SHA(raw)==capture['sha256']
        live=load(folder/capture['liveAnimations']['file'])
        assert SHA(read(folder/capture['liveAnimations']['file']))==capture['liveAnimations']['sha256']
        assert live['complete']and live['readOnly']and live['ordinaryAndOverlayRegistryWalk']and live['comparedValues']==303
        assert len(live['rows'])==live['expected']==capture['liveAnimations']['count']
        assert all(len(row)==303 for row in live['rows'])
        assert len({row[0]for row in live['rows']})==live['expected']
    old=ROOT/'artifacts/th14/native-frame-readback-oct27/initial-decode-full-replay'
    old_gles=load(old/'gles/report.json');old_gpu=load(old/'webgpu/report.json')
    assert not old_gles['completed']and old_gles['frames']==123352 and len(old_gles['checks'])==36 and len(old_gles['captures'])==6
    assert not old_gpu['completed']and old_gpu['frames']==104899 and 'wall budget exhausted'in old_gpu['error']
    assert read(old/'gles/natural-replay-end.bgra')==read(folder/'natural-replay-end.bgra')
    prefix=load(ROOT/'artifacts/th14/native-frame-readback-oct28/registry-menu-prefix/report.json')
    assert prefix['completed']and prefix['frames']==753 and len(prefix['checks'])==20
    assert [x['liveAnimations']['count']for x in prefix['captures']]==[98,110,110]
    assert run['pendingAsyncCallbacks']==0 and run['virtualAudioStreamsCreated']>=1 and run['pcmFrames']>0
    result=dict(verifiedFiniteApplicationFullReplay=True,backend=args.backend,selection=[2,1,2],replaySha256=expected_replay,
        frames=last,assertions=len(checks),stages=stages,naturalReplayEndFrame=end['endFrame'],stableEndFrames=60,
        gameplayCodeCommit=code_commit,currentActualRunNotInherited=True,
        previousIncompleteVmObservationRetained=True,previousWebGpuWallBudgetFailureRetained=True,
        currentWebGpuFullReplayAccepted=False,
        finalLivingStock=1,finalScoreUnits=stable['state'][9],journalRows=len(run['rows']),capturedImages=len(run['captures']),
        actualCppApplicationAndRenderer=True,normalizedMenuInputsOnly=True,declaredPlatformClockAndAsyncQueue=True,
        inputFileUnchanged=True,gameplayOrStageOverrides=False,
        actualSilentSinkPcmFrames=run['pcmFrames'],reportedPcmSha256=run['pcmSha256'],
        rawPcmIndependentlyRetained=False,originalWholeApplicationPixelsOrPcmEqualNotAsserted=True,
        originalOrdinaryMenuEquivalence=False,physicalAudioDevicesOpened=0,browserAcceptance=False,
        wasmSha256=run['wasmSha256'],frozenRunnerSha256=run['toolSha256'],verifierSha256=SHA(Path(__file__).read_bytes()),
        bindings=bindings,completeGame=False,nativeEquivalent=False,
        scope='One actual production C++ Application cold-menu replay through all six stages and stable living end. Read-only state waits do not alter inputs or force progression. Frozen game/device build, real native GPU and declared logical SDL/WASI services with silent PCM sink. Images are retained outputs, not original full-Application visual comparisons; PCM is a sink hash. No original ordinary UI, physical devices, browser/IndexedDB, all-mode or whole-game equivalence.')
    output=args.output.resolve();assert output.is_relative_to(ROOT/'docs/porting')or output.is_relative_to(ROOT/'artifacts/th14')
    if args.check:assert json.loads(output.read_bytes())==result
    else:output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({key:result[key]for key in ['verifiedFiniteApplicationFullReplay','frames','assertions','stages','naturalReplayEndFrame','capturedImages','browserAcceptance']}))


if __name__=='__main__':main()
