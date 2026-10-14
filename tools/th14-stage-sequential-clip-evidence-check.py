"""Recompute sequential CPU clip candidate color/UV full-buffer evidence.

No Native process is started. Original D3D9 references remain immutable. Native
full UV bytes exist for four cases; the other 19 primary draws have full-frame
hashes plus physical sample bytes, which are reported as that narrower evidence.
"""
import hashlib,json,struct
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
BASE='artifacts/th14/stage-gpu-stream-replay/'
OUT='artifacts/th14/stage-current-sequential-clip-fe406-oct14/'
evidence={}
sha=lambda b:hashlib.sha256(b).hexdigest()
def track(p):
    b=(ROOT/p).read_bytes();evidence[p]={'bytes':len(b),'sha256':sha(b)};return b
def read(p):return json.loads(track(p))
def assert_hash(p,h):assert sha(track(p))==h,p
source=read(OUT+'sources.json')
assert source['toolSha256']==sha(track('tools/th14-stage-current-sequential-clip-build.mjs'))
for p,h in source['snapshots'].items():assert_hash(OUT+'source/'+p,h)
# Source snapshots bind history even if production changes after this capture.
for p,binding in source['sourceBindings'].items():
    name='fixture.cpp' if p.endswith('th14-stage-gpu-stream-fixture.cpp') else p.rsplit('/',1)[1]
    frozen=track(OUT+'source/'+name)
    if name=='fixture.cpp':
        # Only the fixture's include path is relocated for the private build.
        frozen=frozen.replace(b'"Renderer.hpp"',b'"../../../portable/sdl/Renderer.hpp"',1)
    assert len(frozen)==binding['bytes'] and sha(frozen)==binding['sha256'],p
prepared=read(BASE+'prepared.json');native=read(BASE+'native.json');native_color=track(BASE+'native.bgra')
assert native['preparedSha256']==sha(track(BASE+'prepared.json'))
assert native['pixelsSha256']==sha(native_color) and native['bytes']==len(native_color)==21*640*480*4
assert_hash('tools/th14-stage-gpu-stream-hal.py',native['toolSha256'])
assert_hash('tools/th14-gpu-raster-native.py',native['typesSha256'])
capture_path='artifacts/th14/stage-gpu-stream-with-initial/'
capture=read(capture_path+'native.json')
assert capture['passed'] and prepared['captureSha256']==sha(track(capture_path+'native.json'))
assert capture['executableSha256']==sha(Path('H:/Games/th/14/th14.exe').read_bytes())
for k,p in [('toolSha256','tools/th14-stage-gpu-stream-native.py'),('rendererSha256','tools/th14-native-stage-gpu-stream.py'),('loaderSha256','tools/th14-native-stage-fpu-resource-loader.py'),('parserSha256','tools/th-anm-script-dump.py')]:assert_hash(p,capture[k])
assert_hash('tools/th14-stage-gpu-stream-input.py',prepared['toolSha256'])
assert len(capture['samples'])==len(prepared['frames'])==len(native['frames'])==21
for s,f in zip(capture['samples'],prepared['frames'],strict=True):
    original=read(capture_path+s['file']);assert evidence[capture_path+s['file']]['sha256']==s['sha256']==f['capturedSha256']
    assert (original['stage'],original['frame'])==(f['stage'],f['frame'])
    words=struct.pack('<'+str(len(original['rawSubmissionWords']))+'I',*original['rawSubmissionWords'])
    assert sha(words)==f['submissionSha256']==original['summary']['sha256']
assert sum(f['directDraws'] for f in prepared['frames'])==1005
for t in prepared['textures']:assert_hash(BASE+t['file'],t['sha256'])
uv_native=read(BASE+'sampler-uv/native.json');uv_samples=track(BASE+'sampler-uv/samples.rgba32f')
assert sha(uv_samples)==uv_native['pixelsSha256'] and len(uv_samples)==102*16
assert uv_native['preparedSha256']==native['preparedSha256']
assert_hash('tools/th14-stage-sampler-uv-hal.py',uv_native['toolSha256'])
ug=read(BASE+'sampler-uv/generation.json')
for k,p in [('generatorSha256','tools/th14-stage-sampler-uv-native.py'),('baseSourceSha256','tools/th14-stage-sampler-raw-hal.py'),('halSourceSha256','tools/th14-stage-sampler-uv-hal.py'),('inputsSha256',BASE+'sampler-uv/inputs.json'),('nativeSha256',BASE+'sampler-uv/native.json'),('assemblySha256',BASE+'sampler-uv/probe.asm'),('shaderSha256',BASE+'sampler-uv/probe.pso')]:assert_hash(p,ug[k])
assert len(uv_native['frames'])==21
assert uv_samples==b''.join(struct.pack('<4I',*s['words']) for r in uv_native['frames'] for s in r['samples'])
cases=read(OUT+'uv-cases.json');assert len(cases['cases'])==23
assert cases['nativeUVReportSha256']==sha(track(cases['nativeUVReportPath']))
for case,nr in zip(cases['cases'][:21],uv_native['frames'],strict=True):
    assert case['role']=='selected21' and case['samples']==nr['samples']
    assert (case['stage'],case['frame'],case['originalDrawIndex'],case['nativeSha256'])==(nr['stage'],nr['frame'],nr['originalDrawIndex'],nr['fullFloatFrameSha256'])
