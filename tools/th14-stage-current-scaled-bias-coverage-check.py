"""Independent archived-buffer check for the uniform scaled half-pixel trial."""
import hashlib,json,struct
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1];evidence={}
sha=lambda b:hashlib.sha256(b).hexdigest()
def track(p):
    b=(ROOT/p).read_bytes();evidence[p]={'bytes':len(b),'sha256':sha(b)};return b
def read(p):return json.loads(track(p))
BASE='artifacts/th14/stage-current-graphics-fe406-oct14/'
CANDIDATE='artifacts/th14/stage-current-sequential-clip-scaled-bias-fe406-oct14/'
cases=read(BASE+'uv-cases.json');report=read(CANDIDATE+'uv/capture/report.json');build=read(CANDIDATE+'uv/build.json')
assert len(cases['cases'])==len(report['reports'])==23
assert report['sourceBindings']==build['sourceBindings']==read(BASE+'sources.json')['sourceBindings']
assert not build['transformFeedback'] and not build['constantVaryings'] and not build['capturedNativeClipValuesUsed']
assert build['preservesCurrentDepth16'] and build['preservesFogEye']
assert sha(track(CANDIDATE+'uv/gpu.wasm'))==build['wasmSha256']==report['wasmSha256']
assert sha(track(CANDIDATE+'uv/gpu.mjs'))==build['loaderSha256']
for p,b in build['sources'].items():
    raw=track(CANDIDATE+'uv/'+p);assert len(raw)==b['bytes'] and sha(raw)==b['sha256']
assert sha(track('tools/th14-stage-current-sequential-clip-scaled-bias-build.mjs'))==build['toolSha256']
full={}
for binding in cases['fullBindings']:
    raw=track(binding['path'])[binding['offset']:binding['offset']+binding['bytes']];assert sha(raw)==binding['sha256'];full[binding['key']]=raw
    assert sha(track(binding['reportPath']))==binding['reportSha256']
rows=[];samples=words=primary_equal=extra_equal=0;planes=[];yy,xx=np.indices((480,640))
for i,(case,observed) in enumerate(zip(cases['cases'],report['reports'],strict=True)):
    raw=track(CANDIDATE+'uv/capture/'+f'frame-{i:03d}.rgba32f');assert len(raw)==640*480*16 and sha(raw)==observed['portableSha256']
    assert case['nativeSha256']==observed['nativeSha256'];equal=sha(raw)==case['nativeSha256'];assert equal==observed['strictFullBufferHashEqual']
    if case['role']=='selected21':primary_equal+=equal
    else:extra_equal+=equal
    uv=np.frombuffer(raw,dtype='<f4').reshape(480,640,4);raw_words=np.frombuffer(raw,dtype='<u4').reshape(480,640,4);sample_diffs=[]
    for s in case['samples']:
        actual=list(map(int,raw_words[s['y'],s['x']]));count=sum(a!=b for a,b in zip(actual,s['words'],strict=True));samples+=1;words+=count
        if count:sample_diffs.append(dict(x=s['x'],y=s['y'],nativeWords=s['words'],portableWords=actual,differentWords=count))
    row=dict(index=i,stage=case['stage'],frame=case['frame'],draw=case['originalDrawIndex'],role=case['role'],nativeFullBytesAvailable=case['nativeFullBytesAvailable'],strictFullHashEqual=equal,nativeSha256=case['nativeSha256'],portableSha256=sha(raw),selectedDifferences=sample_diffs)
    key='/'.join(map(str,[case['stage'],case['frame'],case['originalDrawIndex']]))
    if key in full:
        original=full[key];assert raw==original;native=np.frombuffer(original,dtype='<f4').reshape(480,640,4)
        row.update(comparedFloatWords=640*480*4,differentFloatWords=0,coverageDifferences=int(((uv[:,:,3]!=0)!=(native[:,:,3]!=0)).sum()),nativeCovered=int((native[:,:,3]!=0).sum()))
        # Fit two implicated quads; identical bytes independently guarantee identical fits.
        if i in [10,21]:
            for triangle in [[0,1,2],[2,1,3]]:
                mask=(uv[:,:,3]==1)&((uv[:,:,0]+uv[:,:,1]<1-1e-4) if triangle==[0,1,2] else(uv[:,:,0]+uv[:,:,1]>1+1e-4));x=xx[mask]/640;y=yy[mask]/480;u=uv[:,:,0][mask].astype(float);v=uv[:,:,1][mask].astype(float);one=np.ones_like(x);zero=np.zeros_like(x)
                a=np.vstack((np.column_stack((x,y,one,zero,zero,zero,-u*x,-u*y)),np.column_stack((zero,zero,zero,x,y,one,-v*x,-v*y))));rhs=np.concatenate((u,v));coeff,_,rank,svals=np.linalg.lstsq(a,rhs,rcond=None);assert rank==8
                aa,bb,cc,dd,ee,ff,gg,hh=coeff;vertices=[]
                for corner in triangle:
                    cu,cv=[(0,0),(1,0),(0,1),(1,1)][corner];position=np.linalg.solve([[aa-cu*gg,bb-cu*hh],[dd-cv*gg,ee-cv*hh]],[cu-cc,cv-ff])*[640,480];vertices.append(dict(corner=corner,estimatedXY=position.tolist(),nearestSnap8XY=(np.rint(position*256)/256).tolist()))
                planes.append(dict(index=i,stage=case['stage'],frame=case['frame'],draw=case['originalDrawIndex'],triangle=triangle,NativePortableFullBytesEqual=True,vertices=vertices,samples=len(x),conditionNumber=float(svals[0]/svals[-1])))
    rows.append(row)
