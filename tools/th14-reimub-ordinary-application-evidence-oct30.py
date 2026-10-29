"""Recheck the current repaired core's actual cold-menu ReimuB Normal flow.

Requires a terminal successful Application report. Selected terminal score/stock
are compared to a declared warm original reference; images and PCM are retained
outputs, not original whole-Application comparisons.
"""
from pathlib import Path
import argparse,hashlib,io,json,shutil,struct,subprocess,tarfile
ROOT=Path(__file__).resolve().parents[1]
SHA=lambda b:hashlib.sha256(b).hexdigest()

def verify(home):
    bindings={}
    def read(path):
        raw=path.read_bytes();bindings[path.relative_to(ROOT).as_posix()]={'bytes':len(raw),'sha256':SHA(raw)};return raw
    def load(path):return json.loads(read(path))
    plan=load(home/'plan.json');folder=home/'gles';run=load(folder/'report.json')
    assert run['completed']and not run['error'],'Require terminal successful actual Application run'
    end_process=load(home/'process-end.json');assert end_process['exitCode']==0
    assert run['schema']=='th14/native-application-run/1'and run['backend']=='gles'
    assert run['actualProductionApplicationAndDevices']and run['platformClockAndIoDeclared']
    assert run['physicalAudioDevicesOpened']==0 and not run['appUiControlled']and not run['browserRun']
    assert not run['browserAcceptance']and not run['completeGame']and not run['nativeEquivalent']
    commit='57a544191704e0ce64cd46de85fe648a3e152097';assert plan['sourceCommit']==commit
    build_home=ROOT/plan['build'];build=load(build_home/'build.json')
    assert build['compiled']and build['backend']=='gles'
    assert run['wasmSha256']==build['wasmSha256']==plan['wasmSha256']==SHA(read(build_home/'application.wasm'))
    assert run['buildReportSha256']==SHA(read(build_home/'build.json'))
    assert run['toolSha256']==plan['runnerSha256']==SHA(read(folder/'run-tool.py'))==SHA(read(ROOT/plan['runner']))
    for name,row in build['sourceBindings'].items():assert SHA(read(ROOT/name))==row['sha256'],name
    core=load(ROOT/'artifacts/th14/replay-construction-oct30/core-build/observer-build.json')
    assert SHA(read(ROOT/'artifacts/th14/replay-construction-oct30/core-build/observer-build.json'))==build['coreBuildSha256']
    assert build['coreObjects']==core['objectBindings']and len(core['objectBindings'])==plan['verifiedCoreObjects']==141
    archive=subprocess.check_output(['git','-C',str(ROOT/'tools/tmp/github-source-release'),'archive','--format=tar',commit,'runtimes/th12/th12_web/cpp/game'])
    with tarfile.open(fileobj=io.BytesIO(archive))as tree:
        for name,digest in core['sourceHashes'].items():
            assert SHA(tree.extractfile('runtimes/th12/'+name).read())==digest==build['coreSourceHashes'][name]
    for item in core['objectBindings']:assert SHA(read(Path(item['path'])))==item['sha256']
    scenario=load(home/'scenario.json');assert run['scenarioSha256']==plan['scenarioSha256']==SHA(read(home/'scenario.json'))
    assert plan['scenarioUpperBoundFrames']==sum(a['frames']for a in scenario['actions'])==138767
    assert plan['maximumFrames']==150000 and plan['maximumWallSeconds']==3600
    assert plan['minimumFreeBytes']==100*1024**3 and plan['maximumOutputBytes']==128*1024**2 and not plan['automaticNextCase']
    replay_sha='c48412a95f0fe9f685d97574e8ab0655d41e44ff9c41fda7bf788589b1b29c74'
    source=read(ROOT/'artifacts/th14/royalflare-coverage-matrix-oct16/inputs/reimub-normal.rpy')
    assert SHA(source)==plan['sourceReplaySha256']==replay_sha
    assert read(home/'initial-save/replay/th14_01.rpy')==read(folder/'save/replay/th14_01.rpy')==source
    assert run['initialSave']==run['finalSave']=={'replay/th14_01.rpy':{'bytes':len(source),'sha256':replay_sha}}
    metadata=load(ROOT/'artifacts/th14/royalflare-coverage-matrix-oct16/inputs/reimub-normal-source.json')
    assert metadata['actualNativeCodecVerified']and metadata['sha256']==replay_sha
    assert [metadata[k]for k in ['character','subtype','difficulty']]==[0,1,1]
    assert [s['stage']for s in metadata['stages']]==[1,2,3,4,5,6]
    decoded=read(ROOT/'artifacts/th14/royalflare-coverage-matrix-oct16/inputs/reimub-normal-decoded.bin')
    assert SHA(decoded)==metadata['decodedSha256']and struct.unpack_from('<I',decoded,20)[0]==91452576
    reference=load(ROOT/'artifacts/th14/retail-reimub-normal-callback-rng-hardware-oct26/report.json')
    assert SHA(read(ROOT/'artifacts/th14/retail-reimub-normal-callback-rng-hardware-oct26/report.json'))==plan['originalWarmReferenceSha256']
    assert reference['sourceFullReplaySha256']==replay_sha and reference['callbacks']==122537
    assert reference['childExited']and not reference['error']and reference['observedForcedReplayEndMenu']
    assert reference['instructionBytesPatched']==reference['rngOrCounterWrites']==0
    assert reference['caseInitialization']['attractBitClearOnly']and not reference['ordinaryMenuReplayInitialization']
    checks=[];last=0;assert len(run['actions'])==len(scenario['actions'])==25
    for command,observed in zip(scenario['actions'],run['actions']):
        assert set(command)<={'frames','held','pause','capture','expect','until'}
        assert observed['atFrame']==last and observed['held']==command.get('held',0)and observed['pause']==command.get('pause',0)
        elapsed=observed['endFrame']-last;assert 0<=elapsed<=command['frames']
        if 'until'in command:
            assert command.get('held',0)==command.get('pause',0)==0 and observed['until']==command['until']
            assert observed['state'][command['until']['index']]==command['until']['equals']
        else:assert elapsed==command['frames']
        for name,wanted in command.get('expect',{}).items():
            actual=observed['state'][int(name)];assert actual==wanted
            checks.append(dict(frame=observed['endFrame'],index=int(name),expected=wanted,actual=actual,passed=True))
        last=observed['endFrame']
    assert checks==run['checks']and run['frames']==last<=plan['maximumFrames']
    stages=[];first=run['actions'][12];assert first['state'][0:2]==[1,1]and 0<first['state'][6]<=240
    stages.append(dict(stage=1,readyFrame=first['endFrame'],battleFrame=first['state'][6],music=first['state'][18]))
    for stage in range(2,7):
        entry,ready=run['actions'][13+(stage-2)*2:15+(stage-2)*2]
        assert entry['state'][0:2]==ready['state'][0:2]==[1,stage]
        assert ready['endFrame']-entry['endFrame']==240 and entry['state'][6]>1000 and 0<ready['state'][6]<=240
        assert ready['state'][13:16]==[0,1,1]
        stages.append(dict(stage=stage,entryFrame=entry['endFrame'],readyFrame=ready['endFrame'],battleFrame=ready['state'][6],music=ready['state'][18]))
    assert [s['music']for s in stages]==[1,3,5,7,9,11]
    end,stable=run['actions'][-2:];assert end['state'][0:2]==stable['state'][0:2]==[2,6]
    assert end['state'][9]==stable['state'][9]==plan['expectedFinalScoreUnits']==91452576
    assert end['state'][7]==stable['state'][7]==plan['expectedFinalLives']==8
    assert stable['state'][11:13]==[3,1]and stable['endFrame']-end['endFrame']==60
    assert end['state'][6]==stable['state'][6]
    native_end=reference['terminalMenuSamples'][-1];assert native_end['score']==stable['state'][9]and native_end['lives']==stable['state'][7]
    journal=[];previous=0
    for row in run['rows']:
        assert previous<row['frame']<=last and row['clockNs']==row['frame']*1000000000//60;previous=row['frame']
        state=row['state'];assert len(state)==20 and row['key']==state[:2]+state[3:6]+state[7:16]
        if state[0]==1 and state[1]not in journal:journal.append(state[1])
    assert journal==[1,2,3,4,5,6]
    assert [c['label']for c in run['captures']]==['stage-one-ready',*[f'stage-{n}-entry'for n in range(2,7)],'natural-replay-end','stable-replay-end']
    for capture in run['captures']:
        raw=read(folder/capture['file']);assert len(raw)==640*480*4 and SHA(raw)==capture['sha256']
    assert run['pendingAsyncCallbacks']==0 and run['virtualAudioStreamsCreated']>=1 and run['pcmFrames']>0
    assert run['metadataEpochAtFrameZero']==plan['metadataEpochAtFrameZero']==1793037600
    assert run['declaredInitialGameTicks']==plan['declaredInitialGameTicks']==479352152
    entropy=load(folder/'declared-process-entropy.json')
    assert entropy['events']==[dict(bytes=4,value=plan['declaredProcessCookie'],beforeGameCallbacks=True)]
    assert plan['declaredProcessCookie']==3067924159 and entropy['externalEnvironmentInputDeclared']and not entropy['gameRngStateSupplied']
    assert not run.get('workerPauseEvents')and not run.get('workerLifecycleControlledViaProductionMethods')
    observed_bytes=sum(p.stat().st_size for p in folder.rglob('*')if p.is_file());assert observed_bytes<=128*1024**2 and shutil.disk_usage(home).free>=100*1024**3
    return dict(verifiedFiniteApplicationFullReplay=True,sourceCommit=commit,selection=[0,1,1],frames=last,assertions=len(checks),stages=stages,naturalReplayEndFrame=end['endFrame'],stableEndFrames=60,finalScoreUnits=91452576,finalLivingStock=8,terminalScoreEqualsSourceAndDeclaredWarmOriginal=True,inputFileUnchanged=True,replaySha256=replay_sha,coreObjectsVerified=141,actualCppApplicationAndRenderer=True,normalizedColdMenuInputsOnly=True,declaredHostClockEntropyAndAsyncDelivery=True,nativeApplicationWorkerFeatureOff=True,ordinaryOriginalGuiAccepted=False,priorFullAcceptanceInherited=False,retainedFullImages=len(run['captures']),reportedSilentSinkPcmFrames=run['pcmFrames'],reportedPcmSha256=run['pcmSha256'],originalWholeApplicationPixelsOrPcmCompared=False,rawPcmIndependentlyRetained=False,physicalAudioDevicesOpened=0,browserAcceptance=False,wasmSha256=run['wasmSha256'],verifierSha256=SHA(Path(__file__).read_bytes()),bindings=bindings,completeGame=False,nativeEquivalent=False)

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--home',type=Path,required=True);parser.add_argument('--output',type=Path,required=True);parser.add_argument('--check',action='store_true');args=parser.parse_args()
    home=args.home.resolve();output=args.output.resolve();assert home.is_relative_to(ROOT/'artifacts/th14')and (output.is_relative_to(ROOT/'artifacts/th14')or output.is_relative_to(ROOT/'docs/porting'))
    result=verify(home)
    if args.check:assert json.loads(output.read_bytes())==result
    else:output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:result[k]for k in ['verifiedFiniteApplicationFullReplay','frames','assertions','finalScoreUnits','finalLivingStock','browserAcceptance']}))
if __name__=='__main__':main()
