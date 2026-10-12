"""Verify the independent Always override and join original mismatch depth data."""
import hashlib,json,struct,collections
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];BASE='artifacts/th14/stage-gpu-stream-replay/';evidence={};sha=lambda b:hashlib.sha256(b).hexdigest()
def track(path):
    b=(ROOT/path).read_bytes();evidence[path]=dict(bytes=len(b),sha256=sha(b));return b
def read(path):return json.loads(track(path))
n=read(BASE+'depth-always-trace/trace.json');b=read(BASE+'depth-always-trace/browser-result.json');generation=read(BASE+'depth-always-trace/generation.json');build=read(BASE+'variants/depth-always-trace/build.json');original_first=read(BASE+'depth-trace/first-divergences.json');no_depth=read(BASE+'variants/no-depth/native.json');no_depth_browser=read(BASE+'variants/no-depth/browser-result.json');incoming=[];hist=collections.Counter();samples=draws=0
for key,path in [('generatorSha256','tools/th14-stage-gpu-depth-incoming-native.py'),('baseSourceSha256','tools/th14-stage-gpu-depth-trace-hal.py'),('halSourceSha256','tools/th14-stage-gpu-depth-incoming-hal.py'),('inputsSha256',BASE+'depth-always-trace/inputs.json'),('traceSha256',BASE+'depth-always-trace/trace.json')]:assert generation[key]==sha(track(path))
for p,h in build['sources'].items():assert h==sha(track(BASE+'variants/depth-always-trace/'+p))
assert build['toolSha256']==sha(track('tools/th14-stage-gpu-depth-incoming-build.mjs'));assert build['baseBuildSha256']==sha(track(BASE+'variants/depth-trace/build.json'));assert build['wasmSha256']==sha(track(BASE+'variants/depth-always-trace/gpu.wasm'))==b['wasmSha256'];assert build['loaderSha256']==sha(track(BASE+'variants/depth-always-trace/gpu.mjs'))
native_report=read(BASE+'depth-always-trace/native.json');pixels=track(BASE+'depth-always-trace/native.bgra');assert sha(pixels)==native_report['pixelsSha256']
for nr,br,fr in zip(n['frames'],b['reports'],native_report['frames'],strict=True):
    assert (nr['stage'],nr['frame'])==(br['stage'],br['frame']);assert nr['points']==br['points'];assert nr['beforeDraws']==br['beforeDraws'];assert len(nr['draws'])==len(br['tracedDraws']);assert len(nr['depthSamples'])==len(br['depthSamples'])==len(nr['draws'])+1
    nd=next(r for r in no_depth['frames'] if (r['stage'],r['frame'])==(nr['stage'],nr['frame']));bd=next(r for r in no_depth_browser['reports'] if (r['stage'],r['frame'])==(nr['stage'],nr['frame']))
    assert nr['finalSha256']==nd['sha256']==sha(pixels[fr['offset']:fr['offset']+fr['bytes']]);assert br['portableSha256']==bd['portableSha256']
    for ns,bs in zip(nr['depthSamples'],br['depthSamples'],strict=True):
        for w,z,bz in zip(ns['floatWords'],ns['d16'],bs['d16'],strict=True):assert z==round(struct.unpack('<f',struct.pack('<I',w))[0]*65535);assert 0<=z<=65535 and 0<=bz<=65535;samples+=1;hist[bz-z]+=1
    draws+=len(nr['draws'])
for r in original_first:
    nr=next(x for x in n['frames'] if (x['stage'],x['frame'])==(r['stage'],r['frame']));br=next(x for x in b['reports'] if (x['stage'],x['frame'])==(r['stage'],r['frame']));pi=nr['points'].index(r['point']);di=r['draw'];nn=nr['depthSamples'][di+1]['d16'][pi];bb=br['depthSamples'][di+1]['d16'][pi]
    prevn=nr['draws'][di-1]['colors'][pi] if di else nr['beforeDraws'][pi];prevb=br['tracedDraws'][di-1]['colors'][pi] if di else br['beforeDraws'][pi]
    incoming.append(dict(**r,nativeIncomingOrRetained=nn,webglIncomingOrRetained=bb,nativeAlwaysColorChanged=nr['draws'][di]['colors'][pi]!=prevn,webglAlwaysColorChanged=br['tracedDraws'][di]['colors'][pi]!=prevb))
assert incoming==read(BASE+'depth-always-trace/original-first-divergences.json');categories=collections.Counter((r['nativeAlwaysColorChanged'],r['webglAlwaysColorChanged']) for r in incoming);assert categories=={(True,True):35,(False,True):3}
assert draws==452 and samples==6770;assert b['differentChannels']==sum(r['differentChannels'] for r in b['reports'])==762;assert b['maxDelta']==25
out=dict(diagnosticEvidenceVerified=True,productionChanged=False,completeGame=False,nativeEquivalent=False,strictPixelsEqual=False,directDraws=draws,depthSamples=samples,firstDivergences=incoming,categories=[dict(nativeColorChanged=k[0],webglColorChanged=k[1],points=v) for k,v in categories.items()],depthDeltaHistogram=sorted(hist.items()),evidence=evidence,toolSha256=sha(Path(__file__).read_bytes()),scope='Depth Always with depth writes enabled is an independent override. Both final color frame hashes equal separately captured no-depth controls. 35 selected first mismatches write colors on both sides when depth Always; 3 only write on WebGL. IncomingOrRetained is not claimed to be incoming depth when coverage/alpha fails. Does not identify coverage versus alpha or repair the renderer.')
(ROOT/'docs/porting/th14-stage-gpu-depth-incoming-observed-oct12.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(dict(diagnosticEvidenceVerified=True,points=len(incoming),categories=out['categories'])))