assert primary_equal==18 and extra_equal==2 and words==report['differentSampleWords']==17 and samples==105
assert len([r for r in rows if r['nativeFullBytesAvailable']])==4
for index,corner,expected in [(10,2,[376.453125,-63.60546875]),(21,2,[665.40234375,-179.38671875])]:
    for p in planes:
        if p['index']==index:
            v=next(v for v in p['vertices'] if v['corner']==corner);assert v['nearestSnap8XY']==expected
out=dict(diagnosticEvidenceVerified=True,productionChanged=False,completeGame=False,nativeEquivalent=False,primaryFullHashMatches=primary_equal,extraCoverageFullHashMatches=extra_equal,physicalSamplePoints=samples,differentPhysicalSampleWords=words,fullNativeControls=4,fullNativeComparedBytes=4*640*480*16,fullNativeDifferentFloatWords=0,fullNativeCoverageDifferences=0,allPortableUVBytes=23*640*480*16,rows=rows,quadPlaneFits=planes,evidence=evidence,toolSha256=sha(Path(__file__).read_bytes()),numpyVersion=np.__version__,limits='All four complete original Native controls match every byte, including all coverage alpha words and the original four missing edge pixels. Both formerly contradictory corner-grid selections now match their Native full-buffer inferred coordinates. These fits are indirect and never used as runtime corrections. Three primary full hashes still fail: two match every selected sample and one retains17 sampled word differences. Complete Native pixels for these three draws are unavailable in the frozen capture, so no full coverage or pixel-equivalence claim is made for them. Whole-game/current production unchanged; not a complete renderer repair.')
p=ROOT/'docs/porting/th14-stage-current-scaled-bias-coverage-observed-oct14.json';p.write_text(json.dumps(out,indent=2)+'\n',encoding='utf8')
print(json.dumps({k:out[k] for k in ['diagnosticEvidenceVerified','primaryFullHashMatches','extraCoverageFullHashMatches','differentPhysicalSampleWords','fullNativeComparedBytes','fullNativeDifferentFloatWords','fullNativeCoverageDifferences']}))
