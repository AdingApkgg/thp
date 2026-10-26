"""Verify the finite Launcher, owned-beam observation and Continue increment.

Native campaign gates are independently recomputed by the strict campaign
verifier. Here their bound receipts and the one changed observation are checked
alongside actual Application journals, paired images and local HTTP inventory.
"""
from pathlib import Path
import argparse
import gzip
import hashlib
import json
import struct

ROOT=Path(__file__).resolve().parents[1]
SHA=lambda raw:hashlib.sha256(raw).hexdigest()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--home',type=Path,required=True)
    parser.add_argument('--launcher',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--check',action='store_true')
    args=parser.parse_args();home=args.home.resolve();launcher=args.launcher.resolve();bindings={}
    assert home.is_relative_to(ROOT/'artifacts/th14')and launcher.is_relative_to(ROOT/'artifacts/th14')
    def read(path):
        raw=path.read_bytes();bindings[path.relative_to(ROOT).as_posix()]=dict(bytes=len(raw),sha256=SHA(raw));return raw
    def load(path):return json.loads(read(path))
    def hash_file(path):
        with path.open('rb')as stream:return hashlib.file_digest(stream,'sha256').hexdigest()
    routes=load(launcher/'launcher-report.json');transport=load(launcher/'transport.json')
    assert routes['schema']=='th14/webgpu-launcher-routes/1'and routes['prepared']and routes['candidateOnly']
    assert transport['verifiedTransport']and transport['reportSha256']==SHA(read(launcher/'launcher-report.json'))
    assert len(routes['files'])==transport['routes']==133 and len(transport['requests'])==21
    assert transport['quietByDefault']and not routes['payloadFilesCopied']and not routes['originalFilesLinked']
    assert routes['physicalBytesWritten']==103342 and routes['existingPayloadBytesReferenced']==510696322
    assert not routes['defaultPreviewChanged']and not routes['browserRun']and not routes['browserAcceptance']
    for name,row in routes['files'].items():
        path=(ROOT/row['path']).resolve(strict=True);assert path.is_relative_to(ROOT)
        assert path.stat().st_size==row['bytes']and hash_file(path)==row['sha256'],name
    for path,digest in transport['sourceBindings'].items():assert SHA(read(ROOT/path))==digest
    build=load(home/'beam-owned-field-observer-final/observer-build.json')
    assert build['wasmSha256']==hash_file(home/'beam-owned-field-observer-final/observer.wasm')
    assert build['engineObjectsReusedForThisLink']==141 and build['engineSourcesRecompiledForThisLink']==0
    assert build['unusedRendererHeaderProof']['absentFromAllCoreAndFixtureIncludeGraphs']
    assert SHA(read(Path(build['fixtureGraphRoot'])))==build['expandedFixtureSha256']
    assert not any(path.endswith('/portable/sdl/Renderer.hpp')for path in build['fixtureDependencyHashes'])
    for row in build['objectBindings']:assert hash_file(Path(row['path']))==row['sha256']
    old_home=ROOT/'artifacts/th14/stage-item-retirement-oct25/marisab-normal-kmk-full-oct26'
    new_home=home/'marisab-normal-kmk-owned-field-full'
    old=load(old_home/'combat-snapshots.json');new=load(new_home/'combat-snapshots.json')
    assert old['differences']==[dict(callback=2991,stage=1,stageFrame=2991,family='shots',row=14,field='collisionWidth',native=1113063424,portable=1111490560)]
    assert not old['allCapturedCombatWordsEqual']and new['allCapturedCombatWordsEqual']and not new['differences']
    for name in ['selected-state.u32','portable-camera.u32','portable-hud.u32']:
        assert read(old_home/name)==read(new_home/name),name
    for path in old_home.glob('portable-live-*.json'):assert read(path)==read(new_home/path.name)
    changes=[];combat_files=0
    for path in old_home.glob('combat-*.json'):
        if not path.stem.split('-')[-1].isdigit():continue
        before=load(path);after=load(new_home/path.name);combat_files+=1
        assert before.keys()==after.keys()
        assert {k:v for k,v in before.items()if k!='rows'}=={k:v for k,v in after.items()if k!='rows'}
        for family,rows in before['rows'].items():
            actual=after['rows'][family];assert len(rows)==len(actual)
            for index,(left,right)in enumerate(zip(rows,actual)):
                assert len(left)==len(right)
                for field,(a,b)in enumerate(zip(left,right)):
                    if a!=b:changes.append(dict(callback=before['callback'],family=family,row=index,field=field,before=a,after=b))
    assert combat_files==212 and changes==[dict(callback=2991,family='shots',row=14,field=15,before=1111490560,after=1113063424)]
    native=ROOT/'artifacts/th14/retail-marisab-normal-kmk-callback-hardware-oct26'
    snapshot=json.loads(gzip.decompress(read(native/'combat-pools/callback-002991.json.gz')))
    shot=snapshot['original']['shots'][14];raw=bytes.fromhex(shot['rawHex'])
    assert shot['slot']==244 and struct.unpack_from('<I',raw,0x98)[0]==2
    area_address=struct.unpack_from('<I',raw,0xc0)[0]
    area=next(row for row in snapshot['original']['areas']if row['address']==area_address)
    own_width=struct.unpack_from('<I',raw,0xb0)[0];area_width=struct.unpack_from('<I',bytes.fromhex(area['rawHex']),0x24)[0]
    assert(own_width,area_width)==(1113063424,1111490560)
    gates=['allSelected32Equal','allCamera25Equal','allHud2Equal','allVm303AndRegistryOrderEqual','allCapturedCombatWordsEqual']
    native_cases=[]
    for name,count,stages in [('marisab-normal-kmk',19496,[1,2]),('marisab-easy',107233,[1,2,3,4,5,6])]:
        receipt=load(home/(name+'-owned-field-verified.json'))
        assert receipt['verifiedFiniteEvidence']and receipt['callbacks']==count and receipt['stagesObserved']==stages
        assert all(receipt[key]for key in gates)and receipt['wasmSha256']==build['wasmSha256']
        for path,row in receipt['bindings'].items():assert hash_file(ROOT/path)==row['sha256'],path
        native_cases.append(dict(case=name,callbacks=count,stagesObserved=stages,vm303Rows=receipt['vm303Rows'],combatCheckpoints=receipt['combatCheckpoints'],strictFiniteGates=True))
    scenario_path=ROOT/'runtimes/th12/th12_web/tests/fixtures/th14-native-application-continue.json'
    scenario=load(scenario_path);runs=[]
    for backend in ['webgpu','gles']:
        folder=home/('application-continue-'+backend);run=load(folder/'report.json')
        assert run['completed']and not run['error']and run['frames']==3637 and run['backend']==backend
        assert run['scenarioSha256']==SHA(read(scenario_path))and run['metadataEpochAtFrameZero']==1792965600
        assert run['actualProductionApplicationAndDevices']and run['physicalAudioDevicesOpened']==0
        # Verify the frozen runner that actually produced this run. Later
        # budget/scenario changes neither inherit the run nor change its bytes.
        assert run['toolSha256']==SHA(read(folder/'run-tool.py'))
        assert not run['browserRun']and not run['appUiControlled']and run['initialSave']==run['finalSave']=={}
        assert len(run['actions'])==len(scenario['actions'])==22
        expected_checks=[];last=0
        for command,action in zip(scenario['actions'],run['actions']):
            assert action['atFrame']==last and action['held']==command.get('held',0)and action['pause']==command.get('pause',0)
            elapsed=action['endFrame']-last;assert 0<=elapsed<=command.get('frames',0)
            if 'until'in command:
                assert action['until']==command['until']and action['state'][command['until']['index']]==command['until']['equals']
            else:assert elapsed==command.get('frames',0)
            for field,wanted in command.get('expect',{}).items():
                actual=action['state'][int(field)];assert actual==wanted
                expected_checks.append(dict(frame=action['endFrame'],index=int(field),expected=wanted,actual=actual,passed=True))
            last=action['endFrame']
        assert expected_checks==run['checks']and len(expected_checks)==58 and last==3637
        dead,choices,pressed,resumed,playing=run['actions'][-5:]
        assert dead['endFrame']==3472 and dead['state'][0]==3 and dead['state'][7]==0xffffffff
        assert choices['state'][11:13]==[14,0]and pressed['state'][11]==19
        assert resumed['state'][0]==1 and resumed['state'][7:11]==[2,400,0,1]and resumed['state'][18]==1
        assert resumed['state'][6]>dead['state'][6]and resumed['state'][6]-dead['state'][6]<30
        assert playing['state'][6]==resumed['state'][6]+120 and playing['state'][10]==1
        assert run['pcmFrames']==2515968 and run['pendingAsyncCallbacks']==0 and len(run['captures'])==4
        for capture in run['captures']:
            raw=read(folder/capture['file']);assert len(raw)==640*480*4 and SHA(raw)==capture['sha256']
        runs.append(run)
    assert runs[0]['toolSha256']==runs[1]['toolSha256']
    assert runs[0]['rows']==runs[1]['rows']and runs[0]['actions']==runs[1]['actions']
    assert runs[0]['captures']==runs[1]['captures']and runs[0]['pcmSha256']==runs[1]['pcmSha256']
    for capture in runs[0]['captures']:
        assert read(home/'application-continue-webgpu'/capture['file'])==read(home/'application-continue-gles'/capture['file'])
    result=dict(verifiedFiniteIncrement=True,launcher=dict(routes=133,httpChecks=21,metadataBytesWritten=103342,
        existingPayloadBytesReferenced=510696322,quietByDefault=True,browserAcceptance=False),
        beamObservation=dict(productionGameplayChanged=False,ownedShotWidth=54,reusedAreaWidth=48,changedObservedWords=1,
            strictCases=native_cases,wasmSha256=build['wasmSha256'],engineObjectsUnchanged=141),
        applicationContinue=dict(framesPerBackend=3637,assertionsPerBackend=58,pairedJournalRows=len(runs[0]['rows']),
            frozenRunnerSha256=runs[0]['toolSha256'],laterRunnerVersionsNotAcceptedByInheritance=True,
            naturalGameOverFrame=3472,restoredFrame=3517,pairedImages=4,comparedImageBytes=4*640*480*4,
            reportedPairedPcmHashEqual=True,pcmFramesPerBackend=2515968,noGameplayOverrides=True,
            originalOrdinaryMenuEquivalence=False,physicalAudioDevicesOpened=0,browserAcceptance=False),
        verifierSha256=SHA(Path(__file__).read_bytes()),bindings=bindings,
        completeGame=False,nativeEquivalent=False,browserAcceptance=False,
        scope='Local HTTP packaging and contract transport; correction of the owned shot field in the diagnostic observer; strict finite campaign receipts; real C++ Application natural death/Continue with declared platform clock, normalized keys and silent stream. New Normal input still ends in Stage2; no six-stage clear or new whole-mode acceptance. Paired PCM hashes are from the actual host sinks, not independently retained raw PCM or original-device audio.')
    output=args.output.resolve();assert output.is_relative_to(ROOT/'docs/porting')or output.is_relative_to(ROOT/'artifacts/th14')
    if args.check:assert json.loads(output.read_bytes())==result
    else:output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({key:result[key]for key in ['verifiedFiniteIncrement','launcher','beamObservation','applicationContinue','completeGame']}))


if __name__=='__main__':main()
