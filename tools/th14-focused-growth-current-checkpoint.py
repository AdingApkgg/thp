"""Bind the current growth fix to actual full-run evidence without promoting failures."""
import hashlib,json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SHA=lambda b:hashlib.sha256(b).hexdigest()

def main():
    bindings={}
    def bind(name):
        b=(ROOT/name).read_bytes();bindings[name]=dict(bytes=len(b),sha256=SHA(b));return b
    load=lambda name:json.loads(bind(name))
    engine=load('runtimes/th13/th13_web/artifacts/cpp/engine-th14-build.json')
    for name,digest in engine['sourceHashes'].items():assert SHA(bind('runtimes/th12/th12_web/'+name))==digest,name
    cases=[]
    for label,title,frames,stage in [
        ('zps-normal-focused-growth-oct14','SakuyaA Normal',96016,6),
        ('zps-reimub-lunatic-focused-growth-oct14','ReimuB Lunatic',98074,6),
        ('zps-reimua-lunatic-focused-growth-oct14','ReimuA Lunatic',90793,6),
        ('zps-reimua-extra-focused-growth-oct14','ReimuA Extra',39458,7)]:
        directory='artifacts/th14/public-replay-playback/'+label
        r=load(directory+'/report.json');assert r['sourceHashes']==engine['sourceHashes']
        assert (r['frames'],r['stage'],r['candidatePlaybackEnded'])==(frames,stage,True)
        assert not r['gameOverRequested'] and not r['error'] and not r['skipped'] and not r['unsupported']
        assert r['physicalInvocationOrder'] and r['transitionCallbacksRetained']
        assert not r['invulnerabilityOverride'] and not r['forcedProgression']
        for name,key in [('selected-state.u32','selectedStateSha256'),('callback-active.u8','callbackActiveSha256'),('public-replay.wasm','wasmSha256')]:assert SHA(bind(directory+'/'+name))==r[key]
        cases.append(dict(title=title,frames=frames,stage=stage,candidatePlaybackEnded=True,gameOver=False,nativeEquivalent=False,replaySha256=r['replaySha256']))
    lunatic=load('docs/porting/th14-reimua-lunatic-continuous-focused-growth-full-oct14.json')
    normal=load('docs/porting/th14-normal-continuous-focused-growth-oct14.json')
    for r,count in [(lunatic,90793),(normal,96016)]:
        assert not r['passed'] and r['comparedCallbacks']==count and r['gameplayDifferences']==25
        assert len(r['equalSelectedGameplayFields'])==29 and r['allRemainingGameplayDifferencesDuringInactiveLoading']
    extra=load('docs/porting/th14-extra-continuous-focused-growth-oct14.json')
    assert extra['passed'] and extra['comparedCallbacks']==39458 and extra['gameplayDifferences']==0
    assert len(extra['equalSelectedGameplayFields'])==30
    combat=load('docs/porting/th14-focused-growth-full-combat-verified-oct14.json')
    assert combat['diagnosticEvidenceVerified'] and not combat['completeGame'] and not combat['nativeEquivalent']
    assert not combat['comparisonPassed'] and combat['comparedCallbacks']==90793
    assert combat['sourceHashes']==engine['sourceHashes']
    assert (combat['rawGameplayDifferences'],combat['rawVisualDifferences'],combat['retainedDetailDifferences'])==(25,181570,99)
    assert (combat['inactiveLoadingDetailDifferences'],combat['activeBattleDetailDifferences'])==(72,27)
    assert combat['activeAreaDifferenceColumnCounts']=={'8':8,'18':27,'19':27}
    growth=load('docs/porting/th14-focused-area-growth-verified-oct14.json')
    assert growth['diagnosticEvidenceVerified'] and growth['candidateCompleteLunaticFrames']==90793
    assert growth['beforeFocusedRadius']==152 and growth['expectedFocusedRadius']==56
    sanitizer=load('docs/porting/th14-sanitized-replay-focused-growth-oct14-observed-oct13.json')
    assert sanitizer['passed'] and sanitizer['frames']==96016 and not sanitizer['errors']
    assert sanitizer['sourceHashes']==engine['sourceHashes']
    matrix=load('docs/porting/th14-sanitized-input-parity-matrix-focused-growth-oct14-observed-oct14.json')
    assert matrix['sanitizerMatrixVerified'] and matrix['sourceHashes']==engine['sourceHashes']
    assert len(matrix['cases'])==3 and all(r['sanitizerPassed'] and not r['errors'] and r['candidatePlaybackEnded'] for r in matrix['cases'])
    browser=load('docs/porting/th14-focused-growth-browser-flow-verified-oct14.json')
    assert browser['observedBrowserFlowVerified'] and browser['replay']['frames']==468
    assert browser['replay']['actualNativeCodecVerified'] and browser['consoleWarnings']==1 and browser['consoleErrors']==0
    sdl=load('runtimes/th14/th14_web/artifacts/sdl3-release/build.json')
    assert SHA(bind('runtimes/th14/th14_web/artifacts/sdl3-release/th11.wasm'))==sdl['sha256']
    assert browser['build']==sdl
    for name,digest in {**sdl['sources'],**sdl['headers']}.items():assert SHA(bind('runtimes/th12/'+name))==digest,name
    result=dict(diagnosticCheckpointVerified=True,completeGame=False,nativeEquivalent=False,
        sourceFilesVerified=len(engine['sourceHashes']),sourceHashes=engine['sourceHashes'],cases=cases,
        lunaticNativeCallbacks=90793,lunaticEqualGameplayFields=29,lunaticLoadingGameplayDifferences=25,
        lunaticVisualDifferences=181570,lunaticDetailDifferences=99,lunaticLoadingEnemyNextIdDifferences=72,
        lunaticActiveDamageAreaDifferences=27,lunaticActiveAreaZWordDifferences=8,normalNativeCallbacks=96016,normalLoadingGameplayDifferences=25,
        extraNativeCallbacks=39458,extraEqualGameplayFields=30,extraGameplayDifferences=0,extraVisualDifferences=78916,
        sanitizerCases=[dict(title='SakuyaA Normal',frames=96016,passed=True),*matrix['cases']],
        browserReplayFrames=468,browserConsoleWarnings=1,browserConsoleErrors=0,
        sdl=dict(bytes=sdl['bytes'],sha256=sdl['sha256'],sources=len(sdl['sources']),headers=len(sdl['headers'])),
        bindings=bindings,toolSha256=SHA(Path(__file__).read_bytes()),
        scope='The focused-shot spawn now clears growth in the actual reused damage-area record as original451b3a does. Four intact public inputs naturally finish in current production and nonrecovering ASAN/UBSan. The independent uninterrupted90793-callback original Lunatic comparison retains25 loading gameplay counter differences,181570 visual RNG differences,72 loading enemyNextId and27 active damage-area records with owner-memory differences;8 of those records also have differing raw position.z words. Extra has30 selected gameplay fields equal throughout39458 original callbacks with78916 visual differences retained. Declared warm replay initialization remains. Ordinary browser short recording save/reload/playback/natural return and original codec are observed and source-bound; one Launcher update warning remains. Current ordinary full score/ending/storage, all shot types/difficulties, complete owner memory, visual RNG, original menu/loading lifecycle, graphics/audio and whole-game1:1 remain separate. Historical checkpoints are not silently promoted to current-source passes.')
    (ROOT/'docs/porting/th14-focused-growth-current-checkpoint-oct14.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k not in ('sourceHashes','bindings','scope','sanitizerCases')}))

if __name__=='__main__':main()
