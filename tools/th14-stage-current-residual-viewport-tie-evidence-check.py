"""Read-only residual viewport/subpixel analysis; no new runtime candidates.

Offline arithmetic models and indirect UV-plane estimates are not actual
uninstrumented position readback. All absolute pixel failures remain failures.
"""
import hashlib,json,struct,math
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sha=lambda b:hashlib.sha256(b).hexdigest();evidence={}
def track(p):
    b=(ROOT/p).read_bytes();evidence[p]={'bytes':len(b),'sha256':sha(b)};return b
def read(p):return json.loads(track(p))
planes=read('docs/porting/th14-stage-current-residual-uv-plane-observed-oct14.json')
critical=read('docs/porting/th14-stage-current-residual-critical-dot-observed-oct14.json')
rowdot=read('docs/porting/th14-stage-current-sequential-row-dot-assessment-oct14.json')
assert planes['diagnosticEvidenceVerified'] and critical['diagnosticEvidenceVerified'] and rowdot['decision']=='rejected_no_improvement'
assert planes['toolSha256']==sha(track('tools/th14-stage-current-residual-uv-plane-check.py'))
assert critical['toolSha256']==sha(track('tools/th14-stage-current-residual-critical-dot-check.py'))
assert rowdot['toolSha256']==sha(track('tools/th14-stage-current-sequential-row-dot-assessment.py'))
old=read('docs/porting/th14-stage-sampler-vertices-observed-oct12.json')
assert old['diagnosticEvidenceVerified'] and old['vertices']==584 and old['differentWords']==0
g=read('artifacts/th14/stage-gpu-stream-replay/sampler-vertices/generation.json')
n=read('artifacts/th14/stage-gpu-stream-replay/sampler-vertices/native.json')
inputs=read('artifacts/th14/stage-gpu-stream-replay/sampler-vertices/clip-inputs.json')
samples=track('artifacts/th14/stage-gpu-stream-replay/sampler-vertices/samples.rgba32f')
assert sha(track('artifacts/th14/stage-gpu-stream-replay/sampler-vertices/native.json'))==g['nativeSha256']
assert sha(samples)==g['sampleSha256']==n['pixelsSha256'] and len(samples)==584*16
assert g['halSourceSha256']==n['toolSha256']==sha(track('tools/th14-stage-sampler-vertices-hal.py'))
assert g['generatorSha256']==sha(track('tools/th14-stage-sampler-vertices-generator.py'))
assert g['baseSourceSha256']==sha(track('tools/th14-stage-sampler-matrix-float-hal.py'))
assert len(g['results'])==len(n['frames'])==len(inputs)==584
for i,(control,frame,input_row) in enumerate(zip(g['results'],n['frames'],inputs)):
    assert all(control[k]==v for k,v in input_row.items())
    assert control['resultWords']==frame['samples'][0]['words']==list(struct.unpack_from('<4I',samples,i*16))
    assert control['resultValues']==frame['samples'][0]['values']
    assert list(struct.unpack('<4I',struct.pack('<4f',*control['resultValues'])))==control['resultWords']
f32=lambda v:struct.unpack('<f',struct.pack('<f',v))[0]
def models(q,axis):
    a=q[axis]*(1 if axis==0 else -1);w=q[3];half=[320.0,240.0][axis]
    values={'exactDoubleRatio':(a/w+1)*half,
      'binary32RatioSeparate':f32(f32(f32(a/w)*half)+half),
      'binary32RatioFMA':f32(math.fma(f32(a/w),half,half)),
      'binary32HomogeneousDivide':f32(f32(f32(a+w)*half)/w),
      'binary32HomogeneousScaledReciprocal':f32(f32(a+w)*f32(half/w)),
      'binary32ReciprocalRatioFMA':f32(math.fma(f32(a*f32(1/w)),half,half)),
      'binary32HomogeneousViewportFMA':f32(f32(math.fma(a,half,f32(w*half)))/w)}
    return {name:{'screenValue':value,'nearestEvenSnap8':round(value*256)/256} for name,value in values.items()}