full={}
for binding in cases['fullBindings']:
    raw=track(binding['path']);selected=raw[binding['offset']:binding['offset']+binding['bytes']]
    assert sha(selected)==binding['sha256'];nr=read(binding['reportPath']);assert sha(track(binding['reportPath']))==binding['reportSha256']
    assert nr['preparedSha256']==native['preparedSha256']
    if '/world-uv/' in binding['path']:assert_hash('tools/th14-stage-world-uv-hal.py',nr['toolSha256'])
    elif '/sampler-uv-worst/' in binding['path']:assert_hash('tools/th14-stage-sampler-uv-worst-hal.py',nr['toolSha256'])
    else:assert_hash('tools/th14-stage-sampler-uv-strip-hal.py',nr['toolSha256'])
    r=next(r for r in nr['frames'] if '/'.join(map(str,[r['stage'],r['frame'],r['originalDrawIndex']]))==binding['key'])
    assert binding['sha256']==r.get('fullFloatFrameSha256',r.get('sha256'))
    full[binding['key']]=selected
assert len(full)==4
track('tools/th14-stage-sequential-clip-serve.mjs');track('tools/th14-stage-sequential-clip.html')
builds={};reports={}
for mode in ['color','uv']:
    prefix=OUT+mode+'/'
    b=read(prefix+'build.json');r=read(prefix+'capture/report.json');builds[mode]=b;reports[mode]=r
    assert b['sourceBindings']==r['sourceBindings']==source['sourceBindings']
    assert b['toolSha256']==source['toolSha256'] and b['vertexSourceChanged']==r['vertexSourceChanged']==True
    assert r['backendVersion']==10 and r['mode']==mode and r['fragmentUVOverride']==(mode=='uv')
    assert r['wasmSha256']==b['wasmSha256']==sha(track(prefix+'gpu.wasm'));assert_hash(prefix+'gpu.mjs',b['loaderSha256'])
    for p,binding in b['sources'].items():
        raw=track(prefix+p);assert len(raw)==binding['bytes'] and sha(raw)==binding['sha256']
    # Candidate derivation uses captured matrices as normal draw inputs only.
    assert b['diagnosticOnly'] and not b['completeGame'] and not b['nativeEquivalent']
    for key in ['preservesFogEye','preservesCurrentDepth16']:assert b[key]
    for key in ['worldViewportSnap','transformFeedback','constantVaryings','capturedNativeClipValuesUsed']:assert not b[key]
    assert '-O2' in b['flags'] and '-fno-fast-math' in b['flags'] and '-ffp-contract=off' in b['flags']
    shader=track(prefix+'Shaders.hpp');frozen=track(OUT+'source/Shaders.hpp')
    expected=frozen.replace(b'layout(location=8) in vec4 instanceFactor;',b'layout(location=8) in vec4 instanceFactor;\nlayout(location=9) in vec4 instanceClip0;\nlayout(location=10) in vec4 instanceClip1;\nlayout(location=11) in vec4 instanceClip2;\nlayout(location=12) in vec4 instanceClip3;')
    expected=expected.replace(b'uniform mat4 world,view,projection,textureMatrix;',b'uniform mat4 world,view,projection,textureMatrix,clipMatrix;')
    expected=expected.replace(b'gl_Position=projection*eye;',b'mat4 composed=instanced?mat4(instanceClip0,instanceClip1,instanceClip2,instanceClip3):clipMatrix;gl_Position=composed*vec4(position.xyz,1.0);')
    if mode=='uv':expected=expected.replace(b'outColor=c;',b'outColor=vec4(vUV,0.0,1.0);')
    assert shader==expected
    assert b'vec4 eye=view*model*vec4(position.xyz,1.0);' in shader
    renderer=track(prefix+'Renderer.cpp');helper=track(prefix+'ClipComposition.hpp')
    assert b'capturedClip' not in renderer+helper
    for anchor in [b'volatile float product=a[row]*b[col*4];volatile float sum=product;',b'product=a[k*4+row]*b[col*4+k];sum=sum+product;',b'diagnostic_multiply(projection,diagnostic_multiply(view,world))']:assert anchor in helper
    for anchor in [b'const u32 records=instanceSize/68;std::vector<u8> expanded(records*132);',
        b'std::memcpy(model.data(),input+record*68,64);',
        b'auto clip=diagnostic_clip(model,d.matrix[1],d.matrix[2]);',
        b'std::memcpy(expanded.data()+record*132,input+record*68,68);',
        b'std::memcpy(expanded.data()+record*132+68,clip.data(),64);',
        b'glVertexAttribPointer(4+i,4,GL_FLOAT,false,132,reinterpret_cast<void*>(b+i*16))',
        b'glVertexAttribPointer(9+i,4,GL_FLOAT,false,132,reinterpret_cast<void*>(b+68+i*16))',
        b'glVertexAttribPointer(8,4,GL_UNSIGNED_BYTE,true,132,reinterpret_cast<void*>(b+64))',
        b'glDrawArraysInstanced(mode,0,n,instanceSize/68);']:assert anchor in renderer
    # Existing fixture still queues draw calls; no added forced flush occurs.
    assert track(prefix+'fixture.cpp')==track('artifacts/th14/stage-current-graphics-fe406-oct14/'+mode+'/fixture.cpp')
    diag=r['clipDiagnostics'];assert set(diag)=={'regularMatrices','instanceBatches','instanceMatrices','maxVertexAttribs'}
    assert diag['maxVertexAttribs']>=13
    for key in ['regularMatrices','instanceBatches','instanceMatrices']:assert isinstance(diag[key],int) and diag[key]>=0
    assert diag['instanceMatrices']>=2*diag['instanceBatches']
    assert r['gpu']['clipControlAvailable'] and r['gpu']['clipDepthMode']==r['gpu']['clipZeroToOne']
    assert r['gpu']['clipOrigin']==r['gpu']['clipLowerLeft']
    assert 'Direct3D11' in r['gpu']['renderer']
