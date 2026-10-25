"""Verify scoped native/D3D11 clip-order controls; never upgrades browser acceptance."""
import argparse,hashlib,json,struct
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
SHA=lambda b:hashlib.sha256(b).hexdigest()
OUTPUT=ROOT/'docs/porting/th14-background-clip-order-verified-oct26.json'

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--check',action='store_true');args=parser.parse_args();bindings={}
    def read(name):
        path=ROOT/name;data=path.read_bytes();bindings[path.relative_to(ROOT).as_posix()]=dict(bytes=len(data),sha256=SHA(data));return data
    def load(name):return json.loads(read(name))
    home='artifacts/th14/pixel-background-d3d11-oct26/'
    baseline=load('artifacts/th14/current-gpu-baseline-oct25/color/capture/report.json');build=load('artifacts/th14/current-gpu-baseline-oct25/color/build.json')
    assert baseline['exactFullBuffers']==20 and not baseline['strictPixelsEqual']and baseline['differentChannels']==1
    assert build['wasmSha256']==baseline['wasmSha256']
    for name,bound in build['sourceBindings'].items():assert SHA(read(name))==bound['sha256']
    codec=baseline['__th14ShaderSourceCodec'];program=next(p for p in baseline['shaderBackend']['contexts'][0]['programs']if p['programId']==6)
    for shader in program['shaders']:
        digest=shader['translatedSourceSha256'];entry=codec['sourceBySha256'][digest];data=''.join(codec['shaderTextLines'][i]for i in entry['lineIds']).encode()
        assert SHA(data)==digest and len(data)==entry['utf8Bytes']
        assert read(home+'program-6-'+shader['typeName']+'.hlsl').decode().replace('\r\n','\n').encode()==data
    native_uv=load(home+'native-uv/native.json');native_vs2=load(home+'native-vs2/native.json')
    for report,label in [(native_uv,'native-uv'),(native_vs2,'native-vs2')]:
        assert report['generated']and report['format']==116 and len(report['frames'])==1
        raw=read(home+label+'/native.rgba32f');assert len(raw)==16 and SHA(raw)==report['pixelsSha256']
        assert struct.pack('<4I',*report['frames'][0]['words'])==raw
        assert SHA(read(home+label+'/native.py'))==report['toolSha256']
    original_uv=native_uv['frames'][0]['words'];assert original_uv==native_vs2['frames'][0]['words']
    assert original_uv==[1070961857,1073072535,0,1065353216]
    components=load('artifacts/th14/pixel-background-components-oct26/native.json')
    source=next(row for row in components['frames']if row['frame']=='source');fog=next(row for row in components['frames']if row['frame']=='fog-factor')
    raw=read('artifacts/th14/pixel-background-components-oct26/native.bgra');assert SHA(raw)==components['pixelsSha256']
    before=load(home+'result.json');after=load(home+'postclip-viewport/result.json')
    for report in [before,after]:
        assert report['authoredInitialHlslReconstruction']and not report['actualBrowserRun']and not report['actualFinalBrowserDxbc']and not report['productionChanged']
        assert report['draw']==3 and not report['computedPrimitiveEligible']and len(report['rows'])==8
    assert after['halfPixelBiasAfterClipping']
    get=lambda report,inst,mode,format:next(row for row in report['rows']if row['instancedBranch']==inst and row['mode']==mode and row['targetFormat']==format)
    for instanced in [False,True]:
        assert get(before,instanced,'color',87)['values']==[5,30,3,255]
        assert get(after,instanced,'color',87)['values']==[6,30,3,255]
        assert get(after,instanced,'color',2)['words']==source['rgbaWords']
        assert get(before,instanced,'uv',2)['words']==[1070961855,1073072535,0,1065353216]
        assert get(after,instanced,'uv',2)['words']==original_uv
        assert get(before,instanced,'fog',2)['words']==get(after,instanced,'fog',2)['words']==fog['rgbaWords']
    sampler=load(home+'d3d11-sampler-result.json');assert not sampler['actualBrowserRun']and len(sampler['rows'])==8
    positive=[r for r in sampler['rows']if r['inputKind']=='nativeInterpolatedUv'];negative=[r for r in sampler['rows']if r['inputKind']=='reconstructedInitialHlslUv']
    assert len(positive)==len(negative)==4 and all(row['equal']for row in positive)and all(not row['equal']for row in negative)
    for row in positive:assert row['rgbaWords']==next(c['rgbaWords']for c in components['frames']if c['frame']==row['mode'])
    corners=load(home+'native-clip/native.json');inputs=load(home+'native-clip/clip-inputs.json');clip=load(home+'clip-result.json')
    assert len(corners['frames'])==len(inputs)==len(clip['rows'])==4 and clip['allNativeVs2CornerWordsEqual']
    for index,(row,native)in enumerate(zip(clip['rows'],corners['frames'],strict=True)):
        assert row['corner']==inputs[index]['corner']==index and row['equal']and row['actualWords']==row['nativeWords']==native['samples'][0]['words']
    assert SHA(read(home+'native-clip/samples.rgba32f'))==corners['pixelsSha256']
    for name in ['replay.py','replay-postclip.py','sampler.py','clip.py','native-clip/native.py','native-clip/inputs.json','native-vs2/probe.vs.asm','native-uv/probe.asm']:
        read(home+name)
    read('artifacts/th14/pixel-layer-components-oct26/d3d11-blend.py')
    u_before=get(before,False,'uv',2)['values'][0];u_after=get(after,False,'uv',2)['values'][0]
    fraction=lambda value:((value*256-.5)%1)*256
    assert fraction(u_before)==169.4921875 and fraction(u_after)==169.5078125
    result=dict(schema='th14/background-clip-order/1',productionChanged=False,retainedActualBrowser=dict(completeSceneBuffers=21,exactSceneBuffers=20,differentChannels=1,strictPixelsEqual=False,wasmSha256=baseline['wasmSha256']),component=dict(stage=3,frame=1199,draw=3,pixel=[144,373],originalFfpUvEqualsAuthoredD3D9Vs2=True,d3d9Vs2AndD3D11Dot4CornerWordsEqual=16,preclipReconstructionUvWords=get(before,False,'uv',2)['words'][:2],originalUvWords=original_uv[:2],uWordDifference=2,filterFractionBefore=fraction(u_before),filterFractionAfter=fraction(u_after),sameCoordinateSamplerCasesEqual=4,reconstructedCoordinateNegativeCasesDifferent=4,preclipBackgroundBgra=[5,30,3,255],postclipViewportBackgroundBgra=[6,30,3,255],postclipFloatSourceAndFogWordsEqualNative=True,instancedAndOrdinaryBranchesCompared=True),actualBrowserRunThisExperiment=False,currentBrowserPixelFixed=False,rawGameAssetsPublished=False,bindings=bindings,toolSha256=SHA(Path(__file__).read_bytes()),limits=['D3D11 uses retained INITIAL HLSL plus authored IO, constant-buffer layout and coordinate scaffolding. Final browser shader linkage and DXBC were not captured.','This isolates draw3 and a sampled pixel; missing original prefix depth and isolated fragment outputs limit the scope.','The half-pixel viewport control establishes a mechanism in this reconstruction. It does not prove current browser pre-overlay bytes or fix the production WebGL path.','All original full-buffer failures remain failures. No coordinate patch, tolerance or native-value injection into the game runtime was introduced.'],completeGame=False,nativeEquivalent=False)
    if args.check:assert json.loads(OUTPUT.read_bytes())==result
    else:OUTPUT.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    print(json.dumps(dict(verified=True,originalUvWordDifference=2,postclipSourceMatches=True,browserAcceptance=False,productionChanged=False)))

if __name__=='__main__':main()
