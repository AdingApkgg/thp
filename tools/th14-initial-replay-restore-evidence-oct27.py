"""Verify the initial ordinary-replay restore repair and retained full failure."""
from pathlib import Path
import argparse
import hashlib
import importlib
import json
import struct
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]
SHA=lambda raw:hashlib.sha256(raw).hexdigest()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--home',type=Path,default=ROOT/'artifacts/th14/initial-replay-restore-oct27')
    parser.add_argument('--output',type=Path,default=ROOT/'docs/porting/th14-initial-replay-restore-verified-oct27.json')
    parser.add_argument('--check',action='store_true');args=parser.parse_args();home=args.home.resolve();bindings={}
    def read(path):
        raw=path.read_bytes();bindings[path.relative_to(ROOT).as_posix()]=dict(bytes=len(raw),sha256=SHA(raw));return raw
    def load(path):return json.loads(read(path))
    native=load(home/'native-final/native.json');assert native['completed']and native['caseCount']==288
    assert native['stopAddress']==0x435f37 and not native['originalInstructionsModified']and not native['originalProcessLaunched']
    assert native['toolSha256']==SHA(read(home/'native-final/run-tool.py'))==SHA(read(ROOT/'tools/th14-initial-replay-restore-native-oct27.py'))
    sys.path.insert(0,str(ROOT/'tools'));image=importlib.import_module('th-anm-handlers').handlers(14)[0]
    assert SHA(image.data)==native['executableSha256']=='f08e885e28d2e0fc8c579e88034dd7de8f2a648d8f08ce781cf08eadc9ffe353'
    for row in native['originalInstructionSlices']:assert SHA(image.read(row['address'],row['bytes']))==row['sha256']
    decoded_path=ROOT/'artifacts/th14/replay-coverage-input-oct26/marisab-normal-kmk/th14_ud0593-decoded.bin'
    decoded=read(decoded_path);assert SHA(decoded)==native['decodedSha256'];headers={};offset=0x94
    for _ in range(struct.unpack_from('<I',decoded,0x78)[0]):
        stage,seed=struct.unpack_from('<HH',decoded,offset);headers[stage]=decoded[offset:offset+0xdc]
        offset+=0xdc+struct.unpack_from('<I',decoded,offset+8)[0]
    assert offset==len(decoded)and sorted(headers)==list(range(1,7))
    assert struct.unpack_from('<I',decoded,20)[0]==61284943 and struct.unpack_from('<I',decoded,0x88)[0]==8
    source_home=decoded_path.parent;source=load(source_home/'th14_ud0593-source.json')
    assert source['actualNativeCodecVerified']and source['decodedSha256']==SHA(decoded)
    assert source['sha256']==SHA(read(source_home/'th14_ud0593.rpy'))=='28d9d29a34cf1dd0e67d67a82c1f0a5f7c508543271e0f1b1e4cbed527ff7353'
    failed_native=load(home/'native-first/failure.json');assert not failed_native['completed']
    assert failed_native['sourceToolSha256']==SHA(read(home/'native-first/run-tool.py'))
    assert b'AssertionError'in read(home/'core-build-command.log');read(home/'core-build/rebuild-tool.py')
    rejected_plan=load(home/'ordinary-full/plan.json');rejected_scenario=load(home/'ordinary-full/scenario.json')
    assert sum(a.get('frames',0)for a in rejected_scenario['actions'])>rejected_plan['maximumFrames']
    assert b"sum(action.get('frames',0)"in read(home/'ordinary-full/gles-command.log')
    for case in native['cases']:
        header=headers[case['stage']];seed=struct.unpack_from('<H',header,2)[0];assert seed==case['seed']and case['flags']&2
        assert case['rngWords']==[seed|0xa5a50000,case['initialCalls'],seed|0x5a5a0000,0]
        writes=case['writeSequence'];assert len(writes)==31
        assert [(r['pc'],r['address'],r['bytes'],r['value'])for r in writes[:3]]==[
            (0x45610f,0x4db510,2,seed),(0x456123,0x4db508,2,seed),(0x456129,0x4db514,4,0)]
        assert [(r['pc'],r['address'],r['value'])for r in writes[3:]]==[
            (0x456133,0x4f5828+i*4,value)for i,value in enumerate(struct.unpack_from('<28I',header,0x14))]
    before=load(home/'model-before/comparison.json');after=load(home/'model-after/comparison.json')
    assert before['exactCases']==0 and before['legacyInitialCallContract']and after['exactCases']==288 and not after['legacyInitialCallContract']
    for d,folder in [(before,'model-before'),(after,'model-after')]:
        assert d['nativeReportSha256']==SHA(read(home/'native-final/native.json'))and d['actualRestoreBodyCompiled']and not d['currentGameSessionCompiled']
        assert d['wasmSha256']==SHA(read(home/folder/'probe.wasm'))and d['toolSha256']==SHA(read(home/folder/'run-tool.py'))
        assert d['rngWordsComparedPerCase']==4 and d['selectedEconomyWordsComparedPerCase']==22
    for old,new,case in zip(before['rows'],after['rows'],native['cases']):
        assert old['expected']==new['expected']and new['equal']and new['actual']==new['expected']and not old['equal']
        assert [i for i,(a,b)in enumerate(zip(old['actual'],old['expected']))if a!=b]==[0]
        assert old['actual'][0]==case['initialScriptSeed']|0xa5a50000
    for name,row in after['sourceBindings'].items():assert SHA(read(ROOT/name))==row['sha256']
    session_name='runtimes/th12/th12_web/cpp/game/GameSession.cpp'
    old_source=subprocess.check_output(['git','-C',str(ROOT/'tools/tmp/github-source-release'),'show','6ac61159f627700c64c9a79fdef4b7530d399ad4:'+session_name])
    assert before['sourceBindings'][session_name]['sha256']==SHA(old_source)
    core=load(home/'core-build-v2/observer-build.json');assert core['engineSourcesRecompiledForThisLink']==2 and core['engineObjectsReusedForThisLink']==139
    assert core['unusedHeaderGraphProof']['allAbsentFromActualIncludeGraph']and core['unusedHeaderGraphProof']['scannedCoreSources']==141
    for name,digest in core['recompiledSources'].items():assert SHA(read(ROOT/'runtimes/th12'/name))==digest==SHA(read(home/'core-build-v2'/Path(name).name))
    for row in core['objectBindings']:assert SHA(read(Path(row['path'])))==row['sha256']
    build=load(home/'application-build-gles/build.json');assert build['coreBuildSha256']==SHA(read(home/'core-build-v2/observer-build.json'))
    assert build['wasmSha256']==SHA(read(home/'application-build-gles/application.wasm'))
    for name,row in build['sourceBindings'].items():assert SHA(read(ROOT/name))==row['sha256']
    demo=load(home/'demo-gles/report.json');baseline=load(ROOT/'artifacts/th14/application-process-input-oct27/attract-quad-gles/report.json')
    assert demo['completed']and not demo['error']and demo['frames']==2264 and len(demo['checks'])==7
    assert demo['wasmSha256']==build['wasmSha256']and demo['rows']==[r for r in baseline['rows']if r['frame']<=2264]
    for capture in demo['captures']:
        assert capture in baseline['captures'];assert read(home/'demo-gles'/capture['file'])==read(ROOT/'artifacts/th14/application-process-input-oct27/attract-quad-gles'/capture['file'])
    old_audio=load(ROOT/'artifacts/th14/application-render-trace-oct27/gles-bias-application/run/report.json')
    old_audio_build=load(ROOT/'artifacts/th14/application-render-trace-oct27/gles-bias-application/build/build.json')
    old_core=load(ROOT/'artifacts/th14/replay-coverage-input-oct26/beam-owned-field-observer-final/observer-build.json')
    assert old_audio_build['coreSourceHashes']==old_core['sourceHashes']and old_audio['completed']and old_audio['frames']==2264
    assert old_audio['rows']==demo['rows']and old_audio['pcmFrames']==demo['pcmFrames']==1508352 and old_audio['pcmSha256']==demo['pcmSha256']
    full=load(home/'ordinary-full-v2/gles/report.json');plan=load(home/'ordinary-full-v2/plan.json');scenario=load(home/'ordinary-full-v2/scenario.json')
    assert not full['completed']and full['error']=="AssertionError('Declared state was not reached within the frame budget')"and full['frames']==27251
    assert full['wasmSha256']==build['wasmSha256']and not full['physicalAudioDevicesOpened']
    assert plan['minimumFreeBytes']==100*1024**3 and plan['maximumOutputBytes']==128*1024**2 and plan['maximumFrames']==150000
    assert sum(a.get('frames',0)for a in scenario['actions'])==plan['scenarioUpperBoundFrames']==129854
    assert sorted({r['state'][1]for r in full['rows']if r['state'][1]})==[1,2]
    assert full['rows'][-1]['state'][0:2]==[2,2]and full['rows'][-1]['state'][7]==0xffffffff
    assert len(full['checks'])==20 and len(full['rows'])==8434
    result=dict(schema='th14/initial-ordinary-replay-restore-repair/1',verifiedInitialRestoreCallContract=True,nativeCases=288,
        oldCallContractExactCases=0,currentCallContractExactCases=288,sourceReplayStages=6,bothSeedsRestoredForOrdinaryReplay=True,
        scriptCallCountPreserved=True,gameCallCountReset=True,actualRestoreBodyCompared=True,wholeGameSessionComparedToNative=False,
        coreSourcesRecompiled=2,coreObjectsReused=139,actualApplicationOrdinaryMenuReachedStage2=True,
        ordinaryFullReplayAccepted=False,failedActualApplicationFrames=27251,failedActualApplicationJournalRows=8434,
        assertionsPassedBeforeFullFailure=20,sourceDeclaredScoreUnits=61284943,sourceDeclaredReached=8,
        ordinaryCurrentFinalObservedScoreUnits=full['rows'][-1]['state'][9],ordinaryCurrentFinalObservedLives=0xffffffff,
        oldWarmCaseFailureUniquelyAttributed=False,newReplayDownloaded=False,
        currentDemoFrames=2264,currentDemoAssertions=7,currentDemoJournalRows=len(demo['rows']),currentDemoCapturedImages=len(demo['captures']),
        currentDemoImagesAndRowsPreserved=True,currentDemoPcmFrames=1508352,currentDemoPcmHashPreserved=True,
        currentDemoFrame2264NativeBytesEqual=1228800,productionGameplayChanged=True,productionGraphicsChanged=False,
        sourceAndOldFailuresRetained=True,preview8218StillPreviousPublishedCode=True,originalOrdinaryUiAccepted=False,
        completeGame=False,nativeEquivalent=False,browserAcceptance=False,
        previousPublishedCommit='6ac61159f627700c64c9a79fdef4b7530d399ad4',previousPublishedGameSessionSha256=SHA(old_source),
        verifierSha256=SHA(Path(__file__).read_bytes()),bindings=bindings)
    if args.check:assert json.loads(args.output.read_bytes())==result
    else:args.output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items()if k!='bindings'}),flush=True)


if __name__=='__main__':main()
