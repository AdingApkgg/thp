"""Recompute native JS/WebGPU, async boundaries and browser-candidate evidence.

Preserves the native BGRA PNG color-control failure. No result here certifies
ordinary browser execution or complete-game fidelity.
"""
from pathlib import Path
import argparse
import hashlib
import json
import os
import struct
import subprocess
import sys
import zlib

ROOT=Path(__file__).resolve().parents[1]
SHA=lambda raw:hashlib.sha256(raw).hexdigest()


def png_rgba(raw):
    assert raw[:8]==b'\x89PNG\r\n\x1a\n'
    at=8;compressed=bytearray();dimensions=None
    while at<len(raw):
        size=struct.unpack_from('>I',raw,at)[0];kind=raw[at+4:at+8];data=raw[at+8:at+8+size]
        assert zlib.crc32(kind+data)&0xffffffff==struct.unpack_from('>I',raw,at+8+size)[0]
        if kind==b'IHDR':dimensions=struct.unpack('>2I5B',data)
        if kind==b'IDAT':compressed.extend(data)
        at+=12+size
    assert dimensions==(2,2,8,6,0,0,0)
    encoded=zlib.decompress(compressed);result=bytearray();prior=bytearray(8)
    assert len(encoded)==18
    for y in range(2):
        mode=encoded[y*9];row=bytearray(encoded[y*9+1:y*9+9]);assert mode<=4
        for x in range(8):
            left=row[x-4]if x>=4 else 0;up=prior[x];corner=prior[x-4]if x>=4 else 0
            if mode==1:prediction=left
            elif mode==2:prediction=up
            elif mode==3:prediction=(left+up)//2
            elif mode==4:
                value=left+up-corner;distances=[abs(value-left),abs(value-up),abs(value-corner)];prediction=[left,up,corner][distances.index(min(distances))]
            else:prediction=0
            row[x]=(row[x]+prediction)&255
        result.extend(row);prior=row
    return bytes(result)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--home',type=Path,required=True);parser.add_argument('--output',type=Path,required=True);parser.add_argument('--check',action='store_true')
    args=parser.parse_args();home=args.home.resolve(strict=True);bindings={}
    def read(path):
        raw=path.read_bytes();bindings[path.relative_to(ROOT).as_posix()]=dict(bytes=len(raw),sha256=SHA(raw));return raw
    def load(path):return json.loads(read(path))
    def checked_build(name):
        folder=home/name;build=load(folder/'build.json')
        assert build['actualCppRenderer']and build['asyncify']and not build['browserRun']
        assert build['toolSha256']==SHA(read(folder/'build-tool.py'))==SHA(read(ROOT/'tools/th14-build-webgpu-async-component.py'))
        for path,row in build['sourceBindings'].items():assert SHA(read(ROOT/path))==row['sha256'],path
        for path,row in build['sourceFiles'].items():assert SHA(read(folder/'src'/path))==row['sha256'],path
        assert SHA(read(folder/'component.wasm'))==build['wasmSha256']and SHA(read(folder/'component.mjs'))==build['loaderSha256']
        return build
    stage_build=checked_build('stage-build-verified');surface_build=checked_build('surface-build-verified');async_build=checked_build('async-build-current')
    stage=load(home/'stage-verified/report.json');surface=load(home/'surfaces-verified/report.json');asynchronous=load(home/'async-current/report.json')
    for run,name,tool,build in [(stage,'stage-build-verified','th14-webgpu-js-component.mjs',stage_build),(surface,'surface-build-verified','th14-webgpu-js-surfaces.mjs',surface_build),(asynchronous,'async-build-current','th14-webgpu-async-check.mjs',async_build)]:
        assert run['actualCppRenderer']and run['actualEmscriptenAsyncify']and run['actualJavascriptWebgpuHost']
        assert run['wasmSha256']==build['wasmSha256']and run['buildSha256']==SHA(read(home/name/'build.json'))
        assert run['toolSha256']==SHA(read(ROOT/'tools'/tool))
        assert not any(run[key]for key in ['browserRun','browserAcceptance','osWindowCreated','physicalAudioDevicesOpened','completeGame','nativeEquivalent'])
    native_home=ROOT/'artifacts/th14/stage-gpu-stream-replay';native=load(native_home/'native.json');native_pixels=read(native_home/'native.bgra')
    assert SHA(native_pixels)==native['pixelsSha256']==stage['nativePixelsSha256']
    assert stage['preparedSha256']==SHA(read(native_home/'prepared.json'))and stage['nativeReportSha256']==SHA(read(native_home/'native.json'))
    assert stage['frames']==stage['exactFrames']==len(stage['rows'])==21 and stage['differentBytes']==0
    stage_bytes=0
    for row in stage['rows']:
        original=next(n for n in native['frames']if(n['stage'],n['frame'])==(row['stage'],row['frame']))
        actual=read(home/f"stage-verified/stage{row['stage']}-frame{row['frame']}.bgra");expected=native_pixels[original['offset']:original['offset']+original['bytes']]
        assert actual==expected and SHA(actual)==row['actualSha256']==row['nativeSha256']==original['sha256'];stage_bytes+=len(actual)
    d3dx_home=ROOT/'artifacts/th14/deferred-capture-pixels-oct14';d3dx=load(d3dx_home/'native.json')
    assert surface['cases']==surface['exactCases']==len(surface['rows'])==8 and surface['differentBytes']==0
    assert surface['nativeReportSha256']==SHA(read(d3dx_home/'native.json'))and surface['inputsSha256']==SHA(read(d3dx_home/'inputs.json'))and surface['sourceSha256']==SHA(read(d3dx_home/'source.bgra'))
    capture_bytes=0
    for row,n in zip(surface['rows'],d3dx['cases']):
        actual=read(home/f"surfaces-verified/case-{row['index']}.pixels");expected=read(d3dx_home/n['pixelFile'])
        assert actual==expected and SHA(actual)==row['actualSha256']==row['nativeSha256']==n['pixelSha256'];capture_bytes+=len(actual)
    width=96;prefill=bytes.fromhex('a1b2c3d4')*(96*128);expected=bytearray(prefill)
    for left,top,right,bottom in [(3,7,49,61),(47,43,90,119)]:
        for y in range(top,bottom):expected[(y*width+left)*4:(y*width+right)*4]=(0xffa15127).to_bytes(4,'little')*(right-left)
    assert read(home/'surfaces-verified/partial-clear.bgra')==expected
    expected[(8*width+4)*4:(8*width+5)*4]=bytes.fromhex('225577ff');copied=bytearray(prefill)
    for y in range(43):copied[((19+y)*width+17)*4:((19+y)*width+52)*4]=expected[((8+y)*width+4)*4:((8+y)*width+39)*4]
    assert read(home/'surfaces-verified/version-copy.bgra')==copied
    assert all(asynchronous[key]for key in ['passed','actualGpuReadback','readWasSuspended','noCallbackReentryWhileSuspended','wasmMemoryGrewDuringRead','heapViewsReacquired','coreBindingIdempotent'])
    assert asynchronous['cppStackGuardWords']==2048 and asynchronous['growthBytes']==65536 and asynchronous['queuedKeyCalls']==1
    assert asynchronous['finalState']==[3,7,1,11,3,30,13,0,0,0,17,1]
    canvas=load(home/'canvas-verified/report.json');source=bytes(canvas['sourceBgra']);rgba=bytearray(source)
    for at in range(0,len(rgba),4):rgba[at],rgba[at+2]=rgba[at+2],rgba[at]
    canvas_results=[]
    for row in canvas['rows']:
        fmt=row['format'];gpu=read(home/f'canvas-verified/{fmt}.raw');png=read(home/f'canvas-verified/{fmt}.png');decoded=png_rgba(png)
        assert SHA(gpu)==row['gpuRawSha256']and SHA(png)==row['pngSha256']
        assert gpu==(source if fmt=='bgra8unorm'else rgba)
        canvas_results.append(dict(format=fmt,rawGpuBytesEqual=True,pngRgbaBytesEqual=decoded==rgba,pngDifferentBytes=sum(a!=b for a,b in zip(decoded,rgba))))
    assert canvas_results[0]['pngRgbaBytesEqual']is False and canvas_results[1]['pngRgbaBytesEqual']is True
    assert canvas['toolSha256']==SHA(read(ROOT/'tools/th14-webgpu-canvas-control.mjs'))
    for path,digest in canvas['sourceBindings'].items():assert SHA(read(ROOT/path))==digest
    application=load(home/'application-verified.json')
    for path,row in application['bindings'].items():assert SHA(read(ROOT/path))==row['sha256'],path
    assert application['verifiedFiniteApplicationIntegration']and application['scenarioAssertions']==239 and application['captures']==18
    paired_captures=0
    for name in ['workflow','reload']:
        a=load(home/(name+'-final')/'report.json');b=load(home/(name+'-gles')/'report.json')
        assert a['completed']and b['completed']and a['metadataEpochAtFrameZero']==b['metadataEpochAtFrameZero']==1792965600
        assert a['actions']==b['actions']and a['checks']==b['checks']and a['finalSave']==b['finalSave']and a['pcmFrames']==b['pcmFrames']and a['pcmSha256']==b['pcmSha256']
        for x,y in zip(a['captures'],b['captures']):assert x['label']==y['label']and read(home/(name+'-final')/x['file'])==read(home/(name+'-gles')/y['file']);paired_captures+=1
    assert paired_captures==18
    candidate=load(home/'browser-candidate-final/build.json');base=load(home/'browser-candidate-v2/build.json')
    assert candidate['compiled']and candidate['sourceUnits']==candidate['reusedObjectCount']==146 and candidate['compiledUnits']==0 and base['compiledUnits']==146
    assert candidate['reuseBuildReportSha256']==SHA(read(home/'browser-candidate-v2/build.json'))
    assert candidate['toolSha256']==SHA(read(home/'browser-candidate-final/build-tool.py'))==SHA(read(ROOT/'tools/th14-build-webgpu-release.py'))
    for path,row in candidate['sourceBindings'].items():assert SHA(read(home/'browser-candidate-final/source'/path))==row['sha256']
    for path in candidate['overlays']:assert SHA(read(ROOT/'runtimes/th12'/path))==candidate['sourceBindings'][path]['sha256']
    for path,digest in candidate['objectHashes'].items():
        filename=path.replace('/','_')+'.o';assert SHA(read(home/'browser-candidate-final/objects'/filename))==SHA(read(home/'browser-candidate-v2/objects'/filename))==digest==base['objectHashes'][path]
    package=load(home/'browser-runtime-final/package-report.json')
    assert package['prepared']and package['noDiagnosticGameControlExports']and not package['defaultPreviewChanged']and not package['browserAcceptance']
    assert package['buildSha256']==SHA(read(home/'browser-candidate-final/build.json'))
    assert candidate['wasmSha256']==package['wasmSha256']==SHA(read(home/'browser-runtime-final/th14-sdl.wasm'))
    assert package['toolSha256']==SHA(read(ROOT/'tools/th14-package-webgpu-candidate.py'))
    for path,row in package['sourceBindings'].items():assert SHA(read(ROOT/path))==row['sha256'],path
    alias_names={row['path']for row in package['generatedResourceAliases']}
    for path,row in package['files'].items():
        target=home/'browser-runtime-final'/path
        if path in alias_names:continue  # Hash-checked below without reading twice.
        raw=read(target);assert len(raw)==row['bytes']and SHA(raw)==row['sha256']
    for row in package['generatedResourceAliases']:
        target=home/'browser-runtime-final'/row['path'];original=ROOT/row['source']
        assert os.path.samefile(target,original)and target.stat().st_size==row['bytes']
        with target.open('rb')as stream:assert hashlib.file_digest(stream,'sha256').hexdigest()==row['sha256']
    result=dict(schema='th14/js-webgpu-verified/1',independentlyRecomputedFiniteEvidence=True,
        actualCppEmscriptenJavascriptWebgpuChain=True,nativeStageFrames=21,nativeStageComparedBytes=stage_bytes,nativeStageDifferentBytes=0,
        nativeD3dxCaptureCases=8,nativeD3dxComparedBytes=capture_bytes,nativeD3dxDifferentBytes=0,
        asyncStackGuardWords=2048,asyncMemoryGrowthBytes=65536,queuedCppCallbacks=6,queuedKeyArguments=[17,1],noObservedCallbackReentry=True,coreBindingIdempotent=True,
        nativeCanvasControls=canvas_results,nativeBgraPngFailureRetained=True,productionPresentationColorSwapAdded=False,
        applicationAssertions=239,pairedApplicationCaptures=18,pairedApplicationPcmAndFilesEqual=True,freshProcessFilesUnchanged=True,
        browserCandidateSourceUnits=146,browserCandidateWasmBytes=candidate['wasmBytes'],browserCandidateWasmSha256=candidate['wasmSha256'],browserCandidatePackaged=True,
        generatedResourceBytesAliased=package['generatedResourceBytesAliased'],originalRetailFilesLinked=False,defaultPreviewChanged=False,
        browserHostImplementationPresent=True,browserRun=False,browserAcceptance=False,physicalAudioDevicesOpened=0,completeGame=False,nativeEquivalent=False,
        checkerSha256=SHA(Path(__file__).read_bytes()),bindings=bindings,
        scope='Native Deno WebGPU API components and source-bound browser candidate compilation/packaging. Full finite Stage/D3DX buffers and async C++ boundary are checked. Production Application workflows use their declared native WASI platform. Native Canvas raw bytes are correct; BGRA PNG color control fails and is retained. No ordinary Chrome, compositor, physical input/audio, IndexedDB or complete-game acceptance.')
    output=args.output.resolve();assert output.is_relative_to(ROOT)
    if args.check:assert json.loads(output.read_bytes())==result
    else:assert not output.exists();output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({key:result[key]for key in ['nativeStageFrames','nativeD3dxCaptureCases','applicationAssertions','browserCandidatePackaged','nativeBgraPngFailureRetained','browserAcceptance']}))


if __name__=='__main__':main()
