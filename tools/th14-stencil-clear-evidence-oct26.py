"""Recheck finite HAL/CPP/JS/native-host stencil-clear buffers and regressions."""
from pathlib import Path
import argparse
import hashlib
import itertools
import json
import struct

ROOT=Path(__file__).resolve().parents[1]
SHA=lambda raw:hashlib.sha256(raw).hexdigest()


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path,required=True);parser.add_argument('--check',action='store_true')
    args=parser.parse_args();bindings={}
    def read(path):
        raw=path.read_bytes();bindings[path.relative_to(ROOT).as_posix()]=dict(bytes=len(raw),sha256=SHA(raw));return raw
    def load(path):return json.loads(read(path))
    def home(suffix):return ROOT/'artifacts/th14'/('stencil-clear-oct26-'+suffix)
    hal=load(home('hal-reference')/'report.json');js=load(home('js-verified')/'report.json');native=load(home('native-verified')/'report.json')
    assert hal['caseCount']==js['caseCount']==native['caseCount']==96
    assert hal['actualD3d9Hal']and hal['allIndependentCpuExpectationsEqual']and not hal['originalGameProcess']
    assert hal['toolSha256']==SHA(read(ROOT/'tools/th14-stencil-clear-hal-control.py'))
    assert js['actualCppRenderer']and js['actualEmscriptenAsyncify']and js['actualJavascriptWebgpuHost']and not js['negativeOnly']
    assert js['toolSha256']==SHA(read(ROOT/'tools/th14-webgpu-stencil-clear-control.mjs'))
    assert native['toolSha256']==SHA(read(ROOT/'tools/th14-stencil-clear-native-webgpu-control.py'))
    assert native['contextSha256']==SHA(read(ROOT/'tools/th14-native-webgpu-context.py'))
    assert js['halReportSha256']==native['halReportSha256']==SHA(read(home('hal-reference')/'report.json'))
    assert native['invalidDepthFormatsRejected']==[0,3,4]
    for run in[js,native]:
        assert run['comparedBuffers']==384 and run['comparedBytes']==4718592 and run['differentBytes']==0
        assert not run['browserRun']and not run['browserAcceptance']and run['physicalAudioDevicesOpened']==0
    rectangles=[[[3,7,41,35]],[[2,3,30,23],[19,17,61,46]],[[0,0,64,1],[0,1,1,48],[63,0,64,48],[0,47,64,48]]]
    specs=list(itertools.product([4,5,6,7],[0,1,127,128,255,256,0x12345678,0xffffffff],rectangles));compared=0
    for index,(flags,stencil,rects)in enumerate(specs):
        row=hal['cases'][index];assert(row['index'],row['flags'],row['stencil'],row['rectangles'])==(index,flags,stencil,rects)
        mask=lambda x,y:any(left<=x<right and top<=y<bottom for left,top,right,bottom in rects)
        expected={label:bytearray()for label in['color','new-stencil','old-stencil','depth']}
        for y in range(48):
            for x in range(64):
                inside=mask(x,y);stored=stencil&255 if inside else 17
                values=[0x7fa15327 if inside and flags&1 else 0x7fb13257,
                    0xffffffff if stored==(stencil&255)else 0xff010203,
                    0xffffffff if stored==17 else 0xff010203,
                    0xffffffff if inside and flags&2 else 0xff030507]
                for label,value in zip(expected,values):expected[label].extend(struct.pack('<I',value))
        for label,wanted in expected.items():
            reference=read(home('hal-reference')/row['buffers'][label]['file'])
            assert reference==wanted and SHA(reference)==row['buffers'][label]['sha256']
            for suffix,run in[('js-verified',js),('native-verified',native)]:
                actual=read(home(suffix)/f'case-{index:03d}-{label}.bgra')
                record=next(c for c in run['rows'][index]['comparisons']if c['label']==label)
                assert actual==reference and record['sha256']==record['halSha256']==SHA(actual)and record['differentBytes']==0
            compared+=len(reference)
    builds={}
    for name in['cpp-baseline-build','cpp-final-build','stage-build','surfaces-build']:
        folder=home(name);build=load(folder/'build.json');builds[name]=build
        assert build['actualCppRenderer']and build['asyncify']and not build['browserRun']
        assert build['wasmSha256']==SHA(read(folder/'component.wasm'))and build['loaderSha256']==SHA(read(folder/'component.mjs'))
        for path,row in build['sourceFiles'].items():assert SHA(read(folder/'src'/path))==row['sha256']
        if name!='cpp-baseline-build':
            for path,row in build['sourceBindings'].items():assert SHA(read(ROOT/path))==row['sha256'],path
    before,after=builds['cpp-baseline-build'],builds['cpp-final-build']
    assert before['wasmSha256']==after['wasmSha256']==js['wasmSha256']
    changed=[path for path in before['sourceBindings']if before['sourceBindings'][path]!=after['sourceBindings'][path]]
    assert changed==['runtimes/th12/portable/sdl/Th14WebGpuHost.mjs']
    baseline=load(home('js-baseline')/'report.json')
    assert baseline['negativeOnly']and baseline['caseCount']==0 and'Partial stencil clear is not implemented'in baseline['rejected']
    assert baseline['toolSha256']==SHA(read(home('js-baseline')/'run-tool-reconstructed.mjs'))
    assert baseline['buildSha256']==SHA(read(home('cpp-baseline-build')/'build.json'))
    assert js['buildSha256']==SHA(read(home('cpp-final-build')/'build.json'))
    stage=load(home('stage-regression')/'report.json');surfaces=load(home('surfaces-regression')/'report.json')
    assert stage['frames']==stage['exactFrames']==21 and surfaces['cases']==surfaces['exactCases']==8
    original=read(ROOT/'artifacts/th14/stage-gpu-stream-replay/native.bgra');stage_bytes=0
    for index,row in enumerate(stage['rows']):
        actual=read(home('stage-regression')/f"stage{row['stage']}-frame{row['frame']}.bgra")
        assert actual==original[index*1228800:(index+1)*1228800]and row['differentBytes']==0;stage_bytes+=len(actual)
    surface_bytes=0;original_surfaces=load(ROOT/'artifacts/th14/deferred-capture-pixels-oct14/native.json')
    for row,ref in zip(surfaces['rows'],original_surfaces['cases']):
        actual=read(home('surfaces-regression')/f"case-{row['index']}.pixels");expected=read(ROOT/'artifacts/th14/deferred-capture-pixels-oct14'/ref['pixelFile'])
        assert actual==expected and row['differentBytes']==0;surface_bytes+=len(actual)
    assert stage_bytes==25804800 and surface_bytes==5242880
    assert surfaces['rectangleControls']['exact']and surfaces['rectangleControls']['cpuVersionInvalidation']
    result=dict(verifiedFiniteStencilClearIncrement=True,halCases=96,cppJsCases=96,nativeHostCases=96,pairedBuffersPerHost=384,
        comparedBytesPerHost=compared,allHalAndBothHostBytesEqual=True,allIndependentCpuExpectationsEqual=True,
        partialStencilClearImplemented=True,colorDepthStencilIsolationChecked=True,stencilLow8BitControls=True,invalidNativeDepthFormatsRejected=3,
        cppWasmBeforeAfterByteIdentical=True,onlyCppBuildSourceChange='JavaScript WebGPU host',retainedBaselineRejectedPartialStencil=True,
        baselineTestSourceReconstructedAndHashMatched=True,baselineTestSourceFrozenAtStart=False,
        stageRegressionFrames=21,stageRegressionBytes=stage_bytes,d3dxRegressionCases=8,d3dxRegressionBytes=surface_bytes,
        partialColorCpuVersionAndCopyRegression=True,productionJavascriptHostChanged=True,nativePythonHostChanged=True,
        productionGameEngineChanged=False,productionGameplayOrAudioChanged=False,packedRasterTargetsStillRejected=True,
        currentBrowserPackageUpdated=False,ordinaryBrowserAcceptance=False,browserAcceptance=False,completeGame=False,nativeEquivalent=False,
        verifierSha256=SHA(Path(__file__).read_bytes()),bindings=bindings,
        scope='Finite actual D3D9 HAL color/stencil/depth controls and actual CPP/Asyncify/JS native-device path, plus a separate native Python GPU host. All retained outputs and independent CPU expectations rechecked. Current21 Stage/8 D3DX controls regress exactly. No original full-game, complete raster-format, browser/IndexedDB, physical input/audio or whole-game acceptance.')
    output=args.output.resolve();assert output.is_relative_to(ROOT/'artifacts/th14')or output.is_relative_to(ROOT/'docs/porting')
    if args.check:assert json.loads(output.read_bytes())==result
    else:output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({key:result[key]for key in['verifiedFiniteStencilClearIncrement','halCases','pairedBuffersPerHost','comparedBytesPerHost','stageRegressionFrames','d3dxRegressionCases','browserAcceptance']}))


if __name__=='__main__':main()
