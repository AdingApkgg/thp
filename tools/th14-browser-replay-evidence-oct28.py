"""Bind a finite, ordinary browser save/reload/playback case to its exact files."""
from pathlib import Path
import argparse,hashlib,importlib.util,json,subprocess
R=Path(__file__).resolve().parents[1]
SHA=lambda raw:hashlib.sha256(raw).hexdigest()

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--check',action='store_true')
    p.add_argument('--output',type=Path,default=R/'docs/porting/th14-browser-replay-observed-oct28.json')
    a=p.parse_args();bindings={}
    def read(path):
        raw=path.read_bytes();bindings[path.relative_to(R).as_posix()]=dict(bytes=len(raw),sha256=SHA(raw));return raw
    def load(path):return json.loads(read(path))
    H=R/'artifacts/th14/native-frame-readback-oct28';U=H/'browser-replay';B=H/'worker-runtime-delivery-v2/browser-candidate'
    build=load(B/'build.json');assert build['compiled'] and build['backgroundArchiveIntegration']
    assert SHA(read(B/'th14-sdl.wasm'))==build['wasmSha256']=='f9e4d7c37b761492f1a05af9813b80ec6314c18e44d5cdbd3fdb9d0a7bce2089'
    commit='185e53982fb317b4ea31a8955781f9510bc48abb';courier=R/'tools/tmp/github-source-release'
    for name in ['th12_web/cpp/game/Replay.cpp','th12_web/cpp/game/ResourceCrypt.cpp','th12_web/cpp/game/Lzss.cpp',
                 'th12_web/cpp/game/GameResources.cpp','th12_web/cpp/sdl/Application.cpp']:
        frozen=read(B/'source'/name);assert SHA(frozen)==build['sourceBindings'][name]['sha256']
        assert frozen==subprocess.check_output(['git','-C',str(courier),'show',commit+':runtimes/th12/'+name])
    first=read(U/'downloaded-th14_01.rpy');after=read(U/'after-playback-th14_01.rpy')
    assert first==after and len(first)==823 and SHA(first)=='75d5212f15433d6a09296d23602942c2dfd7966cb80df9723b55a9848b5edce9'
    immutable=load(U/'immutable-after-playback.json');assert immutable['passed'] and immutable['fullEncodedBytesUnchangedAfterTwoPlaybacks']
    native=load(U/'native-codec/report.json');production=load(U/'production-codec/report.json')
    assert native['passed'] and production['passed'] and production['exitCode']==0
    assert native['inputSha256']==production['inputSha256']==SHA(first)
    decoded=read(U/'native-codec/decoded.bin');assert decoded==read(U/'production-codec/decoded.bin')
    assert len(decoded)==4694 and SHA(decoded)==native['decodedSha256']==production['decodedSha256']
    assert native['actualRetailInstructionBodies'] and native['controlledCrtBoundaries'] and native['freshZeroDictionary']
    assert native['allDecodedBytesEqualIndependentPythonMirror'] and production['allDecodedBytesEqualRetailComponent']
    assert production['sourceAndHeaderHashesEqualCurrentBrowser'] and len(production['objectBindings'])==3
    assert native['nameHex']=='4120202020202020' and [native[k] for k in ['stageCount','character','subtype','difficulty']]==[1,0,0,1]
    assert native['stages'][0]['stage']==1 and native['stages'][0]['frames']==717
    assert native['trailingBytes']==0 and not native['nativeFilesystemOrPlaybackAcceptance']
    for row in production['objectBindings']:assert SHA(read(Path(row['path'])))==row['sha256']
    assert SHA(read(U/'production-codec/reader.wasm'))==production['wasmSha256']
    assert SHA(read(U/'production-codec/fixture.cpp'))==production['fixtureSha256']
    assert SHA(read(R/'tools/th14-replay-file-production-oct28.py'))==production['toolSha256']
    assert SHA(read(R/'tools/th14-replay-file-native-codec-oct28.py'))==native['toolSha256']
    image_tool=R/'tools/th14-browser-startup-evidence-oct28.py';read(image_tool)
    spec=importlib.util.spec_from_file_location('replay_jpeg',image_tool);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    pictures=[]
    for name in ['pause-before-save','save-slot-list','save-name-end','saved-slot-01','returned-title','normal-quit-launcher',
                 'after-reload-manager','after-reload-game-replay-list','after-reload-stage-selection',
                 'playback-natural-end','replay-again-running','replay-again-natural-end','after-playback-manager']:
        raw=read(U/(name+'.jpg'));width,height=module.jpeg_dimensions(raw);assert width>=640 and height>=480
        pictures.append(dict(label=name,width=width,height=height,sha256=SHA(raw)))
    for name in ['after-reload-manager-ax.txt','after-playback-manager-ax.txt']:
        text=read(U/name).decode();assert 'th14_01.rpy' in text and '1 个文件' in text and '127.0.0.1:8234/' in text
    for name in ['after-reload-game-replay-list-ax.txt','playback-natural-end-ax.txt','replay-again-running-ax.txt','replay-again-natural-end-ax.txt']:
        text=read(U/name).decode();assert 'runtimeEpoch=2' in text and '本机测试静音' in text and 'WebGPU / C++' in text
    logs=load(U/'runtime-replay-console.json')
    assert any(row['message']=='[replay] selected: record stage 1, character 0 subtype 0 difficulty 1, 823 bytes' for row in logs)
    result=dict(verifiedFiniteBrowserReplayCase=True,gameSourceCommit=commit,browserWasmSha256=build['wasmSha256'],
        ordinaryGameSave=True,emptySlotSelected=1,topLevelPageReloadObserved=True,launcherDownloadAfterReload=True,
        gameReplayMenuRediscoveredFile=True,ordinaryPlaybackNaturalEndObserved=True,replayAgainNaturalEndObserved=True,
        recordedInputFrames=717,stage=1,character='Reimu A',difficulty='Normal',name='A',
        fileBytes=823,fileSha256=SHA(first),decodedBytes=4694,decodedSha256=SHA(decoded),
        fullEncodedFileUnchangedAfterBothPlaybacks=True,productionAndRetailComponentDecodedBytesEqual=True,
        manuallyObservedBothTerminalHuds=dict(displayedScore=3100,lives=1,power='1.03',graze=2),
        hudEvidenceMethod='Manual observation of full browser screenshots; no pixel-equality or hidden state claim.',
        uiPictures=pictures,quietByDefault=True,ordinaryKeyboardMenusOnly=True,
        nativeOrdinaryReplayAcceptance=False,allModesOrMultiStageBrowserReplayAccepted=False,
        completeBrowserAcceptance=False,completeGame=False,nativeEquivalent=False,
        verifierSha256=SHA(Path(__file__).read_bytes()),bindings=bindings)
    if a.check:assert json.loads(a.output.read_bytes())==result
    else:a.output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k not in ['bindings','uiPictures']}))
if __name__=='__main__':main()
