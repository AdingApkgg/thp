"""Check the bounded production Application workflow and fresh-process files.

This is component integration evidence, not browser or original ordinary UI
acceptance. Recomputes file hashes and the scenario assertions from the journal.
"""
import argparse
import hashlib
import json
from pathlib import Path
import struct

ROOT=Path(__file__).resolve().parents[1]
SHA=lambda raw:hashlib.sha256(raw).hexdigest()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--home',type=Path,default=ROOT/'artifacts/th14/native-application-final-oct26')
    parser.add_argument('--output',type=Path,default=ROOT/'docs/porting/th14-native-application-verified-oct26.json')
    parser.add_argument('--check',action='store_true')
    args=parser.parse_args();home=args.home.resolve(strict=True);bindings={}
    def read(path):
        raw=path.read_bytes();bindings[path.relative_to(ROOT).as_posix()]=dict(bytes=len(raw),sha256=SHA(raw));return raw
    def load(path):return json.loads(read(path))
    build_home=home/'build-final';build=load(build_home/'build.json')
    assert build['compiled']and build['productionSourceFilesUnmodified']and not build['productionChanged']
    assert build['toolSha256']==SHA(read(build_home/'build-tool.py'))==SHA(read(ROOT/'tools/th14-build-native-application.py'))
    assert build['wasmSha256']==SHA(read(build_home/'application.wasm'))
    assert build['glSignaturesSha256']==SHA(read(build_home/'gl-signatures.json'))
    for path,row in build['sourceBindings'].items():
        raw=read(ROOT/path);assert len(raw)==row['bytes']and SHA(raw)==row['sha256'],path
    assert len(build['coreObjects'])==141
    for row in build['coreObjects']:assert SHA(read(Path(row['path'])))==row['sha256']
    assert set(build['exports'])==set(['component_initialize','component_tick','component_state','component_pixels','component_audio_close','th11_error','th11_last_resource','malloc','free'])
    runs=[]
    for directory,scenario_name,frames,checks in [('workflow-final','save-replay',1286,218),('reload-final','reload-replay',722,21)]:
        folder=home/directory;run=load(folder/'report.json')
        scenario=load(ROOT/f'runtimes/th12/th12_web/tests/fixtures/th14-native-application-{scenario_name}.json')
        scenario_path=ROOT/f'runtimes/th12/th12_web/tests/fixtures/th14-native-application-{scenario_name}.json'
        assert run['scenarioSha256']==SHA(read(scenario_path))and run['wasmSha256']==build['wasmSha256']
        assert run['buildReportSha256']==SHA(read(build_home/'build.json'))
        assert run['toolSha256']==SHA(read(folder/'run-tool.py'))==SHA(read(ROOT/'tools/th14-native-application.py'))
        assert run['completed']and not run['error']and run['frames']==frames and len(run['checks'])==checks
        assert run['actualProductionApplicationAndDevices']and run['platformClockAndIoDeclared']
        assert run['physicalAudioDevicesOpened']==0 and run['virtualAudioStreamsCreated']==1 and run['pcmFrames']>0
        assert not any(run[k]for k in ['appUiControlled','browserRun','browserAcceptance','productionChanged','completeGame','nativeEquivalent'])
        assert len(run['actions'])==len(scenario['actions'])
        journal=[];frame=0
        for command,observed in zip(scenario['actions'],run['actions']):
            assert observed['atFrame']==frame
            for field in ['frames','held','pause']:assert observed[field]==command.get(field,0)
            frame+=observed['frames'];assert observed['endFrame']==frame and len(observed['state'])==20
            for index,expected in command.get('expect',{}).items():
                actual=observed['state'][int(index)];assert actual==expected
                journal.append(dict(frame=frame,index=int(index),expected=expected,actual=actual,passed=True))
        assert frame==frames and journal==run['checks']
        for capture in run['captures']:
            raw=read(folder/capture['file']);assert len(raw)==640*480*4 and SHA(raw)==capture['sha256']
        final={}
        for path in sorted((folder/'save').rglob('*')):
            if path.is_file():
                raw=read(path);final[path.relative_to(folder/'save').as_posix()]=dict(bytes=len(raw),sha256=SHA(raw))
        assert final==run['finalSave']
        state=run['actions'][-1]['state'];assert[state[i]for i in [0,1,2,6,11,12,13,14,15,19]]==[2,1,127,128,3,1,2,1,0,1]
        runs.append(run)
    workflow,reload=runs
    assert workflow['initialSave']=={}and reload['initialSave']==workflow['finalSave']==reload['finalSave']
    expected_files={'replay/th14_01.rpy':358,'scoreth14.dat':21635,'th14.cfg':92}
    assert{k:v['bytes']for k,v in workflow['finalSave'].items()}==expected_files
    codec=load(home/'native-files-final/report.json')
    assert codec['verifiedFiniteNativeCodecEvidence']and not codec['originalProcessLaunched']and codec['instructionBytesPatched']==0
    assert codec['toolSha256']==SHA(read(ROOT/'tools/th14-native-application-files.py'))
    assert codec['replay']['sha256']==workflow['finalSave']['replay/th14_01.rpy']['sha256']
    assert codec['score']['sha256']==workflow['finalSave']['scoreth14.dat']['sha256']
    assert all(codec['score'][key]for key in ['allEightRecordChecksumsValid','originalFullLoaderBytesEqual','originalFullWriterBytesEqual'])
    for name,row in [('replay',codec['replay']),('score',codec['score'])]:
        decoded=read(home/f'native-files-final/{name}-decoded.bin');assert len(decoded)==row['decodedBytes']and SHA(decoded)==row['decodedSha256']
    result=dict(verifiedFiniteApplicationIntegration=True,wasmSha256=build['wasmSha256'],coreWasmSha256=build['coreWasmSha256'],workflowFrames=workflow['frames'],reloadFrames=reload['frames'],scenarioAssertions=sum(len(run['checks'])for run in runs),captures=len(workflow['captures'])+len(reload['captures']),saveFiles=workflow['finalSave'],freshProcessSaveBytesUnchanged=True,nativeFileCodecs=codec,physicalAudioDevicesOpened=0,physicalInputMappingTested=False,normalizedInputOnly=True,declaredHostClockAndAsyncQueue=True,ordinaryOriginalMenuEquivalence=False,browserAcceptance=False,productionChanged=False,completeGame=False,nativeEquivalent=False,verifierSha256=SHA(Path(__file__).read_bytes()),bindings=bindings,scope='Real production C++ Application, renderer, font and audio devices, plus141 frozen game objects. Declared single-thread platform services, normalized inputs and virtual silent audio queue. Cold main/selection/stage/pause/resume/save/name/title/replay EOF and fresh-process reload in these bounded scenarios; original codecs independently check the produced files. No original cold-menu comparison, whole game, physical input/audio, browser/IndexedDB or full image equivalence. Reused game-source provenance belongs to the stated frozen core build, not every current workspace source.')
    output=args.output.resolve();assert output.is_relative_to(ROOT/'docs/porting')or output.is_relative_to(ROOT/'artifacts/th14')
    if args.check:assert json.loads(output.read_bytes())==result
    else:output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({key:result[key]for key in ['verifiedFiniteApplicationIntegration','workflowFrames','reloadFrames','scenarioAssertions','captures','freshProcessSaveBytesUnchanged','browserAcceptance']}))


if __name__=='__main__':main()