assert reports['color']['gpu']==reports['uv']['gpu']
color_rows=[];different=maximum=exact=0;color_combined=bytearray()
for i,(nr,observed) in enumerate(zip(native['frames'],reports['color']['reports'],strict=True)):
    p=OUT+'color/capture/frame-'+f'{i:03d}'+'.bgra';actual=track(p);expected=native_color[nr['offset']:nr['offset']+nr['bytes']]
    assert len(actual)==nr['bytes'];assert sha(actual)==observed['portableSha256'];assert sha(expected)==nr['sha256']==observed['nativeSha256']
    assert (observed['stage'],observed['frame'])==(nr['stage'],nr['frame']);color_combined.extend(actual)
    a=np.frombuffer(actual,dtype=np.uint8);n=np.frombuffer(expected,dtype=np.uint8);indices=np.flatnonzero(a!=n);count=len(indices);delta=int(np.max(np.abs(a.astype(np.int16)-n.astype(np.int16))))
    first=[dict(x=int(j//4%640),y=int(j//2560),channel=int(j%4),portable=int(a[j]),native=int(n[j])) for j in indices[:32]]
    assert count==observed['differentChannels'] and delta==observed['maxDelta'] and first==observed['first']
    equal=count==0;assert equal==observed['strictFullBufferHashEqual'];exact+=equal;different+=count;maximum=max(maximum,delta)
    color_rows.append(dict(index=i,stage=nr['stage'],frame=nr['frame'],differentChannels=count,maxDelta=delta,strictPixelsEqual=equal,portableSha256=sha(actual),nativeSha256=sha(expected),first=first))
assert len(color_rows)==21 and different==reports['color']['differentChannels'] and maximum==reports['color']['maxDelta'] and exact==reports['color']['exactFullBuffers']
uv_rows=[];sample_difference=primary_exact=control_exact=0;uv_differences=[]
for i,(case,observed) in enumerate(zip(cases['cases'],reports['uv']['reports'],strict=True)):
    p=OUT+'uv/capture/frame-'+f'{i:03d}'+'.rgba32f';actual=track(p);assert len(actual)==640*480*16 and sha(actual)==observed['portableSha256']
    assert (case['stage'],case['frame'],case['originalDrawIndex'],case['role'],case['nativeSha256'])==(observed['stage'],observed['frame'],observed['originalDrawIndex'],observed['role'],observed['nativeSha256'])
    a=np.frombuffer(actual,dtype='<u4').reshape(-1,4);av=np.frombuffer(actual,dtype='<f4').reshape(-1,4);covered=av[:,3]!=0
    assert int(covered.sum())==observed['portableCovered'];samples=[]
    for native_sample,s in zip(case['samples'],observed['samples'],strict=True):
        at=native_sample['y']*640+native_sample['x'];ws=list(map(int,a[at]));values=list(map(float,av[at]));count=sum(x!=y for x,y in zip(ws,native_sample['words'],strict=True))
        assert {k:s[k] for k in native_sample}==native_sample and s['portableWords']==ws and s['portableValues']==values and s['differentWords']==count
        sample_difference+=count;samples.append(dict(x=s['x'],y=s['y'],differentWords=count,nativeWords=native_sample['words'],portableWords=ws))
    equal=sha(actual)==case['nativeSha256'];assert equal==observed['strictFullBufferHashEqual']
    if case['role']=='selected21':primary_exact+=equal
    else:control_exact+=equal
    row=dict(index=i,stage=case['stage'],frame=case['frame'],draw=case['originalDrawIndex'],role=case['role'],strictFullBufferHashEqual=equal,portableSha256=sha(actual),nativeSha256=case['nativeSha256'],portableCovered=int(covered.sum()),samples=samples,nativeFullBytesAvailable=case['nativeFullBytesAvailable'])
    key='/'.join(map(str,[case['stage'],case['frame'],case['originalDrawIndex']]))
    if key in full:
        nr=full[key];assert sha(nr)==case['nativeSha256'];n=np.frombuffer(nr,dtype='<u4').reshape(-1,4);nv=np.frombuffer(nr,dtype='<f4').reshape(-1,4);nc=nv[:,3]!=0
        dif=a!=n;indices=np.flatnonzero(dif.reshape(-1));coverage=int((covered!=nc).sum());uv=int(dif[:,0:2][covered&nc].sum());delta=float(np.max(np.abs(av[covered&nc,0:2]-nv[covered&nc,0:2]))) if np.any(covered&nc) else 0.0
        first=[dict(x=int(j//4%640),y=int(j//2560),channel=int(j%4),native=float(nv.flat[j]),portable=float(av.flat[j])) for j in indices[:32]]
        assert coverage==observed['coverageDifferences'] and uv==observed['differentUVOnCommonCoverage'] and delta==observed['maxUVDelta'] and first==observed['first'] and int(nc.sum())==observed['nativeCovered']
        for j in indices:uv_differences.append(struct.pack('<4I',i,int(j),int(n.flat[j]),int(a.flat[j])))
        row.update(nativeCovered=int(nc.sum()),coverageDifferences=coverage,differentUVOnCommonCoverage=uv,allDifferentFloatWords=int(dif.sum()),maxUVDelta=delta,first=first)
    uv_rows.append(row)
assert sample_difference==reports['uv']['differentSampleWords']
assert primary_exact+control_exact==reports['uv']['exactFullBuffers']
diff_bytes=b''.join(uv_differences);diff_path=ROOT/OUT/'uv/full-native-word-differences.bin'
if diff_path.exists():assert diff_path.read_bytes()==diff_bytes
else:diff_path.write_bytes(diff_bytes)
track(str(diff_path.relative_to(ROOT)).replace('\\','/'))
color_combined_path=ROOT/OUT/'color/portable.bgra'
if color_combined_path.exists():assert color_combined_path.read_bytes()==color_combined
else:color_combined_path.write_bytes(color_combined)
track(str(color_combined_path.relative_to(ROOT)).replace('\\','/'))
receipt=dict(diagnosticEvidenceVerified=True,completeGame=False,nativeEquivalent=False,productionChanged=False,label='Sourcefe406-sequential-clip-diagnostic-oct14')
receipt.update(sourceBindings=source['sourceBindings'],gpu=reports['color']['gpu'],clipDiagnostics={mode:reports[mode]['clipDiagnostics'] for mode in ['color','uv']},compilerFlags={mode:builds[mode]['flags'] for mode in ['color','uv']},color=dict(frames=21,directDraws=1005,pixelBytes=len(color_combined),exactFrames=exact,differentChannels=different,maxDelta=maximum,strictPixelsEqual=exact==21,rows=color_rows),uv=dict(primaryDraws=21,extraCoverageControls=2,portableFullBufferBytes=23*640*480*16,nativeFullBufferCases=4,primaryFullHashMatches=primary_exact,extraControlFullHashMatches=control_exact,physicalSamplePoints=105,physicalSampleFloatWords=420,differentSampleWords=sample_difference,allNativeFullCaseWordDifferences=len(uv_differences),strictFullBufferHashesEqual=primary_exact==21 and control_exact==2,rows=uv_rows),evidence=evidence,toolSha256=sha(Path(__file__).read_bytes()),numpyVersion=np.__version__,limits='Independent CPU sequential binary32 projection*(view*world) candidate changes only the private clip path. Per-instance derived clip matrices use each original world; original model/factor and eye/fog paths remain. Original D16, clip control and no world snap retain current semantics. GLSL matrix-vector operation remains GPU arithmetic, not a captured Native result or forced constant varying. UV fragment output alone changes and alpha/depth/blend/fog disable only in UV isolation. All 21 original draw hashes and sample words are independent Native references. Complete Native pixels exist for two primary draws and two additional controls; other19 full per-pixel comparisons are unavailable. Every portable buffer and every Native-available difference is retained. Hidden HAL references, driver-specific diagnostics, no production or whole-game equivalence.')
baseline=read('docs/porting/th14-stage-current-graphics-observed-oct14.json')
assert baseline['diagnosticEvidenceVerified'] and baseline['sourceBindings']==source['sourceBindings']
base_uv={str((r['stage'],r['frame'],r['draw'])):r for r in baseline['uv']['rows']}
base_color={str((r['stage'],r['frame'])):r for r in baseline['color']['rows']}
receipt['baselineComparison']={
 'baselineReport':'docs/porting/th14-stage-current-graphics-observed-oct14.json',
 'colorDifferentChannelsBefore':baseline['color']['differentChannels'],
 'colorDifferentChannelsAfter':different,
 'colorRows':[dict(stage=r['stage'],frame=r['frame'],before=base_color[str((r['stage'],r['frame']))]['differentChannels'],after=r['differentChannels']) for r in color_rows],
 'primaryFullHashMatchesBefore':baseline['uv']['primaryFullHashMatches'],
 'primaryFullHashMatchesAfter':primary_exact,
 'sampleWordDifferencesBefore':baseline['uv']['differentSampleWords'],
 'sampleWordDifferencesAfter':sample_difference,
 'allFullNativeWordDifferencesBefore':baseline['uv']['allNativeFullCaseWordDifferences'],
 'allFullNativeWordDifferencesAfter':len(uv_differences),
 'fullNativeRows':[dict(stage=r['stage'],frame=r['frame'],draw=r['draw'],
   coverageBefore=base_uv[str((r['stage'],r['frame'],r['draw']))]['coverageDifferences'],
   coverageAfter=r['coverageDifferences'],
   allFloatWordsBefore=base_uv[str((r['stage'],r['frame'],r['draw']))]['allDifferentFloatWords'],
   allFloatWordsAfter=r['allDifferentFloatWords']) for r in uv_rows if 'allDifferentFloatWords' in r]
}
path=ROOT/'docs/porting/th14-stage-sequential-clip-observed-oct14.json';path.write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf8')
completion=dict(reportSha256=sha(path.read_bytes()),colorReportSha256=sha(track(OUT+'color/capture/report.json')),uvReportSha256=sha(track(OUT+'uv/capture/report.json')),verifierSha256=receipt['toolSha256'])
done=ROOT/OUT/'capture-complete.json'
if done.exists():assert json.loads(done.read_text())==completion
else:done.write_text(json.dumps(completion,indent=2)+'\n')
print(json.dumps({'diagnosticEvidenceVerified':True,'color':{k:receipt['color'][k] for k in ['exactFrames','differentChannels','maxDelta']},'uv':{k:receipt['uv'][k] for k in ['primaryFullHashMatches','extraControlFullHashMatches','differentSampleWords','allNativeFullCaseWordDifferences']},'clipDiagnostics':receipt['clipDiagnostics'],'gpu':receipt['gpu']}))


