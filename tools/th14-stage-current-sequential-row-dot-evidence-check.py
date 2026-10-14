"""Independent all21 color/all23 UV verification of one explicit row-dot trial.

The immutable prior verifier is reused with declared source/path changes only;
all comparison logic and failed buffers remain intact. Three new archived
Native full controls extend the four controls that prior verifier already had.
"""
import hashlib,json,struct
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1];sha=lambda b:hashlib.sha256(b).hexdigest()
parent=ROOT/'tools/th14-stage-sequential-clip-scaled-bias-evidence-check.py'
source=parent.read_text(encoding='utf8');assert sha(parent.read_bytes())=='7a90821c4474b9bea96e7db762aa54f18a8bdab4f6d8e6e78448bb610ed79aa7'
for a,b in [('stage-current-sequential-clip-scaled-bias-fe406-oct14','stage-current-sequential-row-dot-fe406-oct14'),('tools/th14-stage-current-sequential-clip-scaled-bias-build.mjs','tools/th14-stage-current-sequential-row-dot-build.mjs'),('Sourcefe406-sequential-clip-scaled-bias-diagnostic-oct14','Sourcefe406-sequential-row-dot-diagnostic-oct14'),('tools/th14-stage-sequential-clip-scaled-bias-serve.mjs','tools/th14-stage-current-sequential-row-dot-serve.mjs'),('docs/porting/th14-stage-sequential-clip-scaled-bias-observed-oct14.json','docs/porting/th14-stage-current-sequential-row-dot-observed-oct14.json')]:
    assert a in source,a;source=source.replace(a,b)
