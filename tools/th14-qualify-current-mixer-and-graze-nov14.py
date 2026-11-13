"""Bind current silent-mixer and captured-query evidence with explicit limits."""
from pathlib import Path
import hashlib
import json
import os

R=Path(__file__).resolve().parents[1]
H=R/'artifacts/th14/ordinary-difficulties-nov14'
A=R/'artifacts/th14/current-audio-mixer-nov14'
load=lambda p:json.loads(p.read_bytes())
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()


def write(p,q):
    t=p.with_name(p.name+'.new');t.write_text(json.dumps(q,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');os.replace(t,p)


def main():
    a=load(A/'run-loop-v3/report.json');b=load(A/'component-loop/build.json')
    assert a['passed'] and a['closed'] and not a['exception'] and not a['errors']
    assert a['soundCases']==76 and a['fadeCases']==48 and a['loopCaseCount']==18 and len(a['musicCases'])==3
    assert a['sourceWasmSha256']==b['outputs']['candidate']['wasmSha256']==sha(A/'component-loop/candidate.wasm')
    assert a['toolSha256']==sha(R/'tools/th14-run-current-audio-mixer-nov14.mjs')
    assert b['builderSha256']==sha(R/'tools/th14-build-current-audio-mixer-nov14.py')
    for path,digest in {**b['sourceBindingsByMode']['candidate'],**b['objectBindings']}.items():assert sha(R/path)==digest,path
    assert a['platform']['audibleOutput'] is False and not a['platform']['stream'] and not a['platform']['openFiles']
    assert [r['id'] for r in a['sounds'] if r['loop']]==[20,55]
    assert a['musicCases'][0]['firstSecond']['energy']==0 and a['musicCases'][0]['normal']['energy']>0
    fades=load(R/'artifacts/th14/music-fade-native.json');assert fades['executableSha256']=='f08e885e28d2e0fc8c579e88034dd7de8f2a648d8f08ce781cf08eadc9ffe353'
    archive=Path(load(R/'runtimes/th14/target.json')['dataArchives']['th14.dat']['path'])
    archive_sha=sha(archive);assert archive_sha=='57d84a5cbe82460931cca26f090a0fde7aef180889ce5bfe8315851fc97b0233'
    aq=dict(acceptanceStandard='observable-behavior-alignment',passed=True,actualCurrentMixer=True,
            soundCases=76,loopingSoundIds=[20,55],fadeNativeTimelines=48,musicStateCases=a['musicCases'],
            musicLoopCases=a['loopCases'],musicLoopCaseCount=18,mixedFrames=a['totalMixedFrames'],
            providersVerified=145,virtualAudioClock=True,sdlBoundaryDeclared=True,silent=True,
            audibleOutput=False,newGameAssetCopies=False,sourceWasmSha256=a['sourceWasmSha256'],
            archiveSha256=archive_sha,buildSha256=sha(A/'component-loop/build.json'),
            reportSha256=sha(A/'run-loop-v3/report.json'),nativeFadeReportSha256=sha(R/'artifacts/th14/music-fade-native.json'),
            titleFirstSecondHasSourceSilence=True,titleSilenceFfmpegLogSha256=sha(A/'track01-ten-seconds-ffmpeg.log'),
            originalDirectSoundPcmCompared=False,completeBrowserAudioAccepted=False,
            gameLogicChanged=False,newRuntimeDeployed=False,completeGame=False)
    write(R/'docs/porting/th14-current-audio-mixer-nov14.json',aq)
    g=load(H/'stage3-collision-retail-oracle-v2.json');n=load(H/'stage3-collision-observer-neutrality-v2.json')
    p=load(H/'stage3-heading-math-component-v2/report.json');c=load(H/'player-collision-current-recheck/report.json')
    assert g['passed'] and g['cases']==393 and g['mismatchCount']==0
    assert n['postRunReadoutBaselineTerminalGameplayUnchanged'] and n['baselineCallbacks']==120192
    assert p['productionPolarVsFreshRetailDifferences']==0 and p['cases']==393
    assert g['captureSha256']==p['captureSha256'] and g['captureBytes']==66024
    assert c['passed'] and c['cases']==10800 and c['wasmUnchanged']
    for rel,q in [('tools/th14-oracle-stage3-collision-queries-nov14.py',g),
                  ('tools/th14-check-captured-heading-math-nov14.mjs',p),
                  ('tools/th14-player-collision-current-recheck-nov14.mjs',c)]:assert sha(R/rel)==q['toolSha256']
    gq=dict(acceptanceStandard='observable-behavior-alignment',selectedTerminalGameplayUnchanged=True,
            callbacks=120192,nearBoundaryQueries=393,eligibleGrazeQueries=196,queryCaptureBytes=66024,
            retailQueryMismatches=0,retailInstructionsModified=False,actualProductionPolarCases=393,
            productionPolarVsFreshRetailDifferences=0,storedVelocityVsFreshHeadingDifferences=100,
            storedVelocityHistoryDifferenceDoesNotAloneProveBug=True,currentCollisionRecheckCases=10800,
            currentCollisionModuleByteEqualToRetained=True,closestQueries=g['closestBoundaryQueries'][:6],
            captureSha256=g['captureSha256'],oracleReportSha256=sha(H/'stage3-collision-retail-oracle-v2.json'),
            neutralReportSha256=sha(H/'stage3-collision-observer-neutrality-v2.json'),
            polarReportSha256=sha(H/'stage3-heading-math-component-v2/report.json'),
            oneExtraGrazeCauseEstablished=False,firstDivergentInStageFrameLocated=False,
            originalTrajectoriesOrPlayerTimelineAccepted=False,gameLogicChanged=False,completeGame=False)
    write(R/'docs/porting/th14-stage3-graze-queries-nov14.json',gq)
    invalid=H/'marisab-lunatic-stage3-collision-boundaries-v1/stage3-collision-queries.u32'
    write(H/'stage3-invalid-capture-retained.json',dict(captureBytes=invalid.stat().st_size,
          sha256=sha(invalid),validQueryCapture=False,reason='Buffer.from(Uint32Array) retained low bytes only.',
          correctedValidCaptureBytes=66024,completeGame=False))
    state_path=R/'artifacts/th14/option-recall-once-nov02/work-state.json';state=load(state_path)
    state['goalTurnNov14CurrentMixerAndGraze']=dict(classification='progress',onlyTitle='th14',silent=True,
        mixerEvidence='docs/porting/th14-current-audio-mixer-nov14.json',
        grazeEvidence='docs/porting/th14-stage3-graze-queries-nov14.json',
        sourceFix=False,queryExportBugFixed=True,originalCaptureFailureRetained=True,
        allJobsTerminal=True,next=['Full browser/GPU and audio delivery acceptance',
            'Optional practice tools, mobile touch and independent Purple replay interoperability',
            'Retain stage-3 extra graze; compare original trajectory/player inputs before any rule change'],completeGame=False)
    write(state_path,state)
    print(json.dumps(dict(mixerSoundCases=76,nativeFades=48,mixerLoops=18,mixedFrames=a['totalMixedFrames'],
                         capturedQueries=393,retailQueryMismatches=0,extraGrazeUnresolved=True,completeGame=False)))


if __name__=='__main__':
    main()