rows=[]
for c in critical['rows']:
    control=next(r for r in g['results'] if (r['stage'],r['frame'],r['draw'],r['corner'])==(c['stage'],c['frame'],c['draw'],c['vertex']))
    assert control['matrixWords']==c['computedOriginalMatrixWords']
    assert control['sourceWords']==list(struct.unpack('<4I',struct.pack('<4f',*c['submittedPosition'])))
    axis=c['criticalAxis'];native=c['indirectPlaneSnap8XY']['Native'][axis];candidate=c['indirectPlaneSnap8XY']['candidate'][axis];midpoint=(native+candidate)/2
    modes={name:models(model['clipValues'],axis) for name,model in c['models'].items()}
    constant_modes=models(control['resultValues'],axis)
    rows.append(dict(stage=c['stage'],frame=c['frame'],draw=c['draw'],vertex=c['vertex'],axis=axis,inferredNativeSnap=native,inferredPortableSnap=candidate,subpixelStep=abs(native-candidate),inferredBoundaryMidpoint=midpoint,
      separateSeqIdealDistanceToMidpoint=modes['separateSeq']['exactDoubleRatio']['screenValue']-midpoint,
      oldAuthoredConstantInputClipControlWords=control['resultWords'],oldAuthoredConstantInputClipControlValues=control['resultValues'],oldConstantControlMatchesSeparateSeqWords=control['resultWords']==c['models']['separateSeq']['clipWords'],
      offlineDotAndViewportModels=modes,authoredConstantInputViewportModels=constant_modes))
assert [r['subpixelStep'] for r in rows]==[1/256]*3
# Use every indirect triangle fit, report conditioning rather than silently
# elevating a fit to direct GPU evidence. A declared reliability subset is only
# for model diagnostics; it never filters physical equality comparisons.
fit_controls=[];summary={};included=excluded=0
for case in planes['rows']:
    for segment in case['segments']:
        for triangle in segment['triangles']:
            if not triangle['fits']:continue
            fit=triangle['fits']['Native']
            for corner in triangle['corners']:
                position=fit['vertices'][corner];vertex=segment['submittedVertices'][corner]
                control=next(r for r in g['results'] if (r['stage'],r['frame'],r['draw'],r['corner'])==(case['stage'],case['frame'],case['draw'],vertex))
                reliable=fit['conditionNumber']<=1e6 and max(abs(v) for v in position['distanceToSnap8'])<=0.0005
                for axis in [0,1]:
                    predicted=models(control['resultValues'],axis);native=position['nearestSnap8XY'][axis]
                    for name,value in predicted.items():
                        item=summary.setdefault(name,{'reliableAxisControls':0,'differentNearestEvenSnap8':0})
                        if reliable:item['reliableAxisControls']+=1;item['differentNearestEvenSnap8']+=value['nearestEvenSnap8']!=native
                    included+=reliable;excluded+=not reliable
                    fit_controls.append(dict(stage=case['stage'],frame=case['frame'],draw=case['draw'],segment=segment['segment'],triangle=triangle['corners'],vertex=vertex,axis=axis,conditionNumber=fit['conditionNumber'],inferredDistanceToSnap8=position['distanceToSnap8'],inferredNativeSnap8=native,diagnosticReliabilitySubset=reliable,models=predicted))
