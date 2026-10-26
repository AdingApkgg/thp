"""Independently compare all retained WebGPU component buffers and sampler words.

This does not execute the production C++ renderer or a browser, and never
relabels this WGSL prototype as a production WebGL fix.
"""
import argparse
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SHA=lambda raw:hashlib.sha256(raw).hexdigest()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--home',type=Path,default=ROOT/'artifacts/th14/webgpu-stage-final-oct26')
    parser.add_argument('--reference',type=Path,default=ROOT/'artifacts/th14/stage-gpu-stream-replay')
    parser.add_argument('--output',type=Path,default=ROOT/'docs/porting/th14-webgpu-stage-verified-oct26.json')
    parser.add_argument('--check',action='store_true')
    args=parser.parse_args();home=args.home.resolve(strict=True);reference=args.reference.resolve(strict=True);bindings={}
    def read(path):
        raw=path.read_bytes();bindings[path.relative_to(ROOT).as_posix()]=dict(bytes=len(raw),sha256=SHA(raw));return raw
    def load(path):return json.loads(read(path))
    stage=load(home/'replay/report.json');sampler=load(home/'sampler/report.json')
    for directory,tool,report in [('replay','th14-webgpu-stage-component-oct26.py',stage),('sampler','th14-webgpu-rgb565-sampler-oct26.py',sampler)]:
        assert report['toolSha256']==SHA(read(home/directory/'run-tool.py'))==SHA(read(ROOT/'tools'/tool))
        assert report['requiredFeatures']==[]and not report['browserRun']and not report['productionChanged']
        assert report['physicalAudioDevicesOpened']==0 and report['wgpuVersion']=='0.32.0'
    assert stage['frames']==stage['exactFrames']==21 and stage['differentChannels']==0
    assert not stage['actualProductionCppRenderer']and stage['productionSemanticsPartiallyMirrored']and stage['postclipFractionalViewport']
    assert stage['packedRgb565BitReplicatedTo8']and not stage['packedRgb565ExpandedToFloat32']
    assert stage['alphaConversionMeasuredOnOwnDevice']and stage['backend']=='D3D12'and not stage['appUiControlled']
    assert stage['wgpuNativeLibrary']==sampler['wgpuNativeLibrary']
    for path,digest in stage['sourceBindings'].items():assert SHA(read(ROOT/path))==digest
    assert SHA(read(home/'replay/shader.wgsl'))==stage['shaderSha256']
    prepared=load(reference/'prepared.json');native=load(reference/'native.json');pixels=read(reference/'native.bgra')
    assert SHA(pixels)==stage['nativePixelsSha256']==native['pixelsSha256']
    assert SHA(read(reference/'prepared.json'))==stage['preparedSha256']
    for texture in prepared['textures']:assert SHA(read(reference/texture['file']))==texture['sha256']
    assert len(prepared['frames'])==len(native['frames'])==len(stage['rows'])==21
    frames=[];bytes_compared=0
    for frame,row in zip(prepared['frames'],stage['rows']):
        assert(frame['stage'],frame['frame'])==(row['stage'],row['frame'])
        target=next(r for r in native['frames']if(r['stage'],r['frame'])==(row['stage'],row['frame']))
        expected=pixels[target['offset']:target['offset']+target['bytes']]
        actual=read(home/f"replay/stage{row['stage']}-frame{row['frame']}.bgra")
        assert len(actual)==len(expected)==640*480*4 and actual==expected
        assert SHA(actual)==row['actualSha256']==row['nativeSha256']==target['sha256']and row['differentChannels']==0
        frames.append(dict(stage=row['stage'],frame=row['frame'],draws=frame['directDraws'],fullBufferSha256=SHA(actual),controlledScreenQuadsExcluded=frame['controlledScreenQuadsExcluded']))
        bytes_compared+=len(actual)
    assert{(row['stage'],row['frame'])for row in frames}=={(stage,frame)for stage in range(1,8)for frame in [0,599,1199]}
    assert sampler['sourceWordCount']==65536 and sampler['samplerModes']==['nearest','linear']and sampler['linearTexelFraction']==[.25,.25]
    assert len(sampler['tests'])==3 and all(row['differentWords']==0 and row['maxAbsoluteDifference']==0 for row in sampler['tests'].values())
    samples={}
    for name,digest in sampler['outputs'].items():
        raw=read(home/f'sampler/{name}.f32');assert len(raw)==65536*4*4 and SHA(raw)==digest;samples[name]=raw
    pairs=[('gles565-nearest','gles8-nearest'),('gles565-linear','gles8-linear'),('gles565-linear','wgpu8-linear')]
    assert all(samples[left]==samples[right]for left,right in pairs)
    result=dict(verifiedFiniteWebgpuComponent=True,stageReferenceFrames=21,exactStageReferenceFrames=21,comparedStageBytes=bytes_compared,frames=frames,backend=stage['backend'],wgpuVersion=stage['wgpuVersion'],wgpuNativeLibrary=stage['wgpuNativeLibrary'],adapter=stage['adapter'],requiredOptionalWebgpuFeatures=[],postclipFractionalViewport=True,rgb565Expansion='B5G6R5 bit replication to BGRA8; b/r=(v<<3)|(v>>2),g=(v<<2)|(v>>4)',samplerSourceWords=65536,samplerFloatWordComparisons=3*65536*4,allSamplerFloatWordsEqual=True,linearSamplerFractions=[.25,.25],nativeGlesContext=sampler['glesInfo'],actualProductionCppRenderer=False,productionWebgpuBackendImplemented=False,productionWebglFix=False,browserAcceptance=False,productionChanged=False,physicalAudioDevicesOpened=0,completeGame=False,nativeEquivalent=False,verifierSha256=SHA(Path(__file__).read_bytes()),bindings=bindings,limitations=['A WGSL mirror of the stated fixed-function subset; the actual production C++ Renderer is not executed. Integration remains required.','The original native offscreen Stage command reference retains its controlled defaults and screen-queue exclusions; not an original whole-game framebuffer.','Sampler equality covers all16-bit source codes with nearest and one quarter-texel linear configuration on the stated devices; not all UVs/devices/formats.','No ordinary application UI, complete render targets/pause/capture, browser WebGPU or WebGL correctness, audio, whole game or all-input equivalence.'])
    output=args.output.resolve();assert output.is_relative_to(ROOT/'docs/porting')or output.is_relative_to(ROOT/'artifacts/th14')
    if args.check:assert json.loads(output.read_bytes())==result
    else:output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({key:result[key]for key in ['verifiedFiniteWebgpuComponent','exactStageReferenceFrames','comparedStageBytes','samplerSourceWords','samplerFloatWordComparisons','productionWebgpuBackendImplemented']}))


if __name__=='__main__':main()
