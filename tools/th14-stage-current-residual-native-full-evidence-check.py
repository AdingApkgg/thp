"""Bind newly extended Native full captures to old hashes/samples and failed UVs."""
import hashlib,json,struct
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1];evidence={}
BASE='artifacts/th14/stage-gpu-stream-replay/'
OUT='artifacts/th14/stage-current-residual-native-uv-fe406-oct14/'
CANDIDATE='artifacts/th14/stage-current-sequential-clip-scaled-bias-fe406-oct14/'
sha=lambda b:hashlib.sha256(b).hexdigest()
def track(p):
    path=Path(p);path=path if path.is_absolute() else ROOT/path;b=path.read_bytes();evidence[str(p)]={'bytes':len(b),'sha256':sha(b)};return b
def read(p):return json.loads(track(p))
pre=read(OUT+'preflight.json');completion=read(OUT+'capture-complete.json');native=read(OUT+'native.json');old=read(BASE+'sampler-uv/native.json');inputs=read(OUT+'inputs.json');prepared=read(BASE+'prepared.json')
assert pre['adapterToolSha256']==completion['toolSha256']==sha(track('tools/th14-stage-current-residual-native-full-capture.py'))
assert pre['originalHelperSha256']==sha(track(pre['originalHelperPath']))=='b3e677676867a3585185f413fe8a92b5354eaa4b182c52adcbd93204c814e207'
assert pre['adaptedHelperSha256']==native['toolSha256']==sha(track(OUT+'capture-hal.py'))
assert completion['originalNativeUVReportSha256']==sha(track(BASE+'sampler-uv/native.json'))
assert completion['newNativeReportSha256']==sha(track(OUT+'native.json'));assert completion['preflightSha256']==sha(track(OUT+'preflight.json'))
for p,b in pre['bindings'].items():assert sha(track(p))==b['sha256'],p
assert native['preparedSha256']==old['preparedSha256']==sha(track(BASE+'prepared.json'))
assert native['typesSha256']==old['typesSha256']==sha(track('tools/th14-gpu-raster-native.py'))
loaded=read(OUT+'loaded-d3d9.json');assert Path(loaded['path']).resolve()==Path('C:/Windows/System32/d3d9.dll').resolve()
assert loaded['sha256']==native['d3d9Sha256']==old['d3d9Sha256']==sha(track(loaded['path'])) and loaded['hiddenWindowStyle']==0
assert pre['compiledProbeSha256']==sha(track(OUT+'probe.pso'))==sha(track(BASE+'sampler-uv/probe.pso'))
assert track(OUT+'probe.asm')==track(BASE+'sampler-uv/probe.asm')
assert pre['selectedCases']==inputs['cases'] and len(native['frames'])==len(inputs['cases'])==3
assert native['format']==116 and native['behaviorFlags']==0x40
report=read(CANDIDATE+'uv/capture/report.json');build=read(CANDIDATE+'uv/build.json');assert report['wasmSha256']==build['wasmSha256']==sha(track(CANDIDATE+'uv/gpu.wasm'))
assert sha(track(CANDIDATE+'uv/gpu.mjs'))==build['loaderSha256']
for p,b in build['sources'].items():assert sha(track(CANDIDATE+'uv/'+p))==b['sha256']
assert not build['capturedNativeClipValuesUsed'] and not build['transformFeedback'] and not build['constantVaryings']
sample_bytes=track(OUT+'samples.rgba32f');assert sha(sample_bytes)==native['pixelsSha256'] and len(sample_bytes)==18*16
rows=[];differences=[];sum_words=sum_uv=sum_coverage=0
for i,nr in enumerate(native['frames']):
    expected=next(r for r in old['frames'] if (r['stage'],r['frame'],r['originalDrawIndex'])==(nr['stage'],nr['frame'],nr['originalDrawIndex']))
    actual=track(OUT+f'frame-{i:03d}.rgba32f');assert len(actual)==640*480*16
    assert sha(actual)==nr['fullFloatFrameSha256']==expected['fullFloatFrameSha256'] and nr['samples']==expected['samples']
    for s in expected['samples']:assert list(struct.unpack_from('<4I',actual,(s['y']*640+s['x'])*16))==s['words']
    idx=next(j for j,r in enumerate(report['reports']) if (r['stage'],r['frame'],r['originalDrawIndex'])==(nr['stage'],nr['frame'],nr['originalDrawIndex']))
    portable=track(CANDIDATE+'uv/capture/'+f'frame-{idx:03d}.rgba32f');assert sha(portable)==report['reports'][idx]['portableSha256'];assert report['reports'][idx]['nativeSha256']==sha(actual)
    n=np.frombuffer(actual,dtype='<u4').reshape(-1,4);p=np.frombuffer(portable,dtype='<u4').reshape(-1,4);nf=np.frombuffer(actual,dtype='<f4').reshape(-1,4);pf=np.frombuffer(portable,dtype='<f4').reshape(-1,4)
    nc=nf[:,3]!=0;pc=pf[:,3]!=0;common=nc&pc;mask=n!=p;indices=np.flatnonzero(mask.reshape(-1));coverage=int((nc!=pc).sum());uv=int(mask[:,0:2][common].sum());delta=float(np.max(np.abs(nf[common,0:2]-pf[common,0:2])))
    assert coverage==0 and len(indices)==uv
    first=[dict(x=int(j//4%640),y=int(j//2560),channel=int(j%4),nativeWord=int(n.flat[j]),portableWord=int(p.flat[j]),native=float(nf.flat[j]),portable=float(pf.flat[j])) for j in indices[:32]]
    for j in indices:differences.append(struct.pack('<4I',i,int(j),int(n.flat[j]),int(p.flat[j])))
    row=dict(nativeIndex=i,candidateIndex=idx,stage=nr['stage'],frame=nr['frame'],draw=nr['originalDrawIndex'],originalFullHashAndSamplesPreserved=True,nativeSha256=sha(actual),portableSha256=sha(portable),nativeCovered=int(nc.sum()),portableCovered=int(pc.sum()),coverageDifferences=coverage,differentFloatWords=int(mask.sum()),differentUVWords=uv,maxUVDelta=delta,first=first)
    sum_words+=len(indices);sum_uv+=uv;sum_coverage+=coverage;rows.append(row)
assert [r['differentFloatWords'] for r in rows]==[327,1225,3740]
binary=b''.join(differences);p=ROOT/OUT/'all-candidate-word-differences.bin'
if p.exists():assert p.read_bytes()==binary
else:p.write_bytes(binary)
track(OUT+'all-candidate-word-differences.bin')
output=dict(diagnosticEvidenceVerified=True,productionChanged=False,completeGame=False,nativeEquivalent=False,newOriginalNativeFullBytes=3*640*480*16,oldFullHashesAndSamplesPreserved=True,physicalSamplePoints=18,differentCandidateFloatWords=sum_words,differentCandidateUVWords=sum_uv,candidateCoverageDifferences=sum_coverage,rows=rows,evidence=evidence,toolSha256=sha(Path(__file__).read_bytes()),numpyVersion=np.__version__,scope='Three previously unarchived complete Native UV buffers produced by the existing own isolated D3D9 HAL hardware-vertex-processing helper, exact frozen original draw/matrix/state/vertex/texture inputs and the existing compiled own PS2 UV probe. Invisible own window/style0 and own offscreen RGBA32F target only. No retail game process, user UI control, Native-buffer reconstruction, source oracle replacement or historical overwrite. Every new full SHA256 and every physical sample equals the frozen21-draw Native record. Comparison is the declared pre-production CPU-sequential/scaled-bias candidate; actual integrated production sources need separate recapture. All failed words are retained.')
path=ROOT/'docs/porting/th14-stage-current-residual-native-full-observed-oct14.json';path.write_text(json.dumps(output,indent=2)+'\n',encoding='utf8')
print(json.dumps({k:output[k] for k in ['diagnosticEvidenceVerified','newOriginalNativeFullBytes','oldFullHashesAndSamplesPreserved','differentCandidateFloatWords','candidateCoverageDifferences']}))