assert all(item['differentNearestEvenSnap8']>0 for item in summary.values())
sources=[
 dict(title='Microsoft Direct3D9 rasterization rules',url='https://learn.microsoft.com/en-us/windows/win32/direct3d9/rasterization-rules',sections=['Triangle Rasterization Rules'],support='D3D9 uses integer pixel centers and top-left coverage. The documentation allows small hardware variations; it does not prescribe the exact arithmetic of this captured driver.'),
 dict(title='Microsoft Direct3D9 viewports and clipping',url='https://learn.microsoft.com/en-us/windows/win32/direct3d9/viewports-and-clipping',sections=['Viewport Rectangle'],support='The documented viewport map includes width/height scaling, top-left Y reversal and homogeneous coordinates before conversion. This establishes the real-number map, not a specific float evaluation order.'),
 dict(title='Microsoft D3D11.3 Functional Specification',url='https://microsoft.github.io/DirectX-Specs/d3d/archive/D3D11_3_FunctionalSpec.htm',sections=['3.2.4.1','3.4.1','15.16','15.16.2'],support='On the ANGLE D3D11 side, XY positions are snapped to eight fractional bits before interpolator setup. Nearest-even conversion has a permitted 0.6 fixed-point ULP tolerance. Thus a one-grid-step vertex difference can change UV while preserving all integer sample coverage; this is an explanatory constraint, not proof of a D3D9 rounding implementation.'),
 dict(title='Khronos OpenGL ES3.0.6 specification',url='https://registry.khronos.org/OpenGL/specs/es/3.0/es_spec_3.0.pdf',sections=['2.13','2.13.1','Table6.28'],support='The specified conceptual path divides by clip W then maps NDC through viewport scale/center. Four reported subpixel bits are the ES minimum; they do not establish that this D3D11-backed capture rasterized at only four bits.'),
 dict(title='ANGLE DynamicHLSL.cpp reference revision chromium7479',url='https://chromium.googlesource.com/angle/angle/+/refs/heads/chromium/7479/src/libANGLE/renderer/d3d/DynamicHLSL.cpp',sections=['generateVertexShaderForInputLayout vertex output'],support='The reference backend passes clip XY/W to D3D11, handles clip-control Y and Z, and has a separate lower-feature-level viewport-adjust path. This revision was read as primary source context; no installed browser version or executed branch was identified from this file.'),
]
out=dict(diagnosticEvidenceVerified=True,productionChanged=False,completeGame=False,nativeEquivalent=False,remainingOriginalUVFloatWords=5292,remainingOriginalCoverageDifferences=0,rowDotRejected=True,criticalRows=rows,indirectFitViewportModelSummary=summary,indirectFitSubset=dict(includedAxisControls=included,excludedAxisControls=excluded,criteria='Condition number <=1e6 and both estimated XY distances to snap8 <=0.0005 pixel. This diagnostic subset does not mask any actual buffer comparison.'),allIndirectFitViewportControls=fit_controls,primarySourceContext=sources,evidence=evidence,toolSha256=sha(Path(__file__).read_bytes()),conclusion='All three residual Native/portable differences are consistent with one isolated strip vertex crossing an eight-fractional-bit screen-coordinate boundary. Identical color/UV row-dot controls rule out a benefit from that syntax change on this captured driver. No tested offline viewport expression uniformly predicts every retained indirect Native corner estimate; further shader algebra trials need an actual backend arithmetic measurement rather than fitted corrections.',nextMeasurement='Read the unchanged current GL shader translation with WEBGL_debug_shaders, if the owned diagnostic context exposes it, and bind installed renderer/translated-source hashes without changing shader text, transform feedback, outputs or physical comparisons. The old constant-input clip controls demonstrate authored m4x4 arithmetic, not the uninstru mented per-attribute oPos result; do not equate them.',scope='Read-only arithmetic and primary-source analysis. Original complete failures remain 5292 UV words with zero coverage differences. Indirect rational-plane fits and authored constant-input clip controls are explicitly distinguished from actual uninstrumented original or production gl_Position outputs. No runtime changes, new compiled candidates, guessed sample correction, Native coordinate/varying injection or pixel masking.')
(ROOT/'docs/porting/th14-stage-current-residual-viewport-tie-observed-oct14.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf8')
print(json.dumps({'diagnosticEvidenceVerified':True,'criticalBoundaryDistances':[r['separateSeqIdealDistanceToMidpoint'] for r in rows],'constantControlsMatchSeparateSeq':[r['oldConstantControlMatchesSeparateSeqWords'] for r in rows],'viewportModelSummary':summary,'includedAxisControls':included,'excludedAxisControls':excluded}))
