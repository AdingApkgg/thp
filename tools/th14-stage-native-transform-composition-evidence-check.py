"""Audit preserved Native HAL matrix controls without running Native or editing C++.

The authored VS2 control is compared against independent FFP UV buffers. Its
clip output has no explicit viewport snap; both still use the Native rasterizer.
CPU dot products are bounded mathematical controls, not GPU source-order proof.
"""
import hashlib,json,struct
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
BASE='artifacts/th14/stage-gpu-stream-replay/'
OUT='artifacts/th14/stage-native-transform-composition-verified-oct14/'
evidence={}
sha=lambda b:hashlib.sha256(b).hexdigest()
def track(p):
    b=(ROOT/p).read_bytes();evidence[p]=dict(bytes=len(b),sha256=sha(b));return b
def read(p):return json.loads(track(p))
def bound(p,h):assert sha(track(p))==h,p
def f32(x):return struct.unpack('<f',struct.pack('<f',x))[0]
def floats(words):return [struct.unpack('<f',struct.pack('<I',w))[0] for w in words]
def words(values):return [struct.unpack('<I',struct.pack('<f',v))[0] for v in values]
def mul(a,b):
    result=[]
    for col in range(4):
        for row in range(4):
            v=f32(a[row]*b[col*4])
            for k in range(1,4):v=f32(v+f32(a[k*4+row]*b[col*4+k]))
            result.append(v)
    return result
def dot(a,v):
    out=[]
    for row in range(4):
        s=f32(a[row]*v[0])
        for k in range(1,4):s=f32(s+f32(a[k*4+row]*v[k]))
        out.append(s)
    return out
baseline=read('docs/porting/th14-stage-current-graphics-observed-oct14.json')
assert baseline['diagnosticEvidenceVerified'] and not baseline['productionChanged']
prepared=read(BASE+'prepared.json')
assert sha(track(BASE+'prepared.json'))==baseline['evidence'][BASE+'prepared.json']['sha256']
reference=track(BASE+'world-uv/native.rgba32f');ffp=read(BASE+'world-uv/native.json')
assert len(reference)==9830400 and sha(reference)==ffp['pixelsSha256']
assert ffp['preparedSha256']==sha(track(BASE+'prepared.json'))
bound('tools/th14-stage-world-uv-hal.py',ffp['toolSha256'])
mode_rows=[];all_differences=[]
for mode_index,mode in enumerate(['float','pair','double','viewproj']):
    prefix=BASE+'world-uv-native-'+mode+'/'
    generation=read(prefix+'generation.json');native=read(prefix+'native.json');raw=track(prefix+'native.rgba32f')
    assert generation['mode']==mode and generation['ffpPixelsSha256']==sha(reference)
    assert generation['nativePixelsSha256']==native['pixelsSha256']==sha(raw)
    assert native['preparedSha256']==ffp['preparedSha256'] and len(raw)==len(reference)
    bound('tools/th14-stage-world-uv-matrix-native.py',generation['generatorSha256'])
    bound('tools/th14-stage-world-uv-hal.py',generation['baseSourceSha256'])
    hal='tools/th14-stage-world-uv-matrix-'+mode+'-hal.py';bound(hal,generation['halSourceSha256'])
    assert native['toolSha256']==generation['halSourceSha256']
    assembly=track(prefix+'probe.vs.asm');track(prefix+'probe.vso')
    assert assembly==b'vs_2_0\ndcl_position v0\ndcl_texcoord v1\nm4x4 oPos,v0,c0\nmov oT0,v1\n'
    a=np.frombuffer(raw,dtype='<u4');n=np.frombuffer(reference,dtype='<u4')
    different=np.flatnonzero(a!=n)
    if len(different):
        all_differences.append(np.column_stack([np.full(len(different),mode_index,dtype='<u4'),different.astype('<u4'),n[different],a[different]]).astype('<u4').tobytes())
    rows=[]
    for expected,row in zip(generation['differences'],native['frames'],strict=True):
        assert row['frame'] in (599,1199) and row['stage']==3
        start=row['offset']//4;end=start+row['bytes']//4
        aa=a[start:end].reshape(-1,4);nn=n[start:end].reshape(-1,4)
        observed=dict(frame=row['frame'],differentFloatWords=int((aa!=nn).sum()),coverageDifferences=int((aa[:,3]!=nn[:,3]).sum()))
        assert observed==expected
        assert sha(raw[row['offset']:row['offset']+row['bytes']])==row['sha256']
        rows.append(observed)
    mode_rows.append(dict(mode=mode,explicitVertexViewportSnap=False,authoredVertexAssembly=assembly.decode(),rows=rows,fullFloatWords=int(len(a)),strictFullBufferEqual=not len(different)))
assert mode_rows[0]['strictFullBufferEqual']
generation=read(BASE+'clip-dot-native-matrix/generation.json')
assert generation['mode']=='matrix' and len(generation['results'])==8
for p,k in [('tools/th14-stage-clip-dot-native.py','generatorSha256'),('tools/th14-stage-world-uv-matrix-float-hal.py','baseSourceSha256'),('tools/th14-stage-clip-dot-matrix-hal.py','halSourceSha256')]:bound(p,generation[k])
bound(BASE+'clip-dot-native-matrix/native.json',generation['nativeSha256'])
dot_native=read(BASE+'clip-dot-native-matrix/native.json');dot_inputs=read(BASE+'clip-dot-native-matrix/inputs.json')
dot_pixels=track(BASE+'clip-dot-native-matrix/native.rgba32f')
assert sha(dot_pixels)==generation['pixelsSha256']==dot_native['pixelsSha256'] and len(dot_pixels)==131072
assert dot_native['width']==dot_native['height']==32
assert len(dot_native['frames'])==len(dot_inputs)==8
for nr,gr,inp in zip(dot_native['frames'],generation['results'],dot_inputs,strict=True):
    raw=dot_pixels[nr['offset']:nr['offset']+nr['bytes']]
    assert sha(raw)==nr['sha256']
    assert list(struct.unpack_from('<4I',raw,(16*32+16)*16))==gr['resultWords']
    assert inp['sourceWords']==gr['sourceWords'] and inp['matrixWords']==gr['matrixWords']
    assert (nr['stage'],nr['frame'],nr['corner'])==(gr['stage'],gr['frame'],gr['corner'])