anchor='    assert shader==expected'
assert source.count(anchor)==1
source=source.replace(anchor,"    delta=b['matrixVectorSourceDelta'];expected=expected.replace(delta['oldExpression'].encode(),delta['rowExpression'].encode())\n"+anchor)
# Shared scaled-bias arithmetic evidence remains the prior same arithmetic;
# the sole new hypothesis is dot expression, not the declared viewport path.
anchor="assert arithmetic['candidateLabel']==source['label'] and arithmetic['fullControlVertices']==92"
assert source.count(anchor)==1
source=source.replace(anchor,"assert arithmetic['candidateLabel']=='Sourcefe406-sequential-clip-scaled-bias-diagnostic-oct14' and arithmetic['fullControlVertices']==92")
source=source.replace("limits='Independent CPU sequential binary32", "limits='One explicit four-row-dot shader hypothesis, unchanged O2 flags and all other prior shader/CPP bytes; no adoption. Independent CPU sequential binary32",1)
extra="""
# Independently bind the newly frozen original HAL full3, retaining all failures.
residual='artifacts/th14/stage-current-residual-native-uv-fe406-oct14/'
residual_receipt=read('docs/porting/th14-stage-current-residual-native-full-observed-oct14.json')
residual_native=read(residual+'native.json');completion_native=read(residual+'capture-complete.json')
assert residual_receipt['diagnosticEvidenceVerified'] and residual_receipt['oldFullHashesAndSamplesPreserved']
assert completion_native['newNativeReportSha256']==sha(track(residual+'native.json'))
assert completion_native['toolSha256']==sha(track('tools/th14-stage-current-residual-native-full-capture.py'))
assert residual_receipt['toolSha256']==sha(track('tools/th14-stage-current-residual-native-full-evidence-check.py'))
extended=[];residual_differences=[]
for i,nr in enumerate(residual_native['frames']):
    idx=next(j for j,case in enumerate(cases['cases']) if (case['stage'],case['frame'],case['originalDrawIndex'])==(nr['stage'],nr['frame'],nr['originalDrawIndex']))
    row=uv_rows[idx];native_bytes=track(residual+f'frame-{i:03d}.rgba32f');portable_bytes=track(OUT+'uv/capture/'+f'frame-{idx:03d}.rgba32f')
    assert sha(native_bytes)==nr['fullFloatFrameSha256']==row['nativeSha256']==residual_receipt['rows'][i]['nativeSha256']
    n=np.frombuffer(native_bytes,'<u4').reshape(-1,4);a=np.frombuffer(portable_bytes,'<u4').reshape(-1,4);nv=n.view('<f4');av=a.view('<f4')
    nc=nv[:,3]!=0;ac=av[:,3]!=0;dif=a!=n;indices=np.flatnonzero(dif.reshape(-1));coverage=int((nc!=ac).sum())
    for j in indices:residual_differences.append(struct.pack('<4I',idx,int(j),int(n.flat[j]),int(a.flat[j])))
    extended.append(dict(index=idx,stage=nr['stage'],frame=nr['frame'],draw=nr['originalDrawIndex'],nativeSha256=sha(native_bytes),portableSha256=sha(portable_bytes),nativeCovered=int(nc.sum()),portableCovered=int(ac.sum()),coverageDifferences=coverage,allDifferentFloatWords=int(dif.sum()),differentUVOnCommonCoverage=int(dif[:,:2][nc&ac].sum()),maxUVDelta=float(np.max(np.abs(nv[nc&ac,:2]-av[nc&ac,:2]))) if np.any(nc&ac) else 0.0))
binary=b''.join(residual_differences);target=ROOT/OUT/'uv/full-native-residual-word-differences.bin'
if target.exists():assert target.read_bytes()==binary
else:target.write_bytes(binary)
track(str(target.relative_to(ROOT)).replace('\\\\','/'))
receipt['extendedNativeFullUV']=dict(cases=3,bytes=14745600,rows=extended,allDifferentFloatWords=len(residual_differences),coverageDifferences=sum(r['coverageDifferences'] for r in extended),fullBufferCountIncludingExistingFour=7,fullBufferBytesIncludingExistingFour=7*640*480*16)
prior=read('docs/porting/th14-stage-sequential-clip-scaled-bias-observed-oct14.json')
receipt['rowDotBaselineComparison']=dict(parentReport='docs/porting/th14-stage-sequential-clip-scaled-bias-observed-oct14.json',colorBefore=prior['color']['differentChannels'],colorAfter=receipt['color']['differentChannels'],sampleWordsBefore=prior['uv']['differentSampleWords'],sampleWordsAfter=receipt['uv']['differentSampleWords'],primaryFullHashesBefore=prior['uv']['primaryFullHashMatches'],primaryFullHashesAfter=receipt['uv']['primaryFullHashMatches'],nativeFull3WordsBefore=residual_receipt['differentCandidateFloatWords'],nativeFull3WordsAfter=len(residual_differences))
for mode in ['color','uv']:
    b=builds[mode];prior_build=read('artifacts/th14/stage-current-sequential-clip-scaled-bias-fe406-oct14/'+mode+'/build.json')
    assert b['flags']==prior_build['flags'] and b['parentBuildSha256']==sha(track('artifacts/th14/stage-current-sequential-clip-scaled-bias-fe406-oct14/'+mode+'/build.json'))
    for filename,binding in b['sources'].items():
        before=track('artifacts/th14/stage-current-sequential-clip-scaled-bias-fe406-oct14/'+mode+'/'+filename);actual=track(OUT+mode+'/'+filename)
        if filename=='Shaders.hpp':
            delta=b['matrixVectorSourceDelta'];assert actual==before.replace(delta['oldExpression'].encode(),delta['rowExpression'].encode())
        else:assert actual==before
receipt['productionAdopted']=False
receipt['limits']+=' Extended independently frozen original full3 Native bytes are compared word by word as well, keeping every residual difference; row-dot changes are not production adopted.'
receipt['evidence']=evidence
"""
anchor="path=ROOT/'docs/porting/th14-stage-current-sequential-row-dot-observed-oct14.json'"
assert source.count(anchor)==1;source=source.replace(anchor,extra+'\n'+anchor)
namespace={'__file__':str(Path(__file__)),'__name__':'__main__'}
exec(compile(source,str(parent),'exec'),namespace)
receipt=namespace['receipt']
print(json.dumps({'extendedNativeFullUV':receipt['extendedNativeFullUV'],'rowDotBaselineComparison':receipt['rowDotBaselineComparison'],'productionAdopted':False}))
