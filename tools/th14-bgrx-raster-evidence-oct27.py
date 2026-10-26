"""Verify full canonical A8/X8 buffers without dropping channels or raw evidence."""
from pathlib import Path
import argparse
import hashlib
import itertools
import json
import struct

ROOT=Path(__file__).resolve().parents[1]
SHA=lambda raw:hashlib.sha256(raw).hexdigest()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--home',type=Path,required=True);parser.add_argument('--output',type=Path,required=True);parser.add_argument('--check',action='store_true');args=parser.parse_args()
    home=args.home.resolve();assert home.is_relative_to(ROOT/'artifacts/th14');bindings={};digests={};counts={}
    def read(path,bind=True):
        raw=path.read_bytes()
        if bind:bindings[path.relative_to(ROOT).as_posix()]=dict(bytes=len(raw),sha256=SHA(raw))
        return raw
    def load(path):return json.loads(read(path))
    def buffer(dataset,path,expected_sha):
        raw=read(path,False);assert len(raw)==1024 and SHA(raw)==expected_sha
        digest=digests.setdefault(dataset,hashlib.sha256());digest.update(path.name.encode()+b'\0'+raw)
        counts[dataset]=counts.get(dataset,0)+1;return raw
    hal_home=home/'hal-canonical-reference';hal=load(hal_home/'report.json');js=load(home/'final/report.json');native=load(home/'native-verified/report.json')
    assert hal['actualD3d9Hal']and hal['actualD3dxFormatConversion']and hal['x8CanonicalAlphaAlwaysOpaque']
    assert hal['toolSha256']==SHA(read(hal_home/'run-tool.py'))==SHA(read(ROOT/'tools/th14-bgrx-raster-hal-control-oct27.py'))
    assert js['toolSha256']==SHA(read(home/'final/run-tool.mjs'))==SHA(read(ROOT/'tools/th14-webgpu-bgrx-raster-control-oct27.mjs'))
    assert native['toolSha256']==SHA(read(home/'native-verified/run-tool.py'))==SHA(read(ROOT/'tools/th14-native-webgpu-bgrx-control-oct27.py'))
    assert native['contextSha256']==SHA(read(home/'native-verified/context-tool.py'))==SHA(read(ROOT/'tools/th14-native-webgpu-context.py'))
    assert js['nativeReportSha256']==native['nativeReportSha256']==SHA(read(hal_home/'report.json'))
    assert not js['negativeOnly']and js['actualCppRenderer']and js['actualEmscriptenAsyncify']and js['actualJavascriptWebgpuHost']
    assert native['actualCppRenderer']and native['glesFallbackCalls']==0
    assert native['unexecutedGlesImportsBoundToRejectingTraps']and not any(native['gpuCalls'].get(name,0)for name in native['unexecutedGlesImportsBoundToRejectingTraps'])
    for run in[js,native]:
        assert run['caseCount']==1344 and run['comparedBuffers']==4032 and run['comparedBytes']==4128768 and not run['differentBytes']
        assert not run['browserRun']and not run['browserAcceptance']and run['physicalAudioDevicesOpened']==0
    blends=[('replace',2,1,1,False),('source-alpha',5,6,1,True),('destination-alpha',7,1,1,True),('inverse-destination-alpha',8,2,1,True),
        ('source-alpha-saturate',11,2,1,True),('add',2,2,1,True),('subtract',5,6,2,True),('reverse-subtract',5,6,3,True)]
    specs=list(itertools.product([21,22],[0,49,199,255],blends,[0,1,2,4,7,8,15],[0,127,255]));assert len(hal['cases'])==len(specs)==1344
    x8_upper={name:set()for name in['clear','first','chain']};opaque_chain_cases=0
    for index,(fmt,alpha,blend,mask,source_alpha)in enumerate(specs):
        row=hal['cases'][index];name,sb,db,op,enabled=blend
        assert(row['index'],row['format'],row['colorMask'],row['sourceColor'])==(index,fmt,mask,source_alpha<<24|0xc05329)
        assert(row['blendName'],row['sourceBlend'],row['destinationBlend'],row['blendOperation'],row['blendEnabled'])==blend
        assert row['clearColor']==alpha<<24|0x398db7 and row['partialColor']==(255-alpha)<<24|0x7124c3
        assert row['rectangles']==[[2,3,11,12],[8,9,15,16]]
        canonical={}
        for label,ref in row['buffers'].items():
            expected=buffer('halCanonical',hal_home/ref['file'],ref['sha256']);raw=buffer('halRaw',hal_home/ref['rawFile'],ref['rawSha256']);canonical[label]=expected
            if fmt==21:assert raw==expected
            else:
                assert all(expected[i]==255 for i in range(3,1024,4))
                assert all(raw[i:i+3]==expected[i:i+3]for i in range(0,1024,4));x8_upper[label].update(raw[3::4])
            for dataset,folder,run in[('cppJs','final',js),('nativeCpp','native-verified',native)]:
                actual_row=run['rows'][index];assert actual_row['format']==fmt and actual_row['index']==index
                record=next(item for item in actual_row['comparisons']if item['label']==label)
                assert record['bytes']==1024 and not record['differentBytes']and record['halSha256']==ref['sha256']
                assert buffer(dataset,home/folder/record['file'],record['sha256'])==expected
        clear_expected=bytearray();first_expected=bytearray();chain_expected=bytearray()
        for y in range(16):
            for x in range(16):
                color=row['partialColor']if any(l<=x<r and t<=y<b for l,t,r,b in row['rectangles'])else row['clearColor']
                if fmt==22:color|=0xff000000
                clear_expected.extend(struct.pack('<I',color))
                if not enabled:
                    current=bytearray(struct.pack('<I',color));source=struct.pack('<I',row['sourceColor'])
                    for bit,channel in[(1,2),(2,1),(4,0),(8,3)]:
                        if mask&bit and not(fmt==22 and bit==8):current[channel]=source[channel]
                    first_expected.extend(current)
                if fmt==22:
                    offset=(y*16+x)*4
                    chain_expected.extend(struct.pack('<I',0xff27a1d3)if 4<=x<14 and 5<=y<15 else canonical['first'][offset:offset+4])
        assert canonical['clear']==clear_expected
        if not enabled:assert canonical['first']==first_expected
        if fmt==22:assert canonical['chain']==chain_expected;opaque_chain_cases+=1
    assert {k:sorted(v)for k,v in x8_upper.items()}==hal['x8RawUpperByteValues']==dict(clear=[0],first=[0],chain=[0])
    builds={}
    for label in['baseline-build','final-build','stage-build','surfaces-build','stencil-build']:
        folder=home/label;build=load(folder/'build.json');builds[label]=build
        assert build['actualCppRenderer']and build['asyncify']and SHA(read(folder/'component.wasm'))==build['wasmSha256']
        assert SHA(read(folder/'component.mjs'))==build['loaderSha256']
        for file,record in build['sourceFiles'].items():assert SHA(read(folder/'src'/file))==record['sha256']
        if label!='baseline-build':
            for path,record in build['sourceBindings'].items():assert SHA(read(ROOT/path))==record['sha256'],path
    before,after=builds['baseline-build'],builds['final-build']
    assert before['wasmSha256']!=after['wasmSha256']==js['wasmSha256']
    assert[path for path in before['sourceBindings']if before['sourceBindings'][path]!=after['sourceBindings'][path]]==['runtimes/th12/portable/sdl/WebGpuRenderer.hpp']
    assert SHA(read(home/'final-build/build.json'))==js['buildSha256']
    nbuild=load(home/'native-build/build.json');assert nbuild['backend']=='webgpu'and nbuild['wasmSha256']==native['wasmSha256']==SHA(read(home/'native-build/probe.wasm'))
    assert native['buildSha256']==SHA(read(home/'native-build/build.json'))
    for path,record in nbuild['sourceBindings'].items():assert SHA(read(ROOT/path))==record['sha256']
    rejection=load(home/'baseline-rejected/report.json');assert rejection['negativeOnly']and rejection['caseCount']==0
    assert any('packed raster target unsupported'in line for line in rejection['errors'])and'Aborted'in rejection['rejection']
    assert rejection['toolSha256']==SHA(read(home/'baseline-rejected/run-tool.mjs'))and rejection['wasmSha256']==before['wasmSha256']
    stage=load(home/'stage-regression/report.json');surfaces=load(home/'surfaces-regression/report.json');stencil=load(home/'stencil-regression/report.json')
    assert stage['frames']==stage['exactFrames']==21 and surfaces['cases']==surfaces['exactCases']==8
    assert stage['buildSha256']==SHA(read(home/'stage-build/build.json'))and surfaces['buildSha256']==SHA(read(home/'surfaces-build/build.json'))
    stage_reference=ROOT/'artifacts/th14/stage-gpu-stream-replay';stage_native=load(stage_reference/'native.json')
    original=read(stage_reference/'native.bgra',False);stage_bytes=0
    assert SHA(original)==stage_native['pixelsSha256']==stage['nativePixelsSha256']
    assert stage['nativeReportSha256']==SHA(read(stage_reference/'native.json'))
    for i,row in enumerate(stage['rows']):
        actual=read(home/'stage-regression'/f"stage{row['stage']}-frame{row['frame']}.bgra",False);assert actual==original[i*1228800:(i+1)*1228800]and not row['differentBytes'];stage_bytes+=len(actual)
        assert SHA(actual)==row['actualSha256']==row['nativeSha256']
    refs=load(ROOT/'artifacts/th14/deferred-capture-pixels-oct14/native.json');surface_bytes=0
    for row,ref in zip(surfaces['rows'],refs['cases']):
        actual=read(home/'surfaces-regression'/f"case-{row['index']}.pixels",False);expected=read(ROOT/'artifacts/th14/deferred-capture-pixels-oct14'/ref['pixelFile'],False)
        assert actual==expected and not row['differentBytes'];surface_bytes+=len(actual)
        assert SHA(actual)==row['actualSha256']==row['nativeSha256']==ref['pixelSha256']
    assert surfaces['rectangleControls']['exact']and surfaces['rectangleControls']['cpuVersionInvalidation']
    stencil_reference=ROOT/'artifacts/th14/stencil-clear-oct26-hal-reference';stencil_hal=load(stencil_reference/'report.json')
    assert stencil['caseCount']==96 and stencil['comparedBuffers']==384 and not stencil['differentBytes']
    assert stencil['buildSha256']==SHA(read(home/'stencil-build/build.json'))
    for row,ref in zip(stencil['rows'],stencil_hal['cases']):
        for comparison in row['comparisons']:
            label=comparison['label'];actual=read(home/'stencil-regression'/f"case-{row['index']:03d}-{label}.bgra",False)
            expected=read(stencil_reference/ref['buffers'][label]['file'],False);assert actual==expected and SHA(expected)==ref['buffers'][label]['sha256']and not comparison['differentBytes']
    assert stage_bytes==25804800 and surface_bytes==5242880 and opaque_chain_cases==672
    compression=load(home/'compression-verified.json');assert compression['files']==24 and compression['allContentHashesUnchanged']and not compression['deletedFiles']
    plan=load(home/'compression-plan.json');assert len(plan['files'])==24
    for row in plan['files']:
        path=Path(row['path']).resolve();assert path.is_relative_to(ROOT/'artifacts/th14')and path.parent.name.startswith('retail-')
        assert path.name in['world-camera.raw','selected-state.u32']
        reference=load(path.parent/'report.json');key='worldCameraSha256'if path.name=='world-camera.raw'else'selectedSha256'
        assert reference['childExited']and not reference['error']and reference[key]==row['sha256']
        with path.open('rb')as stream:assert hashlib.file_digest(stream,'sha256').hexdigest()==row['sha256']
        assert path.stat().st_size==row['bytes']and getattr(path.stat(),'st_file_attributes',0)&0x800
    assert counts['halCanonical']==counts['halRaw']==counts['cppJs']==counts['nativeCpp']==4032
    assert digests['halCanonical'].hexdigest()==digests['cppJs'].hexdigest()==digests['nativeCpp'].hexdigest()
    result=dict(verifiedFiniteBgrxRasterIncrement=True,halCases=1344,a8ControlCases=672,x8Cases=672,cppJsCases=1344,nativeCppCases=1344,
        buffersPerBackend=4032,comparedBytesPerBackend=4128768,allCanonicalBuffersExact=True,noChannelsDropped=True,
        referenceUsesActualD3dxFormatConversion=True,rawHalBuffersRetainedAndChecked=True,x8RawUpperByteValues=hal['x8RawUpperByteValues'],
        canonicalAlphaAlwaysOpaque=True,opaqueDestinationAlphaChainCases=672,independentClearAndUnblendedMaskChecks=True,
        cppBgrxRenderTargetImplemented=True,cppSourceDelta='WebGpuRenderer.hpp target acceptance, opaque clears, alpha write masking',
        packed16BitRasterTargetsStillRejected=True,mixedFormatCopyNotNewlyEnabled=True,baselineCppRejectRetained=True,
        nativeGlesFallbackCalls=0,stageRegressionFrames=21,stageRegressionBytes=stage_bytes,d3dxRegressionCases=8,d3dxRegressionBytes=surface_bytes,
        stencilRegressionCases=96,stencilRegressionBuffers=384,stencilRegressionBytes=4718592,
        pixelDatasetDigests={key:dict(files=counts[key],sha256=value.hexdigest())for key,value in digests.items()},
        observationFilesTransparentlyCompressed=24,observationHashesPreserved=True,productionGameplayOrAudioChanged=False,
        currentBrowserCandidateUpdated=False,browserAcceptance=False,completeGame=False,nativeEquivalent=False,
        wasmSha256=js['wasmSha256'],nativeWasmSha256=native['wasmSha256'],verifierSha256=SHA(Path(__file__).read_bytes()),bindings=bindings,
        scope='Finite actual CPP Renderer A8/X8 target Clear/draw/read versus real D3D9 HAL and real D3DX canonical conversion. Both Emscripten/Asyncify/JS and WASI/native GPU paths compare all32 canonical bits; original X8 ignored bytes remain retained. Full retained21Stage/8D3DX/96stencil regressions also checked. No complete format/mixed-copy, original ordinary UI, full-game GPU/PCM, browser or whole-game acceptance.')
    output=args.output.resolve();assert output.is_relative_to(ROOT/'artifacts/th14')or output.is_relative_to(ROOT/'docs/porting')
    if args.check:assert json.loads(output.read_bytes())==result
    else:output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({key:result[key]for key in['verifiedFiniteBgrxRasterIncrement','halCases','buffersPerBackend','comparedBytesPerBackend','allCanonicalBuffersExact','stageRegressionFrames','d3dxRegressionCases','stencilRegressionCases','browserAcceptance']}))


if __name__=='__main__':main()
