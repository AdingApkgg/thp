"""Recompute private viewport experiments; never start a device or game.

Successful evidence verification is separate from accepting a graphics change.
Both candidates remain rejected, including the one that improves recorded UVs.
"""
from pathlib import Path
import argparse,array,collections,hashlib,json,math,struct
R=Path(__file__).resolve().parents[1];A=R/'artifacts/th14'
OUTPUT=A/'viewport-candidates-audited-v2-oct19.json'
sha=lambda b:hashlib.sha256(b).hexdigest()

def inspect():
    bindings={}
    def read(p):
        p=Path(p);b=p.read_bytes();bindings[str(p.relative_to(R))]=dict(bytes=len(b),sha256=sha(b));return b
    def load(p):return json.loads(read(p))
    def words(b):
        a=array.array('I');a.frombytes(b);return a
    def diff(a,b):
        assert len(a)==len(b)
        return sum(x!=y for x,y in zip(a,b))
    base=A/'stage-production-clip-no-finite-guard-oct14'
    baseColor=load(base/'color/capture/report.json');baseUv=load(base/'uv/capture/report.json')
    nativeColor=load(A/'stage-gpu-stream-replay/native.json');nativeBytes=read(A/'stage-gpu-stream-replay/native.bgra')
    assert sha(nativeBytes)==nativeColor['pixelsSha256']
    references={}
    def add(key,b,expected):
        assert len(b)==4915200 and sha(b)==expected
        if key in references:assert references[key]==b
        references[key]=b
    for folder,file in [('world-uv','native.rgba32f'),('sampler-uv-worst','full.rgba32f'),('sampler-uv-strip','full.rgba32f')]:
        d=A/'stage-gpu-stream-replay'/folder;n=load(d/'native.json');raw=read(d/file)
        for row in n['frames']:
            b=raw[row['offset']:row['offset']+row['bytes']] if folder=='world-uv' else raw
            add((row['stage'],row['frame'],row['originalDrawIndex']),b,row.get('sha256',row.get('fullFloatFrameSha256')))
    for folder in ['stage-current-residual-native-uv-fe406-oct14','viewport-regression-native-oct19']:
        d=A/folder;n=load(d/'native.json')
        for i,row in enumerate(n['frames']):add((row['stage'],row['frame'],row['originalDrawIndex']),read(d/f'frame-{i:03}.rgba32f'),row['fullFloatFrameSha256'])
    candidates=[]
    for name in ['uniform-viewport-candidate-oct19','uniform-viewport-inside-candidate-oct19']:
        d=A/name
        for mode in ['color','uv']:
            build=load(d/mode/'build.json')
            assert sha(read(d/mode/'gpu.wasm'))==build['wasmSha256']
            assert sha(read(d/mode/'gpu.mjs'))==build['loaderSha256']
            for p,row in build['sourceBindings'].items():
                b=read(R/p);assert len(b)==row['bytes'] and sha(b)==row['sha256'],p
            for p,row in build['sources'].items():
                b=read(d/mode/p);assert len(b)==row['bytes'] and sha(b)==row['sha256'],p
            # Actual source changes are limited to the TH14 shader literal.
            original=read(R/'runtimes/th12/portable/sdl/Shaders.hpp').decode()
            changed=read(d/mode/'Shaders.hpp').decode()
            if mode=='color':assert original.split('#else',1)[1]==changed.split('#else',1)[1]
        color=load(d/'color/capture/report.json');uv=load(d/'uv/capture/report.json')
        assert color['frames']==21 and uv['frames']==23
        assert color['wasmSha256']==load(d/'color/build.json')['wasmSha256']
        assert uv['wasmSha256']==load(d/'uv/build.json')['wasmSha256']
        colorRows=[]
        for row,old,n in zip(color['reports'],baseColor['reports'],nativeColor['frames']):
            assert (row['stage'],row['frame'])==(old['stage'],old['frame'])==(n['stage'],n['frame'])
            actual=read(d/'color/capture'/row['savedFile']);prior=read(base/'color/capture'/old['savedFile']);expected=nativeBytes[n['offset']:n['offset']+n['bytes']]
            assert sha(actual)==row['portableSha256'] and sha(prior)==old['portableSha256'] and sha(expected)==row['nativeSha256']
            newCount=diff(actual,expected);oldCount=diff(prior,expected)
            assert newCount==row['differentChannels'] and oldCount==old['differentChannels']
            colorRows.append(dict(stage=row['stage'],frame=row['frame'],baselineDifferences=oldCount,candidateDifferences=newCount))
        assert sum(r['candidateDifferences'] for r in colorRows)==color['differentChannels']
        uvRows=[];exact=0
        for row,old in zip(uv['reports'],baseUv['reports']):
            key=(row['stage'],row['frame'],row['originalDrawIndex']);assert key==(old['stage'],old['frame'],old['originalDrawIndex'])
            b=read(d/'uv/capture'/row['savedFile']);prior=read(base/'uv/capture'/old['savedFile'])
            assert sha(b)==row['portableSha256'] and sha(prior)==old['portableSha256']
            same=sha(b)==row['nativeSha256'];assert same==row['strictFullBufferHashEqual'];exact+=same
            rr=dict(key=list(key),baselineExact=old['strictFullBufferHashEqual'],candidateExact=same)
            if key in references:
                ref=references[key];assert sha(ref)==row['nativeSha256'];nw=words(ref);cw=words(b);bw=words(prior)
                rr.update(baselineWordDifferences=diff(bw,nw),candidateWordDifferences=diff(cw,nw),coverageDifferences=sum((cw[i]!=0)!=(nw[i]!=0) for i in range(3,len(nw),4)),fullNativeWordsCompared=len(nw))
            uvRows.append(rr)
        assert exact==uv['exactFullBuffers']
        candidates.append(dict(name=name,colorDifferences=color['differentChannels'],colorRows=colorRows,exactUv=exact,uvRows=uvRows,accepted=False))
    boundary=A/'viewport-boundary-control-oct19';native=load(boundary/'native-run/report.json')
    assert native['nativeControlFullGate'] and native['finiteOutputGate'] and native['drawCalls']==2
    b=boundary/'v2';report=load(b/'capture/report.json');assert report['drawCalls']==3 and report['executionFailed'] and not report['executionCompleted']
    assert report['aTfCopyGate'] and report['aFrozenPixelsGate'] and report['error']=='Error: Finite GPU output c'
    nativePixels=read(boundary/'native-run/b-full.rgba32f');nw=words(nativePixels);boundaryRows=[]
    assert sha(nativePixels)==native['rows'][1]['sha256']
    source=read(boundary/'synthetic-clip.f32');assert all(math.isfinite(v[0]) for v in struct.iter_unpack('<f',source))
    for label,row in zip('abc',report['arms']):
        tf=read(b/f'capture/{label}-tf.f32');px=read(b/f'capture/{label}-pixels.rgba32f')
        assert sha(tf)==row['emittedSha256'] and sha(px)==row['pixelsSha256']
        nonfiniteTf=sum(not math.isfinite(v[0]) for v in struct.iter_unpack('<f',tf))
        nonfinitePixels=sum(not math.isfinite(v[0]) for v in struct.iter_unpack('<f',px))
        different=diff(words(px),nw);assert different==row['againstFrozenNative']['differentWords']
        boundaryRows.append(dict(label=label,nonfiniteTfWords=nonfiniteTf,nonfinitePixelWords=nonfinitePixels,wordsDifferentFromNative=different))
    assert boundaryRows[1]['nonfiniteTfWords']==0 and boundaryRows[2]['nonfiniteTfWords']==12
    assert boundaryRows[2]['nonfinitePixelWords']==0
    read(Path(__file__))
    return dict(evidenceVerified=True,productionChanged=False,candidateAccepted=False,completeGame=False,nativeEquivalent=False,
                frozenNativeUvBuffers=len(references),candidates=candidates,syntheticBoundaryRows=boundaryRows,allFailedRawBuffersRetained=True,
                scope='Private declared viewport candidates only. Recorded-case improvement does not establish valid clip-boundary behavior. Synthetic candidateC has12 nonfinite TF position words; pixels are finite but differ from Native more than unchanged bridge. No candidate adopted.',bindings=bindings)

def main():
    p=argparse.ArgumentParser();p.add_argument('--write',action='store_true');p.add_argument('--check',action='store_true');a=p.parse_args();assert a.write!=a.check
    result=inspect()
    if a.write:
        with OUTPUT.open('x',encoding='utf-8') as f:json.dump(result,f,indent=2);f.write('\n')
    else:assert json.loads(OUTPUT.read_bytes())==result
    print(json.dumps(dict(evidenceVerified=True,candidateAccepted=False,candidates=[dict(name=r['name'],colorDifferences=r['colorDifferences'],exactUv=r['exactUv']) for r in result['candidates']],boundary=result['syntheticBoundaryRows'],bindings=len(result['bindings']))))
if __name__=='__main__':main()
