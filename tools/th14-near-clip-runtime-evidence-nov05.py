"""Qualify the renderer's separate WebGPU, semantic, browser-build and App runs.

Exports metadata only. Original full-game pixels/audio and browser UI remain
outside these finite component and standalone Application checks.
"""
from pathlib import Path
import argparse,hashlib,json
R=Path(__file__).resolve().parents[1];H=R/'artifacts/th14/gles-clip-portable-nov04';SHA=lambda b:hashlib.sha256(b).hexdigest()

def evidence():
    bindings={}
    def read(path):
        path=Path(path).resolve(strict=True);assert path.is_relative_to(R);raw=path.read_bytes();bindings[path.relative_to(R).as_posix()]=dict(bytes=len(raw),sha256=SHA(raw));return raw
    def load(path):return json.loads(read(path))
    gles=load(R/'docs/porting/th14-portable-near-clip-nov05.json');assert gles['productionFixVerifiedFiniteBuffers']and gles['frames']==85 and not gles['completeGame']
    webgpu=load(H/'webgpu-build-nov05/build.json');assert webgpu['backend']=='webgpu'and webgpu['originalRendererSourcesUnmodified'];assert SHA(read(H/'webgpu-build-nov05/probe.wasm'))==webgpu['wasmSha256']
    for path,row in webgpu['sourceBindings'].items():assert SHA(read(R/path))==row['sha256']
    webgpu_rows=[]
    for name,reference in [('retained21',R/'artifacts/th14/stage-gpu-stream-replay'),('near48',H/'generated-near-clip-matrix-nov05'),('order16',H/'generated-order-geometry-nov05')]:
        home=H/('webgpu-'+name+'-retry2-nov05');report=load(home/'comparison.json');native=load(reference/'native.json');raw_native=read(reference/'native.bgra');assert SHA(raw_native)==native['pixelsSha256']==report['nativePixelsSha256'];assert report['wasmSha256']==webgpu['wasmSha256']and report['actualProductionCppRenderer']and report['postclipFractionalViewport']and not report['browserAcceptance']
        rows=[];actual_hash=hashlib.sha256();wrong=0
        for row,original in zip(report['rows'],native['frames']):
            assert(row['stage'],row['frame'])==(original['stage'],original['frame']);raw=read(home/f"stage{row['stage']}-frame{row['frame']}.bgra");expected=raw_native[original['offset']:original['offset']+original['bytes']]
            assert len(raw)==len(expected)==640*480*4 and SHA(raw)==row['actualSha256']and SHA(expected)==row['originalSha256']==original['sha256'];count=sum(a!=b for a,b in zip(raw,expected));assert count==row['differentChannels'];wrong+=count;actual_hash.update(raw);rows.append(dict(stage=row['stage'],frame=row['frame'],differentChannelBytes=count,actualSha256=SHA(raw),referenceSha256=SHA(expected)))
        assert len(rows)==report['frames']==len(native['frames']) and wrong==report['differentChannels']==0 and actual_hash.hexdigest()==report['actualPixelsSha256']
        webgpu_rows.append(dict(case=name,frames=len(rows),comparedBytes=len(raw_native),differentChannelBytes=wrong,rows=rows))
    sandbox=load(H/'webgpu-isolated-retry1-nov05/process-end.json');assert sandbox['exitCode']==3221225477;read(H/'webgpu-isolated-retry1-nov05/process.log')
    retry=load(H/'webgpu-normal-process-checks-nov05/process-end.json');assert all(row['exitCode']==0 for row in retry['rows'])
    fallback_rows=[]
    for name,reference in [('retained21',R/'artifacts/th14/stage-gpu-stream-replay'),('near48',H/'generated-near-clip-matrix-nov05'),('order16',H/'generated-order-geometry-nov05')]:
        home=H/('no-ext-'+name+'-nov05');report=load(home/'comparison.json');native=load(reference/'native.json');expected=read(reference/'native.bgra');assert SHA(expected)==report['nativePixelsSha256']
        assert not report['clipControlEnabled'] and report['clipControlExtensionDeclinedForFallbackTest']and report['clipDepthMode']==0x935e
        assert report['wasmSha256']==gles['production'][0]['wasmSha256'] and not report['browserAcceptance'];actual_hash=hashlib.sha256();wrong=0
        for row,original in zip(report['rows'],native['frames']):
            raw=read(home/f"stage{row['stage']}-frame{row['frame']}.bgra");before=expected[original['offset']:original['offset']+original['bytes']];assert len(raw)==len(before)==1228800 and SHA(raw)==row['actualSha256']and SHA(before)==row['originalSha256']==original['sha256'];count=sum(a!=b for a,b in zip(raw,before));assert count==row['differentChannels'];wrong+=count;actual_hash.update(raw)
        assert len(report['rows'])==len(native['frames'])==report['frames']and wrong==report['differentChannels']==0 and actual_hash.hexdigest()==report['actualPixelsSha256']
        fallback_rows.append(dict(case=name,frames=report['frames'],differentChannelBytes=0,comparedBytes=len(expected),actualPixelsSha256=actual_hash.hexdigest(),nativePixelsSha256=SHA(expected)))
    semantic=load(H/'semantic-trace-replay-nov05/report.json');semantic_build=load(H/'semantic-trace-build-nov05/build.json');assert semantic['completed']and not semantic['error']and semantic['completeBufferBaselineExact']and semantic['baselineKind']=='independent-hal'and not semantic['actualApplicationBaselineExact']
    assert semantic['representedNativeDraws']==416 and semantic['actualSemanticBatches']==192 and semantic['actualClears']==7 and not semantic['firstDifferingTargets'];assert semantic['wasmSha256']==semantic_build['wasmSha256']==SHA(read(H/'semantic-trace-build-nov05/probe.wasm'))
    for path,row in semantic_build['sourceBindings'].items():assert SHA(read(R/path))==row['sha256']
    native_steps=load(R/'artifacts/th14/application-render-trace-oct27/hal-per-draw/draw-comparisons.json');expected={row['event']:row for row in native_steps['steps']};assert all(row['nativeHashEqual']and row['glesSha256']==row['nativeSha256']==expected[row['event']]['nativeSha256']for row in semantic['steps'])
    semantic_raw=read(H/'semantic-trace-replay-nov05/frame.bgra');hal_raw=read(R/'artifacts/th14/application-render-trace-oct27/production-viewport-final/frame.bgra');assert len(semantic_raw)==1228800 and semantic_raw==hal_raw
    browser=load(H/'browser-retry1-nov05/build.json');assert browser['compiled']and browser['compiledUnits']==146 and browser['reusedObjectCount']==0 and not browser['browserAcceptance']and not browser['retailAssetsIncluded']
    assert SHA(read(H/'browser-retry1-nov05/th14-sdl.wasm'))==browser['wasmSha256'];assert SHA(read(H/'browser-retry1-nov05/th14-sdl.mjs'))==browser['loaderSha256']
    for path,row in browser['sourceBindings'].items():assert SHA(read(H/'browser-retry1-nov05/source'/path))==row['sha256']
    for path,digest in browser['objectHashes'].items():assert SHA(read(H/'browser-retry1-nov05/objects'/(path.replace('/','_')+'.o')))==digest
    for name in ['Renderer.cpp','Renderer.hpp','Shaders.hpp','Th14RenderMath.hpp']:
        key='portable/sdl/'+name;assert browser['sourceBindings'][key]['sha256']==SHA(read(R/'runtimes/th12'/key))
    gles_browser=load(H/'browser-gles-nov05/build.json');assert gles_browser['backend']=='gles'and gles_browser['compiledUnits']==146 and gles_browser['reusedObjectCount']==0 and not gles_browser['backgroundArchiveIntegration']and not gles_browser['frameAndWorkerCallbacksSerialized']
    assert not gles_browser['browserAcceptance']and not gles_browser['retailAssetsIncluded'];assert SHA(read(H/'browser-gles-nov05/th14-sdl.wasm'))==gles_browser['wasmSha256']and SHA(read(H/'browser-gles-nov05/th14-sdl.mjs'))==gles_browser['loaderSha256']
    for path,row in gles_browser['sourceBindings'].items():assert SHA(read(H/'browser-gles-nov05/source'/path))==row['sha256']
    for path,digest in gles_browser['objectHashes'].items():assert SHA(read(H/'browser-gles-nov05/objects'/(path.replace('/','_')+'.o')))==digest
    for name in ['Renderer.cpp','Renderer.hpp','Shaders.hpp','Th14RenderMath.hpp']:
        key='portable/sdl/'+name;assert gles_browser['sourceBindings'][key]['sha256']==SHA(read(R/'runtimes/th12'/key))
    app_home=H/'application-full-nov05';app=load(app_home/'gles/report.json');before_home=R/'artifacts/th14/config-startup-fallback-nov04/full-flow';before=load(before_home/'gles/report.json');build=load(H/'application-build-v2-nov05/build.json');parent_build=load(R/'artifacts/th14/config-startup-fallback-nov04/build/build.json')
    assert load(app_home/'process-end.json')['exitCode']==0 and app['completed']and not app['error']and app['exitSaveCompleted']and app['exitSaveRequested']
    assert app['wasmSha256']==build['wasmSha256']==SHA(read(H/'application-build-v2-nov05/application.wasm')) and app['buildReportSha256']==SHA(read(H/'application-build-v2-nov05/build.json'))
    assert build['coreObjects']==parent_build['coreObjects']and build['coreObjectsReused']==141 and build['applicationObjectsRecompiled']==5
    for path,row in build['sourceBindings'].items():assert SHA(read(R/path))==row['sha256']
    for row in build['coreObjects']+build['applicationObjectBindings']:assert SHA(read(row['path']))==row['sha256']
    assert app['frames']==122780 and len(app['checks'])==53 and all(x['passed']for x in app['checks'])and app['physicalAudioDevicesOpened']==0
    assert app['actions'][-1]['state'][0]==4 and app['actions'][23]['state'][0:2]==[2,6]and app['actions'][23]['endFrame']==122562
    fields=['frames','checks','initialSave','finalSave','rows','actions','pendingAsyncCallbacks','deliveredCallbackSequence','files','pcmFrames','pcmSha256','applicationTicks','replayConstructionTransitions','replayCadenceObservations','finalReferenceState']
    differing=[name for name in fields if app[name]!=before[name]]
    images=[];animations=[]
    assert len(app['captures'])==len(before['captures'])==10
    for row,prior in zip(app['captures'],before['captures']):
        assert(row['label'],row['frame'])==(prior['label'],prior['frame']);a=read(app_home/'gles'/row['file']);b=read(before_home/'gles'/prior['file']);assert len(a)==len(b)==1228800 and SHA(a)==row['sha256']and SHA(b)==prior['sha256'];images.append(dict(label=row['label'],frame=row['frame'],differentBytes=sum(x!=y for x,y in zip(a,b)),newSha256=SHA(a),previousCppSha256=SHA(b)))
        live=load(app_home/'gles'/row['liveAnimations']['file']);old=load(before_home/'gles'/prior['liveAnimations']['file']);assert live['comparedValues']==old['comparedValues']==303;assert SHA(read(app_home/'gles'/row['liveAnimations']['file']))==row['liveAnimations']['sha256'];assert SHA(read(before_home/'gles'/prior['liveAnimations']['file']))==prior['liveAnimations']['sha256'];animations.append(dict(label=row['label'],rows=len(live['rows']),rowsAndRegistryOrderEqual=live['rows']==old['rows']))
    for name,row in app['finalSave'].items():assert SHA(read(app_home/'gles/save'/name))==row['sha256']
    assert app['initialSave']['replay/th14_01.rpy']==app['finalSave']['replay/th14_01.rpy']
    diagnostic=dict(differingPayloads=differing,images=images,animationSnapshots=animations)
    diagnostic_path=H/'runtime-comparison-diagnostic-nov05.json'
    if diagnostic_path.exists():assert json.loads(diagnostic_path.read_bytes())==diagnostic
    else:diagnostic_path.write_text(json.dumps(diagnostic,indent=2)+'\n')
    read(diagnostic_path)
    assert not differing and all(x['rowsAndRegistryOrderEqual']for x in animations),'Gameplay/VM comparison failed; diagnostic retained before acceptance'
    return dict(schema='th14/near-clip-runtime/1',finiteStandaloneRuntimeVerified=True,glesEvidenceSha256=SHA(read(R/'docs/porting/th14-portable-near-clip-nov05.json')),
        webgpu=dict(frames=85,comparedBytes=sum(x['comparedBytes']for x in webgpu_rows),differentChannelBytes=0,wasmSha256=webgpu['wasmSha256'],cases=webgpu_rows,regularProcessPermissionsRequiredForThisHost=True,sandboxInstanceAccessViolationRetained=True,sourceChangedForWebgpu=False),
        glesWithoutClipControl=dict(frames=85,comparedBytes=sum(x['comparedBytes']for x in fallback_rows),differentChannelBytes=0,cases=fallback_rows,optionalExtensionDeclinedOnSameAngleHost=True,physicalOtherDeviceAccepted=False),
        semanticTrace=dict(representedDraws=416,batches=192,clears=7,comparisonCheckpoints=len(semantic['steps']),allRecordedCheckpointHashesEqual=True,finalComparedBytes=1228800,finalDifferentBytes=0,initialColorsFromEarlierCppGpuTrace=True,originalWholeFramebufferReference=False),
        browserBuild=dict(webgpuCompiledUnits=146,webgpuWasmSha256=browser['wasmSha256'],glesCompiledUnits=146,glesWasmSha256=gles_browser['wasmSha256'],glesUsesOrdinarySdlCallbacks=True,glesWorkerCallbackSerializationAccepted=False,reusedUnits=0,retailAssetsIncluded=False,allFourProductionRendererBindingsVerified=True,firstFrozenHeaderBuildFailureRetained=True,browserUiAcceptance=False),
        application=dict(wasmSha256=app['wasmSha256'],frames=app['frames'],assertions=53,naturalEndFrame=122562,ordinaryQuitAndSavePassed=True,referenceIsSameCoreCppParent=True,comparedPayloads=fields,differingPayloads=differing,images=images,animationSnapshots=animations,silentPcmFrames=app['pcmFrames'],silentPcmSha256=app['pcmSha256'],physicalAudioDevicesOpened=0,replayBytesUnchanged=True,unchangedCoreObjects=141,recompiledApplicationUnits=5),
        originalWholePixelsOrPcmAccepted=False,independentSchedulingAccepted=False,browserAcceptance=False,otherGpusAccepted=False,allModesAccepted=False,completeGame=False,nativeEquivalent=False,publicEvidenceContainsOnlyCountersPathsHashes=True,bindings=bindings,verifierSha256=SHA(Path(__file__).read_bytes()))

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);p.add_argument('--check',action='store_true');a=p.parse_args();out=a.output.resolve();assert out.is_relative_to(R);value=evidence()
    if a.check:assert json.loads(out.read_bytes())==value
    else:assert not out.exists();out.write_text(json.dumps(value,indent=2)+'\n')
    print(json.dumps(dict(finiteRuntimeVerified=value['finiteStandaloneRuntimeVerified'],webgpuFrames=85,semanticDraws=416,browserCompiledUnits=146,applicationFrames=value['application']['frames'],imageDifferenceBytes=[x['differentBytes']for x in value['application']['images']],completeGame=False)))

if __name__=='__main__':main()
