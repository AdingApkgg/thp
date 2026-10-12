import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];BASE='artifacts/th14/stage-gpu-stream-replay/';evidence={};sha=lambda b:hashlib.sha256(b).hexdigest()
def track(p):
    b=(ROOT/p).read_bytes();evidence[p]=dict(bytes=len(b),sha256=sha(b));return b
def read(p):return json.loads(track(p))
native=read(BASE+'viewport-color-trace/trace.json');browser=read(BASE+'viewport-color-trace/browser-result.json');inputs=read(BASE+'viewport-color-trace/inputs.json');generation=read(BASE+'viewport-color-trace/generation.json');original=read(BASE+'variants/no-fog/native.json');previous=read(BASE+'variants/viewport-no-fog/browser-result.json');prepared=read(BASE+'prepared.json');pixels=track(BASE+'viewport-color-trace/native.bgra');pixel_report=read(BASE+'viewport-color-trace/native.json');assert sha(pixels)==pixel_report['pixelsSha256']
for key,p in [('generatorSha256','tools/th14-stage-viewport-color-trace-native.py'),('baseSourceSha256','tools/th14-stage-gpu-pixel-trace-hal.py'),('halSourceSha256','tools/th14-stage-viewport-color-trace-hal.py'),('inputsSha256',BASE+'viewport-color-trace/inputs.json'),('traceSha256',BASE+'viewport-color-trace/trace.json')]:assert generation[key]==sha(track(p))
assert inputs['nativeProofSha256']==sha(track(BASE+'variants/no-fog/native.json'));assert inputs['browserProofSha256']==sha(track(BASE+'variants/viewport-no-fog/browser-result.json'));build=read(BASE+'variants/viewport-no-fog/build.json');assert browser['wasmSha256']==build['wasmSha256']==sha(track(BASE+'variants/viewport-no-fog/gpu.wasm'))
for p,h in build['sources'].items():assert h==sha(track(BASE+'variants/viewport-no-fog/'+p))
rows=[];draws=points=different=0
for nr,br,fr in zip(native['frames'],browser['reports'],pixel_report['frames'],strict=True):
    assert (nr['stage'],nr['frame'])==(br['stage'],br['frame']);assert nr['points']==br['points'];assert nr['beforeDraws']==br['beforeDraws'];assert len(nr['draws'])==len(br['tracedDraws']);draws+=len(nr['draws']);points+=len(nr['points']);different+=br['differentChannels']
    n=next(x for x in original['frames'] if (x['stage'],x['frame'])==(nr['stage'],nr['frame']));b=next(x for x in previous['reports'] if (x['stage'],x['frame'])==(nr['stage'],nr['frame']));assert nr['finalSha256']==n['sha256']==sha(pixels[fr['offset']:fr['offset']+fr['bytes']]);assert br['portableSha256']==b['portableSha256']
    f=next(x for x in prepared['frames'] if (x['stage'],x['frame'])==(nr['stage'],nr['frame']));states={60:0xffffffff};tex=0;vf=0;commands=[]
    for c in f['initialState']+f['commands']:
        if c['kind']=='renderState':states[c['key']]=c['value']
        elif c['kind']=='texture':tex=c['handle']
        elif c['kind']=='fvf':vf=c['value']
        elif c['kind']=='draw':commands.append(dict(texture=tex,fvf=vf,factor=states[60],sourceBlend=states.get(19,5),destinationBlend=states.get(20,6),words=c['words'],stride=c['stride']))
    for pi,point in enumerate(nr['points']):
        nc=nr['beforeDraws'][pi];bc=br['beforeDraws'][pi]
        for di,(nd,bd) in enumerate(zip(nr['draws'],br['tracedDraws'],strict=True)):
            assert nd['commandIndex']==bd['commandIndex'] and nd['drawIndex']==bd['drawIndex']
            if nd['colors'][pi]!=bd['colors'][pi]:
                assert nc==bc;rows.append(dict(stage=nr['stage'],frame=nr['frame'],point=point,draw=di,nativeBefore=nc,portableBefore=bc,nativeAfter=nd['colors'][pi],portableAfter=bd['colors'][pi],**commands[di]));break
            nc=nd['colors'][pi];bc=bd['colors'][pi]
assert len(rows)==points==102 and draws==701 and different==3769;assert rows==read(BASE+'viewport-color-trace/first-divergences.json');assert browser['maxDelta']==2
out=dict(diagnosticEvidenceVerified=True,strictPixelsEqual=False,productionChanged=False,completeGame=False,nativeEquivalent=False,frames=9,directDraws=draws,points=points,differentChannels=different,maxDelta=2,firstDivergences=rows,evidence=evidence,toolSha256=sha(Path(__file__).read_bytes()),scope='Independent no-fog override; every selected first mismatch has equal before colors and bound original draw/texture/factor/FVF. Native and browser readback barriers preserve all prior complete frame hashes. Shader source is bound but full portable pixel buffers are not independently archived. Does not identify a single root cause or establish original game/whole-game equivalence.')
(ROOT/'docs/porting/th14-stage-viewport-color-trace-observed-oct12.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(dict(diagnosticEvidenceVerified=True,directDraws=draws,points=points)))
