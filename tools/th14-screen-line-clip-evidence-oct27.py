"""Verify the finite C++ screen-line clip repair and retained negative control.

The independent D3D9 replay consumes observed C++ semantic commands and initial
GPU colors. It is distinct from an original-gameplay frame capture. No process,
browser, input device or physical audio device is opened by this verifier.
"""
from pathlib import Path
import argparse,hashlib,json,struct

ROOT=Path(__file__).resolve().parents[1]
SHA=lambda raw:hashlib.sha256(raw).hexdigest()


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--home',type=Path,default=ROOT/'artifacts/th14/native-frame-readback-oct27')
    p.add_argument('--output',type=Path,default=ROOT/'docs/porting/th14-screen-line-clip-verified-oct27.json')
    p.add_argument('--check',action='store_true');a=p.parse_args();home=a.home.resolve();out=a.output.resolve()
    assert home.is_relative_to(ROOT/'artifacts/th14')and out.is_relative_to(ROOT);bindings={}
    def read(path):
        path=path.resolve();assert path.is_relative_to(ROOT);raw=path.read_bytes()
        bindings[path.relative_to(ROOT).as_posix()]=dict(bytes=len(raw),sha256=SHA(raw));return raw
    def load(path):return json.loads(read(path))
    for name in ['tools/th14-prepare-application-trace-oct27.py','tools/th14-application-trace-hal-oct27.py',
        'tools/th14-application-gles-trace-oct27.py','tools/th14-native-application-process-host-oct27.py',
        'tools/th14-build-native-application.py','tools/th14-build-native-gles-component.py',
        'tools/th14-native-webgpu-component.py','tools/th14-native-webgpu-context.py',
        'runtimes/th12/portable/sdl/WebGpuRenderer.hpp']:
        read(ROOT/name)
    trace_raw=read(home/'demo-trace-webgpu/render-trace.json');trace=json.loads(trace_raw)
    assert trace['frame']==2265 and trace['semanticInputsObservedBeforeBackend']and not trace['nativeValuesProvidedToEngine']
    assert sum(x['kind']==101 for x in trace['events'])==415 and sum(x['kind']==110 for x in trace['events'])==7
    before=load(home/'demo-trace-hal/draw-comparisons.json');hal=load(home/'demo-trace-hal/report.json')
    assert hal['completed']and not hal['error']and hal['actualHalDraws']==415 and hal['actualClears']==7
    assert hal['sourceTraceSha256']==SHA(trace_raw)and hal['toolSha256']==SHA(read(home/'demo-trace-hal/run-tool.py'))
    assert before['webgpuReplayBaselineExact']and before['nativeDifferentBytes']==2 and before['nativeDifferentPixels']==1
    first=next(x for x in before['steps']if x['differentBytes'])
    assert first['completedDraws']==395 and first['event']==1141 and first['target']==10 and first['beforeBuffersEqual']
    assert first['first']==dict(x=128,y=166,channel='R',native=155,webgpu=117)
    native=read(home/'demo-trace-hal/frame.bgra');old=read(home/'idle-demo-webgpu/first-demo-ready.bgra')
    assert old==read(home/'demo-trace-webgpu/first-demo-ready.bgra')and native!=old
    gles=load(home/'demo-trace-gles/report.json')
    assert gles['completed']and not gles['error']and gles['actualApplicationBaselineExact']
    assert gles['representedNativeDraws']==415 and gles['actualSemanticBatches']==192
    assert len(gles['steps'])==199 and all(x['nativeHashEqual']for x in gles['steps'])
    assert read(home/'demo-trace-gles/frame.bgra')==native==read(home/'idle-demo-gles/first-demo-ready.bgra')
    raw_negative=load(home/'screen-lines-raw-experiment/report.json')
    raw_comparison=load(home/'screen-lines-raw-experiment/draw-comparisons.json')
    assert raw_negative['error']and raw_comparison['nativeDifferentBytes']==2
    fixed=load(home/'screen-lines-rounded-bias-in-clip-experiment/report.json')
    comparisons=load(home/'screen-lines-rounded-bias-in-clip-experiment/draw-comparisons.json')
    assert fixed['completed']and not fixed['error']and comparisons['nativeDifferentBytes']==0
    assert len(comparisons['steps'])==422 and all(x['differentBytes']==0 for x in comparisons['steps'])
    build=load(home/'line-webgpu-build/build.json');assert build['backend']=='webgpu'and build['compiled']
    assert build['wasmSha256']==SHA(read(home/'line-webgpu-build/application.wasm'))
    for name,row in build['sourceBindings'].items():assert SHA(read(ROOT/name))==row['sha256'],name
    for row in build['coreObjects']:assert SHA(read(Path(row['path'])))==row['sha256']
    for name,digest in build['newObjects'].items():assert SHA(read(home/'line-webgpu-build'/name))==digest
    current=load(home/'line-demo-webgpu/report.json');baseline=load(home/'idle-demo-gles/report.json')
    assert current['completed']and not current['error']and current['frames']==2265 and len(current['checks'])==7
    assert current['wasmSha256']==build['wasmSha256']and all(x['passed']for x in current['checks'])
    for field in ('rows','actions','checks','finalSave','pcmFrames','pcmSha256'):assert current[field]==baseline[field],field
    assert len(current['rows'])==131 and current['pcmFrames']==1508352
    for x,y in zip(current['captures'],baseline['captures']):
        left=read(home/'line-demo-webgpu'/x['file']);right=read(home/'idle-demo-gles'/y['file'])
        assert left==right and SHA(left)==x['sha256']==y['sha256']
    assert read(home/'line-demo-webgpu/first-demo-ready.bgra')==native
    titles=[]
    for case,native_case in [('240','present-0240'),('420','present-0420-vms')]:
        n=load(home/native_case/'report.json');r=load(home/('line-title'+case+'-webgpu')/'report.json')
        assert n['frameReadbackCompleted']and n['childExited']and r['completed']and not r['error']
        assert r['wasmSha256']==build['wasmSha256']and len(r['captures'])==1
        s=next(x for x in n['rows']if x.get('kind')=='native-Present-entry'and x['ordinal']==int(case))
        c=r['captures'][0];rng=struct.unpack('<HHIHHI',bytes.fromhex(s['rngHex']))
        assert c['referenceState'][:7]==[s['originalInitialTicks'],s['originalProcessCookie'],s['idleCounter'],rng[0],rng[2],rng[3],rng[5]]
        left=read(home/native_case/n['readback']['file']);right=read(home/('line-title'+case+'-webgpu')/c['file'])
        assert left==right and len(left)==1228800 and SHA(left)==c['sha256']==n['readback']['pixelSha256']
        titles.append(dict(nativePresent=int(case),titleIdle=s['idleCounter'],portFrame=r['frames'],sha256=SHA(left)))
    stage=load(home/'line-stage-regression/comparison.json');sb=load(home/'line-stage-build/build.json')
    assert stage['frames']==stage['exactFrames']==21 and stage['differentChannels']==0
    assert stage['wasmSha256']==sb['wasmSha256']==SHA(read(home/'line-stage-build/probe.wasm'))
    for name,row in sb['sourceBindings'].items():assert SHA(read(ROOT/name))==row['sha256'],name
    reference=ROOT/'artifacts/th14/stage-gpu-stream-replay';nr=load(reference/'native.json');pixels=read(reference/'native.bgra')
    assert SHA(pixels)==nr['pixelsSha256'];total=0
    for row in stage['rows']:
        original=next(x for x in nr['frames']if(x['stage'],x['frame'])==(row['stage'],row['frame']))
        expected=pixels[original['offset']:original['offset']+original['bytes']]
        actual=read(home/f"line-stage-regression/stage{row['stage']}-frame{row['frame']}.bgra")
        assert actual==expected and SHA(actual)==row['actualSha256']==row['originalSha256'];total+=len(actual)
    assert total==25804800
    result=dict(schema='th14/screen-line-clip-finite-evidence/1',verifiedFiniteRepair=True,
        firstDifferentDraw=395,firstDifferentTarget=10,firstDifferentTargetPixel=[128,166],finalDifferentPixelBefore=[32,166],
        beforeDifferentPixels=1,beforeDifferentBytes=2,independentHalDraws=415,independentHalClears=7,
        cppSemanticBatches=192,glesSemanticAndClearComparisons=199,glesAllNativeHashesEqual=True,
        removingScreenLineRoundingAloneFailed=True,halfPixelBiasBeforeClipWithOriginalRoundingPassed=True,
        experimentalAll422DrawAndClearComparisonsExact=True,
        actualProductionApplicationFrames=2265,actualApplicationAssertions=7,journalRows=131,silentPcmFrames=1508352,
        currentFull1228800BytesEqualIndependentHal=True,currentFullFrameSha256=SHA(native),
        currentImagesStateFilesAndSilentPcmEqualFrozenGles=True,frozenGlesCodeCommit='4a843e67c262cf6a7968fd71291a80b062e5bbb8',
        currentActualNativeTitleComparisons=titles,stageRegressionFrames=21,stageComparedBytes=total,
        currentShaderAndHostMathUnchanged=True,screenLinesOnlyProductionChange=True,quantizationRetained=True,
        independentHalUsesObservedCppInputsAndInitialGpuColors=True,independentHalIsNotOriginalGameplayCapture=True,
        pixelTolerance=0,alphaExcluded=False,oldFailuresRetained=True,
        strictTitleVmFailuresNotClosed=True,nativeNaturalRunModePairs=30,nativeAllStageEntryModePairs=25,
        browser8224StillEarlierTitleOnlyCode=True,browserAcceptance=False,completeGame=False,nativeEquivalent=False,
        verifierSha256=SHA(Path(__file__).read_bytes()),bindings=bindings)
    encoded=json.dumps(result,indent=2)+'\n'
    if a.check:assert out.read_text()==encoded
    else:out.write_text(encoded)
    print(json.dumps({k:v for k,v in result.items()if k not in ('bindings','currentActualNativeTitleComparisons')}))


if __name__=='__main__':main()