for file in ['probe.vs.asm','probe.vso','probe.asm','probe.pso']:track(BASE+'clip-dot-native-matrix/'+file)
controlled=[];cpu_rows=[]
def draw_inputs(stage,frame,draw_index):
    frame=next(f for f in prepared['frames'] if (f['stage'],f['frame'])==(stage,frame));matrices={};index=0
    for command in frame['initialState']+frame['commands']:
        if command['kind']=='transform':matrices[command['key']]=floats(command['words'])
        if command['kind']=='draw':
            if index==draw_index:return matrices,command
            index+=1
    raise AssertionError('Missing original draw')
for result in generation['results']:
    stage,frame,corner=result['stage'],result['frame'],result['corner'];draw_index=68 if frame==599 else 45
    m,c=draw_inputs(stage,frame,draw_index)
    assert c['stride']==20 and c['count']==2
    vertex=floats(c['words'][corner*5:corner*5+3])+[1.0]
    combined=mul(m[3],mul(m[2],m[256]));actual=dot(combined,vertex)
    assert words(vertex)==result['sourceWords'] and words(combined)==result['matrixWords']
    assert words(actual)==result['resultWords'] and actual==result['resultValues']
    controlled.append(dict(stage=stage,frame=frame,draw=draw_index,corner=corner,sourceWords=result['sourceWords'],computedMatrixWords=words(combined),cpuDotWords=words(actual),nativeControlledDotWords=result['resultWords'],differentWords=0))
for stage,frame,draw_index in [(3,599,11),(3,599,68),(3,1199,45)]:
    m,c=draw_inputs(stage,frame,draw_index);vw=mul(m[2],m[256]);combined=mul(m[3],vw);rows=[]
    for corner in range(4):
        vertex=floats(c['words'][corner*5:corner*5+3])+[1.0]
        combined_words=words(dot(combined,vertex));nested_words=words(dot(m[3],dot(vw,vertex)))
        rows.append(dict(corner=corner,sequentialCombinedWords=combined_words,nestedModelWords=nested_words,differentWords=sum(a!=b for a,b in zip(combined_words,nested_words,strict=True))))
    cpu_rows.append(dict(stage=stage,frame=frame,draw=draw_index,differentWords=sum(r['differentWords'] for r in rows),rows=rows))
out=ROOT/OUT;out.mkdir(parents=True,exist_ok=True);different_bytes=b''.join(all_differences);diff_path=OUT+'all-native-variant-word-differences.bin'
if (ROOT/diff_path).exists():assert (ROOT/diff_path).read_bytes()==different_bytes
else:(ROOT/diff_path).write_bytes(different_bytes)
track(diff_path)
receipt=dict(diagnosticEvidenceVerified=True,completeGame=False,nativeEquivalent=False,productionChanged=False,
 originalFFPFullBytes=len(reference),originalFFPFullFloatWords=len(reference)//4,matrixVariants=mode_rows,
 nativeAuthoredDotCorners=8,nativeAuthoredDotWords=32,controlledDotWordDifferences=0,controlledDotRows=controlled,
 cpuMathematicalModels=cpu_rows,allVariantDifferencesPath=diff_path,allVariantDifferentWords=len(different_bytes)//16,
 sourceBindings=baseline['sourceBindings'],evidence=evidence,toolSha256=sha(Path(__file__).read_bytes()),numpyVersion=np.__version__,
 primaryDocumentation=[dict(url='https://learn.microsoft.com/en-us/windows/win32/direct3d9/device-types-and-vertex-processing-requirements',boundary='ProcessVertices always executes software vertex processing; on hardware VP its results do not directly establish hardware FFP clip output.'),dict(url='https://registry.khronos.org/OpenGL/specs/es/3.0/GLSL_ES_Specification_3.00.pdf',boundary='GLSL ES source associativity is not a guarantee of instruction-level binary32 association or fusion. CPU models do not identify the actual compiled shader arithmetic.')],
 limits='Preserved driver-specific Native offscreen controls. Authored VS2 m4x4 has no explicit viewport snap and passes its clip result to Native rasterization; Native internal viewport and rasterizer rounding are not removed. Sequential binary32 composition exactly reproduces two complete Native FFP UV buffers in these controls, not all original draws or drivers. The controlled dot8 readback matches CPU sequential model for these eight vertices only. Nested CPU model differences demonstrate a possible rounding boundary, not actual production GPU instruction order. No captured Native clip matrices are used by the separate candidate production-input builds. ProcessVertices is a software control and cannot be promoted to hardware FFP proof. All failed alternatives remain byte-bound; no pixel masking, production edits, Native game child, or whole-game equivalence.')
path=ROOT/'docs/porting/th14-stage-native-transform-composition-verified-oct14.json'
path.write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf8')
print(json.dumps(dict(diagnosticEvidenceVerified=True,modeRows=mode_rows,controlledDotWordDifferences=0,cpuModelDifferences=[r['differentWords'] for r in cpu_rows],allVariantDifferentWords=receipt['allVariantDifferentWords'])))
