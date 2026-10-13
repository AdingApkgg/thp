"""Bind existing independent stage checks and current builds without extending their scope."""
import hashlib,json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SHA=lambda data:hashlib.sha256(data).hexdigest()
read=lambda path:json.loads(path.read_text(encoding='utf-8'))
bind=lambda path:dict(path=path.relative_to(ROOT).as_posix(),bytes=path.stat().st_size,sha256=SHA(path.read_bytes()))

def main():
    rt=ROOT/'runtimes/th12/th12_web'
    engine=read(ROOT/'runtimes/th13/th13_web/artifacts/cpp/engine-th14-build.json')
    assert len(engine['sourceHashes'])==265
    for name,digest in engine['sourceHashes'].items():assert SHA((rt/name).read_bytes())==digest,name
    bindings=[];stages=[]
    for stage in range(1,7):
        path=ROOT/f'docs/porting/th14-zps-normal-stage{stage}-current-core-verified-oct13.json'
        case=read(path)
        assert case['passed'] and not case['completeGame'] and not case['nativeEquivalent']
        assert case['sourceFilesVerified']==265 and case['capturedObjectDifferencesReportedByProducer']==0
        frames=case['backendFrames'] if stage==1 else case['comparedFrames']
        assert case.get('productionGameplayDifferences',case.get('gameplayDifferences'))==0
        producer=read(ROOT/f"docs/porting/{'th14-physical-replay-native-trace-zps-normal-stage6-control-clock-verified-oct13' if stage==6 else f'th14-natural-replay-native-trace-zps-normal-stage{stage}-final-core-oct13'}-observed-oct13.json")
        assert producer['passed'] and producer['engineBuild']['sourceHashes']==engine['sourceHashes']
        assert producer['comparedFrames']==frames
        for binding in case['bindings']:
            p=ROOT/binding['path'];assert bind(p)==binding,p
        stages.append(dict(stage=stage,frames=frames,gameplayDifferences=0,
                           retainedVisualDifferences=case['retainedStartupVisualWords'],
                           nativeCaptureTimedOut=case.get('nativeCaptureTimedOut'),
                           repeatedStageClockRows=case.get('repeatedStageClockRows',0)))
        bindings.append(bind(path))
    continuous_path=ROOT/'docs/porting/th14-zps-continuous-physical-active-current-observed-oct13.json'
    continuous=read(continuous_path)
    assert continuous['candidatePlaybackEnded'] and not continuous['gameOverRequested']
    assert continuous['allProductionCallbacks']==continuous['playbackFrames']==96016
    assert continuous['inactiveCallbacksRetained']==750
    for stage in continuous['stages']:
        assert not stage['missingNativeInvocationIndices'] and not stage['productionRowsBeyondNativePrefix']
        assert set(stage['fieldDifferenceCounts'])<= {'pressed','visualSeed','visualCalls'}
        assert stage['fieldDifferenceCounts'].get('pressed',0)==int(stage['stage']>1)
    for binding in continuous['bindings']:assert bind(ROOT/binding['path'])==binding
    bindings.append(bind(continuous_path))
    sdl_path=ROOT/'runtimes/th14/th14_web/artifacts/sdl3-release/build.json';sdl=read(sdl_path)
    assert sdl['releaseProfile'] and sdl['title']==14 and not sdl['completeGame']
    for name,digest in {**sdl['sources'],**sdl['headers']}.items():assert SHA((ROOT/'runtimes/th12'/name).read_bytes())==digest,name
    wasm=ROOT/'runtimes/th14/th14_web/artifacts/sdl3-release/th11.wasm'
    assert SHA(wasm.read_bytes())==sdl['sha256'] and wasm.stat().st_size==sdl['bytes']
    bindings.append(bind(sdl_path))
    result=dict(checked=True,completeGame=False,nativeEquivalent=False,ordinaryMenuLoaderVerified=False,
                productionSourceFiles=265,stages=stages,independentStageFrames=sum(s['frames'] for s in stages),
                independentStageGameplayDifferences=0,continuousProductionFrames=96016,
                continuousCandidatePlaybackEnded=True,continuousInactiveCallbacksRetained=750,
                continuousActiveFramesCompared=sum(s['comparedFrames'] for s in continuous['stages']),
                continuousRetainedPressedDifferences=5,
                sdlBuild=dict(bytes=sdl['bytes'],sha256=sdl['sha256'],sources=len(sdl['sources']),headers=len(sdl['headers'])),
                bindings=bindings,verifierSha256=SHA(Path(__file__).read_bytes()),
                scope='Compact binding of current-source independent warm stage comparisons and uninterrupted production playback. All 95266 active rows, including repeated stage clocks and final transition rows, remain in raw streams. Continuous production retains 750 inactive loading callbacks and five pressed differences versus independent stage startup. Stage6 native capture requested more frames and timed out; whole native completion is unverified. No uninterrupted native menu/loading/ending, all characters/difficulties/Extra, full graphics/audio/persistence or whole-game 1:1 claim.')
    output=ROOT/'docs/porting/th14-zps-normal-six-stage-current-checkpoint-oct13.json'
    output.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:result[k] for k in ('checked','independentStageFrames','continuousProductionFrames','continuousRetainedPressedDifferences','sdlBuild')}))

if __name__=='__main__':main()
