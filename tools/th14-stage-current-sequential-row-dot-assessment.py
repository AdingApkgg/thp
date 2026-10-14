"""Reject no-improvement row-dot trial using every current physical buffer."""
import hashlib,json
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1];sha=lambda b:hashlib.sha256(b).hexdigest();evidence={}
def track(p):
    b=(ROOT/p).read_bytes();evidence[p]={'bytes':len(b),'sha256':sha(b)};return b
def read(p):return json.loads(track(p))
DOT='artifacts/th14/stage-current-sequential-row-dot-fe406-oct14/'
NO_GUARD='artifacts/th14/stage-production-clip-no-finite-guard-oct14/'
BEFORE='artifacts/th14/stage-current-sequential-clip-scaled-bias-fe406-oct14/'
proof=read('docs/porting/th14-stage-current-sequential-row-dot-observed-oct14.json')
other=read('docs/porting/th14-stage-production-clip-no-finite-guard-observed-oct14.json')
assert proof['diagnosticEvidenceVerified'] and other['diagnosticEvidenceVerified']
assert proof['toolSha256']==sha(track('tools/th14-stage-current-sequential-row-dot-evidence-check.py'))
completion=read(DOT+'capture-complete.json');assert completion['reportSha256']==sha(track('docs/porting/th14-stage-current-sequential-row-dot-observed-oct14.json'))
rows=[];totals={}
for mode,count,ext,dtype in [('color',21,'bgra','u1'),('uv',23,'rgba32f','<u4')]:
    reports={prefix:read(prefix+mode+'/capture/report.json') for prefix in [DOT,NO_GUARD,BEFORE]}
    for prefix in [DOT,NO_GUARD,BEFORE]:
        build=read(prefix+mode+'/build.json');assert build['wasmSha256']==reports[prefix]['wasmSha256']==sha(track(prefix+mode+'/gpu.wasm'))
        for file,binding in build['sources'].items():assert sha(track(prefix+mode+'/'+file))==binding['sha256']
    total=0;bytes_compared=0
    for i in range(count):
        data={prefix:track(prefix+mode+'/capture/'+f'frame-{i:03d}.{ext}') for prefix in [DOT,NO_GUARD,BEFORE]}
        for prefix in data:assert sha(data[prefix])==reports[prefix]['reports'][i]['portableSha256']
        dot=np.frombuffer(data[DOT],dtype);current=np.frombuffer(data[NO_GUARD],dtype);before=np.frombuffer(data[BEFORE],dtype)
        different=int((dot!=current).sum());prior_different=int((dot!=before).sum());assert different==prior_different==0
        bytes_compared+=len(data[DOT]);total+=different
        rows.append(dict(mode=mode,index=i,stage=reports[DOT]['reports'][i]['stage'],frame=reports[DOT]['reports'][i]['frame'],bytes=len(data[DOT]),rowDotSha256=sha(data[DOT]),currentNoFiniteSha256=sha(data[NO_GUARD]),priorScaledBiasSha256=sha(data[BEFORE]),differentWordsOrChannels=different,priorDifferentWordsOrChannels=prior_different))
    totals[mode]=dict(frames=count,bytes=bytes_compared,differentWordsOrChannels=total)
output=dict(diagnosticEvidenceVerified=True,productionChanged=False,productionAdopted=False,completeGame=False,nativeEquivalent=False,decision='rejected_no_improvement',totals=totals,rows=rows,colorNativeDifferences=proof['color']['differentChannels'],remainingOriginalUVFloatWords=proof['extendedNativeFullUV']['allDifferentFloatWords'],remainingOriginalCoverageDifferences=proof['extendedNativeFullUV']['coverageDifferences'],evidence=evidence,toolSha256=sha(Path(__file__).read_bytes()),scope='Every 21 complete color and 23 complete UV row-dot trial buffer equals both the immutable O2 scaled-bias candidate and the independent fresh current-production no-finite-guard control. Explicit GLSL row dot gives no change on this tested ANGLE/D3D11 driver. Retain all 880 original color channel failures, 17 physical UV sample-word failures, and 5292 complete residual original UV-word failures; no masking or production adoption. Further algebra candidates are not justified by this result alone.')
(ROOT/'docs/porting/th14-stage-current-sequential-row-dot-assessment-oct14.json').write_text(json.dumps(output,indent=2)+'\n',encoding='utf8')
print(json.dumps({'decision':output['decision'],'totals':totals,'remainingOriginalUVFloatWords':output['remainingOriginalUVFloatWords']}))
