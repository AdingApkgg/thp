"""Verify readback barriers and locate the first observed pixel divergences."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];BASE=ROOT/'artifacts/th14/stage-gpu-stream-replay';OUT=BASE/'pixel-trace'
sha=lambda b:hashlib.sha256(b).hexdigest()
evidence={}
def track(path):
    path=Path(path);p=path if path.is_absolute() else ROOT/path;b=p.read_bytes()
    evidence[str(p.relative_to(ROOT)).replace('\\','/')]=dict(bytes=len(b),sha256=sha(b));return b
def read(path):return json.loads(track(path))

def main():
    native=read(OUT/'trace.json');portable=read(OUT/'browser-result.json');inputs=read(OUT/'inputs.json')
    prepared=read(BASE/'prepared.json');baseline=read(BASE/'browser-result.json')
    assert native['traced'] and portable['variant']=='pixel-trace' and portable['backendVersion']==10
    assert len(native['frames'])==len(portable['reports'])==len(inputs['frames'])==3
    assert native['toolSha256']==sha(track('tools/th14-stage-gpu-pixel-trace-hal.py'))
    assert inputs['toolSha256']==sha(track('tools/th14-stage-gpu-pixel-trace-native.py'))
    assert native['inputsSha256']==sha(track(OUT/'inputs.json'))
    assert portable['wasmSha256']==read(BASE/'build.json')['wasmSha256']
    assert portable['nativePixelsSha256']==read(BASE/'native.json')['pixelsSha256']
    output=[];categories={};draw_count=0;points_count=0
    for actual,n,selected in zip(portable['reports'],native['frames'],inputs['frames']):
        key=(actual['stage'],actual['frame']);assert key==(n['stage'],n['frame'])==(selected['stage'],selected['frame'])
        old=next(r for r in baseline['reports'] if (r['stage'],r['frame'])==key)
        assert n['finalSha256']==n['expectedFinalSha256']==old['nativeSha256']==actual['nativeSha256']
        assert actual['portableSha256']==n['portableFinalSha256']==old['portableSha256']
        assert actual['differentChannels']==old['differentChannels'] and actual['maxDelta']==old['maxDelta']
        assert actual['points']==n['points']==selected['points'] and actual['beforeDraws']==n['beforeDraws']
        frame=next(f for f in prepared['frames'] if (f['stage'],f['frame'])==key)
        assert len(actual['tracedDraws'])==len(n['draws'])==actual['directDraws'];draw_count+=actual['directDraws']
        local=[];points_count+=len(n['points'])
        for i,point in enumerate(n['points']):
            before_a=actual['beforeDraws'][i];before_n=n['beforeDraws'][i]
            for a,b in zip(actual['tracedDraws'],n['draws']):
                assert (a['commandIndex'],a['drawIndex'])==(b['commandIndex'],b['drawIndex'])
                assert frame['commands'][a['commandIndex']]['kind']=='draw'
                if a['colors'][i]!=b['colors'][i]:
                    state={};texture=0;fvf=0
                    for c in frame['initialState']+frame['commands'][:a['commandIndex']]:
                        if c['kind']=='renderState':state[c['key']]=c['value']
                        elif c['kind']=='texture':texture=c['handle']
                        elif c['kind']=='fvf':fvf=c['value']
                    category='both changed' if a['colors'][i]!=before_a and b['colors'][i]!=before_n else 'only portable changed' if a['colors'][i]!=before_a else 'only native changed'
                    categories[category]=categories.get(category,0)+1
                    local.append(dict(point=point,draw=a['drawIndex'],command=a['commandIndex'],category=category,beforePortable=before_a,beforeNative=before_n,portable=a['colors'][i],native=b['colors'][i],texture=texture,fvf=fvf,renderStates=state))
                    break
                before_a=a['colors'][i];before_n=b['colors'][i]
            else:raise AssertionError(('selected mismatch never diverged',key,point))
        output.append(dict(stage=actual['stage'],frame=actual['frame'],firstDivergences=local))
    assert draw_count==452 and points_count==38
    track('tools/th14-stage-gpu-stream.html');track(OUT/'browser-result.png');logs=read(OUT/'browser-logs.json')
    report=dict(diagnosticEvidenceVerified=True,strictPixelsEqual=False,completeGame=False,nativeEquivalent=False,productionChanged=False,
                frames=3,directDraws=draw_count,selectedPixels=points_count,readbackBarriersPreserveNativeFinalFrames=True,
                readbackBarriersPreservePortableFinalFrames=True,categories=categories,firstDivergences=output,browserWarningsOrErrors=len(logs),evidence=evidence,toolSha256=sha(Path(__file__).read_bytes()),
                limits=native['scope']+' Candidate pixel traces are read through visible browser diagnostics. Final per-frame hashes and selected pixels are checked; no original process GPU or actual depth-value capture.')
    (ROOT/'docs/porting/th14-stage-gpu-pixel-trace-observed-oct12.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf8')
    print(json.dumps({k:report[k] for k in ('diagnosticEvidenceVerified','frames','directDraws','selectedPixels','categories','browserWarningsOrErrors')}))
if __name__=='__main__':main()
