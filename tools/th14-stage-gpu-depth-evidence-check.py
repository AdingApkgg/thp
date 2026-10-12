"""Bind depth samples to exact color-frame controls and installed vendor API."""
import collections,hashlib,json,math,struct
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];BASE='artifacts/th14/stage-gpu-stream-replay/';evidence={}
sha=lambda b:hashlib.sha256(b).hexdigest()
def track(path):
    b=(ROOT/path).read_bytes();evidence[path]=dict(bytes=len(b),sha256=sha(b));return b
def read(path):return json.loads(track(path))
native=read(BASE+'depth-trace/trace.json');browser=read(BASE+'depth-trace/browser-result.json');old=read(BASE+'pixel-trace/trace.json');old_browser=read(BASE+'pixel-trace/browser-result.json');generation=read(BASE+'depth-trace/generation.json');build=read(BASE+'variants/depth-trace/build.json')
for key,path in [('generatorSha256','tools/th14-stage-gpu-depth-trace-native.py'),('baseSourceSha256','tools/th14-stage-gpu-pixel-trace-hal.py'),('halSourceSha256','tools/th14-stage-gpu-depth-trace-hal.py'),('referenceSha256',BASE+'depth-reference/reference.json'),('traceSha256',BASE+'depth-trace/trace.json'),('inputsSha256',BASE+'depth-trace/inputs.json')]:assert generation[key]==sha(track(path))
nvpath=Path('C:/Windows/System32/nvapi64.dll');assert generation['nvapiSha256']==sha(nvpath.read_bytes())
ref=read(BASE+'depth-reference/reference.json');assert ref['sha256']==sha(track(BASE+'depth-reference/nvapi_interface.h'))
for p,h in build['sources'].items():assert h==sha(track(BASE+'variants/depth-trace/'+p))
assert build['wasmSha256']==sha(track(BASE+'variants/depth-trace/gpu.wasm'))==browser['wasmSha256'];assert build['loaderSha256']==sha(track(BASE+'variants/depth-trace/gpu.mjs'))
assert build['toolSha256']==sha(track('tools/th14-stage-gpu-depth-trace-build.mjs'));assert build['readToolSha256']==sha(track('tools/th14-stage-gpu-depth-trace-read.js'));assert build['baseBuildSha256']==sha(track(BASE+'build.json'))
native_pixels=track(BASE+'depth-trace/native.bgra');native_frames=read(BASE+'depth-trace/native.json');assert sha(native_pixels)==native_frames['pixelsSha256']
hist=collections.Counter();draws=points=samples=0;first=[]
for nr,br,previous,pb,fr in zip(native['frames'],browser['reports'],old['frames'],old_browser['reports'],native_frames['frames'],strict=True):
    assert [nr['stage'],nr['frame']]==[br['stage'],br['frame']]==[previous['stage'],previous['frame']]
    assert nr['points']==br['points']==previous['points'];assert nr['beforeDraws']==br['beforeDraws']==previous['beforeDraws']
    assert nr['draws']==previous['draws'];assert br['tracedDraws']==pb['tracedDraws']
    assert nr['finalSha256']==previous['finalSha256']==sha(native_pixels[fr['offset']:fr['offset']+fr['bytes']]);assert br['portableSha256']==pb['portableSha256']
    assert len(nr['depthSamples'])==len(br['depthSamples'])==len(nr['draws'])+1
    assert nr['depthSamples'][0]['d16']==br['depthSamples'][0]['d16']==[65535]*len(nr['points'])
    for ns,bs in zip(nr['depthSamples'],br['depthSamples'],strict=True):
        assert len(ns['d16'])==len(bs['d16'])==len(nr['points'])
        for w,z,bz in zip(ns['floatWords'],ns['d16'],bs['d16'],strict=True):
            assert z==round(struct.unpack('<f',struct.pack('<I',w))[0]*65535);assert 0<=z<=65535 and 0<=bz<=65535;hist[bz-z]+=1;samples+=1
    for pi,point in enumerate(nr['points']):
        nc=nr['beforeDraws'][pi];bc=br['beforeDraws'][pi]
        for di,(nd,bd) in enumerate(zip(nr['draws'],br['tracedDraws'],strict=True)):
            if nd['colors'][pi]!=bd['colors'][pi]:
                first.append(dict(stage=nr['stage'],frame=nr['frame'],point=point,draw=di,nativeBefore=nr['depthSamples'][di]['d16'][pi],webglBefore=br['depthSamples'][di]['d16'][pi],nativeAfter=nr['depthSamples'][di+1]['d16'][pi],webglAfter=br['depthSamples'][di+1]['d16'][pi],nativeChanged=nc!=nd['colors'][pi],webglChanged=bc!=bd['colors'][pi]));break
            nc=nd['colors'][pi];bc=bd['colors'][pi]
    draws+=len(nr['draws']);points+=len(nr['points'])
assert draws==452 and points==38;assert first==read(BASE+'depth-trace/first-divergences.json')
model_reports=[]
for folder,expected in [('depth-quantization',334),('depth-threshold',915)]:
    report=read(BASE+folder+'/native.json');assert report['toolSha256']==sha(track('tools/th14-stage-'+('depth-quantization-hal.py' if folder=='depth-quantization' else 'depth-depth-threshold-hal.py').replace('depth-depth','depth')))
    assert report['nvapiSha256']==generation['nvapiSha256'];assert report['interfaceSha256']==ref['sha256'];rows=report['rows'][-1]['samples'];assert len(rows)==expected
    for row in rows:
        assert row['copyStatus']==row['readbackHresult']==0
        z=row['inputDepth'];assert struct.unpack('<f',struct.pack('<I',row['inputWord']))[0]==z
        assert row['d16']==round(row['firstFloat']*65535)
    errs=sum(math.ceil(math.floor(r['inputDepth']*1048576)/1048576*65535-.5)!=r['d16'] for r in rows);assert errs==0
    model_reports.append(dict(folder=folder,samples=expected,fixed20FloorThenNearestTiesDownDifferences=errs))
track('tools/th14-stage-depth-quantization-native.py');track(BASE+'depth-quantization/generation.json');track(BASE+'depth-threshold/thresholds.json');track(BASE+'depth-trace/browser-result.png');assert read(BASE+'depth-trace/browser-logs.json')==[]
output=dict(diagnosticEvidenceVerified=True,completeGame=False,nativeEquivalent=False,productionChanged=False,strictPixelsEqual=False,frames=3,directDraws=draws,points=points,depthSamples=samples,depthDeltaHistogram=sorted(hist.items()),firstDivergences=first,constantScreenDepthModels=model_reports,evidence=evidence,toolSha256=sha(Path(__file__).read_bytes()),scope='Native D16 storage via installed NVAPI R32F copy; independent WebGL D16 renderbuffer blit/encode readback. Per-draw colors and all final frame hashes exactly preserve both previous controls. Constant screen-depth inputs support a fixed20 truncation and nearest ties-down candidate on this installed HAL only. Does not prove world interpolation equivalence or establish all color differences as depth-only. No retail process framebuffer, original-game natural completion or whole-game 1:1 claim.')
(ROOT/'docs/porting/th14-stage-gpu-depth-observed-oct12.json').write_text(json.dumps(output,indent=2)+'\n');print(json.dumps(dict(diagnosticEvidenceVerified=True,depthSamples=samples,constantScreenDepthModels=model_reports)))
