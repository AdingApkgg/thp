"""Audit uniform homogeneous viewport candidate over every full-control vertex.

Strict binary32 CPU models expose possible rounding boundaries. They do not
establish the compiled GPU association, fusion, division accuracy, or rasterizer.
The candidate accepts normal original matrix/vertex inputs, never Native clips.
"""
import hashlib,json,math,struct
from fractions import Fraction
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
BASE='artifacts/th14/stage-gpu-stream-replay/'
CANDIDATE='artifacts/th14/stage-current-sequential-clip-homogeneous-fe406-oct14/'
evidence={};sha=lambda b:hashlib.sha256(b).hexdigest()
def track(p):
    b=(ROOT/p).read_bytes();evidence[p]=dict(bytes=len(b),sha256=sha(b));return b
def read(p):return json.loads(track(p))
def f32(x):return struct.unpack('<f',struct.pack('<f',x))[0]
def floats(words):return [struct.unpack('<f',struct.pack('<I',v))[0] for v in words]
def words(values):return [struct.unpack('<I',struct.pack('<f',v))[0] for v in values]
def mul(a,b):
    out=[]
    for col in range(4):
        for row in range(4):
            v=f32(a[row]*b[col*4])
            for k in range(1,4):v=f32(v+f32(a[k*4+row]*b[col*4+k]))
            out.append(v)
    return out
def dot(a,v):
    out=[]
    for row in range(4):
        s=f32(a[row]*v[0])
        for k in range(1,4):s=f32(s+f32(a[k*4+row]*v[k]))
        out.append(s)
    return out
def inputs(stage,frame,draw):
    f=next(f for f in prepared['frames'] if (f['stage'],f['frame'])==(stage,frame));matrices={};viewport=None;fvf=None;index=0
    for c in f['initialState']+f['commands']:
        if c['kind']=='transform':matrices[c['key']]=floats(c['words'])
        elif c['kind']=='viewport':viewport=c['words']
        elif c['kind']=='fvf':fvf=c['value']
        elif c['kind']=='draw':
            if index==draw:return matrices,viewport,fvf,c
            index+=1
    raise AssertionError('Original draw unavailable')
prepared=read(BASE+'prepared.json');baseline=read('docs/porting/th14-stage-current-graphics-observed-oct14.json')
assert baseline['diagnosticEvidenceVerified']
assert sha(track(BASE+'prepared.json'))==baseline['evidence'][BASE+'prepared.json']['sha256']
candidate=read(CANDIDATE+'color/build.json');sources=read(CANDIDATE+'sources.json')
assert candidate['sourceBindings']==sources['sourceBindings']==baseline['sourceBindings']
assert candidate['worldViewportSnap'] is False and candidate['capturedNativeClipValuesUsed'] is False
assert candidate['preservesFogEye'] and candidate['preservesCurrentDepth16']
assert candidate['worldViewportExpression']=='homogeneous scaled reciprocal: scale=(extent*0.5)/clipW; screen=(clipXY+clipW)*scale; correctedClip=((screen+0.5)/extent*2-1)*clipW'
bound_files={}
for mode in ['color','uv']:
    b=read(CANDIDATE+mode+'/build.json')
    for name in ['Shaders.hpp','Renderer.cpp','ClipComposition.hpp']:
        raw=track(CANDIDATE+mode+'/'+name);assert sha(raw)==b['sources'][name]['sha256'];bound_files[mode+'/'+name]=sha(raw)
    shader=track(CANDIDATE+mode+'/Shaders.hpp')
    assert b'gl_Position.y=-gl_Position.y;vec2 worldScale=(viewport.zw*0.5)/gl_Position.w;vec2 worldScreen=(gl_Position.xy+vec2(gl_Position.w))*worldScale;gl_Position.xy=((worldScreen+vec2(0.5))/viewport.zw*2.0-vec2(1.0))*gl_Position.w;' in shader
    assert b'roundEven' not in shader and b'capturedClip' not in shader
    assert b'vec4 eye=view*model*vec4(position.xyz,1.0);' in shader
track('tools/th14-stage-current-sequential-clip-homogeneous-build.mjs')
assert candidate['toolSha256']==sha(track('tools/th14-stage-current-sequential-clip-homogeneous-build.mjs'))
rows=[];vertices=negative=zero=clip_xy_difference=screen_difference=0
for stage,frame,draw in [(2,1199,44),(3,599,11),(3,599,68),(3,1199,45)]:
    m,vp,fvf,c=inputs(stage,frame,draw)
    assert fvf in (0x102,0x142) and c['stride'] in (20,24) and c['topology']==5
    assert vp and vp[2]>0 and vp[3]>0
    matrix=mul(m[3],mul(m[2],m[256]));stride=c['stride']//4;count=c['count']+2
    assert len(c['words'])==count*stride
    items=[]
    for index in range(count):
        source_words=c['words'][index*stride:index*stride+3]+[1065353216]
        q=dot(matrix,floats(source_words));xy=[q[0],-q[1]];w=q[3];extent=[float(vp[2]),float(vp[3])]
        assert all(map(math.isfinite,q));vertices+=1;negative+=w<0;zero+=w==0
        old=[f32(x+f32(w/e)) for x,e in zip(xy,extent,strict=True)]
        item=dict(vertex=index,sourceWords=source_words,sequentialCPUClipWords=words(q),retainedYFlipWords=words(xy),viewportWords=vp,originalHomogeneousBiasWords=words(old),clipWPositive=w>0)
        if w!=0:
            scale=[f32(f32(e*0.5)/w) for e in extent]
            sums=[f32(x+w) for x in xy]
            screen=[f32(x*s) for x,s in zip(sums,scale,strict=True)]
            normalized=[f32(f32(f32(f32(x/w)*0.5)+0.5)*e) for x,e in zip(xy,extent,strict=True)]
            plus=[f32(x+0.5) for x in screen];div=[f32(x/e) for x,e in zip(plus,extent,strict=True)]
            twice=[f32(x*2.0) for x in div];minus=[f32(x-1.0) for x in twice];new=[f32(x*w) for x in minus]
            # Exact real-number relation for all actual finite nonzero-w inputs:
            # (((x+w)*(e/2/w)+1/2)/e*2-1)*w == x+w/e.
            for x,e in zip(xy,extent,strict=True):
                xx,ee,ww=Fraction(x),Fraction(e),Fraction(w)
                assert (((xx+ww)*(ee/Fraction(2)/ww)+Fraction(1,2))/ee*2-1)*ww==xx+ww/ee
            d=sum(a!=b for a,b in zip(words(new),words(old),strict=True));sd=sum(a!=b for a,b in zip(words(screen),words(normalized),strict=True))
            clip_xy_difference+=d;screen_difference+=sd
            item.update(scaleWords=words(scale),sumBeforeScaleWords=words(sums),screenHomogeneousWords=words(screen),screenNormalizedFirstWords=words(normalized),screenWordDifferences=sd,halfPixelAdditionWords=words(plus),divisionByExtentWords=words(div),scaleByTwoWords=words(twice),subtractOneWords=words(minus),candidateClipXYWords=words(new),clipXYWordDifferences=d,exactRealAlgebraEquivalent=True)
        else:item.update(exactRealAlgebraEquivalent=False,domainFailure='Division by zero in unguarded candidate; original homogeneous XY+bias remains finite.')
        items.append(item)
    rows.append(dict(stage=stage,frame=frame,draw=draw,vertices=count,primitiveCount=c['count'],stride=c['stride'],fvf=fvf,viewportWords=vp,computedClipMatrixWords=words(matrix),rows=items))
assert vertices==92 and zero==0
domain_path='artifacts/th14/stage-current-graphics-fe406-oct14/world-w-domain-analysis.json'
domain=read(domain_path)
domain_vertices=domain_negative=domain_zero=domain_mixed=0;domain_min=math.inf;domain_max=-math.inf
for f in prepared['frames']:
    matrices={};layout=None
    for c in f['initialState']+f['commands']:
        if c['kind']=='transform':matrices[c['key']]=floats(c['words'])
        elif c['kind']=='fvf':layout=c['value']
        elif c['kind']=='draw' and layout in (0x102,0x142):
            assert c['topology']==5 and c['stride'] in (20,24)
            clip=mul(matrices[3],mul(matrices[2],matrices[256]));stride=c['stride']//4;ws=[]
            for index in range(c['count']+2):
                vertex=floats(c['words'][index*stride:index*stride+3])+[1.0]
                w=dot(clip,vertex)[3];assert math.isfinite(w);ws.append(w)
            domain_vertices+=len(ws);domain_negative+=sum(w<0 for w in ws);domain_zero+=sum(w==0 for w in ws)
            domain_mixed+=any(w<0 for w in ws) and any(w>0 for w in ws)
            domain_min=min(domain_min,*ws);domain_max=max(domain_max,*ws)
assert domain_vertices==domain['worldSubmittedVertices']==11148
assert domain_negative==domain['negativeW']==283 and domain_zero==domain['zeroW']==0
assert domain_mixed==domain['mixedSignDraws']==34
strict_domain=dict(worldSubmittedVertices=domain_vertices,negativeW=domain_negative,zeroW=domain_zero,mixedSignDraws=domain_mixed,minimumW=domain_min,maximumW=domain_max,scope='Independent strict binary32 CPU sequential matrix and vector-dot model over original source vertices; not observed GPU clip outputs.')
report=dict(diagnosticEvidenceVerified=True,completeGame=False,nativeEquivalent=False,productionChanged=False,
 candidateLabel=candidate['label'],sourceBindings=candidate['sourceBindings'],fullNativeControls=4,
 fullControlVertices=vertices,fullControlQuadVertices=12,fullControlStripVertices=80,
 fullControlNegativeW=negative,fullControlZeroW=zero,
 cpuClipXYDifferencesFromOriginalBias=clip_xy_difference,cpuScreenDifferencesFromNormalizedFirst=screen_difference,
 operationOrder=['Retain current clip matrix-vector operation and y flip.','Binary32 model scale=round(round(extent*0.5)/w).','Binary32 model screen=round(round(clipXY+w)*scale).','Binary32 model add half pixel, divide extent, multiply2, subtract1, multiplyw.','Keep z/w, depth formula, eye/fog, original vertices/varyings and renderer batching.'],
 runtimeDataBoundary='Only original world/view/projection inputs, source vertex and runtime viewport enter candidate. No captured Native clip words, inferred snap coordinates, per-draw index, stage/frame, pixel-specific number, or explicit grid rounding enters runtime.',
 exactRealAlgebra='For w!=0 and extent!=0: (((x+w)*(extent/2/w)+1/2)/extent*2-1)*w = x+w/extent. Algebraic equality does not imply equality after binary32 rounding.',
 mathematicalCPUModels=rows,capturedInputDomainEvidencePath=domain_path,priorFusedCPUDomainEvidence=domain,independentSequentialCPUDomain=strict_domain,
 officialViewportReference='https://learn.microsoft.com/en-us/windows/win32/direct3d9/viewports-and-clipping',
 officialViewportBoundary='Microsoft describes a viewport matrix that scales/translates homogeneous vertices and flips y before conversion to non-homogeneous coordinates. This motivates the algebra; it does not specify host or GPU floating-point instruction order.',
 zeroNegativeWBoundary='Current diagnostic is unguarded and w0 division/reconstruction is undefined. Actual captured mixed-sign/negative-w primitives exist; no production adoption is justified. A separate generic w<=0 fallback to original homogeneous XY+bias must be verified if this candidate has benefits. Full92 controls have no zero w; this is not absence in all possible gameplay.',
 evidence=evidence,toolSha256=sha(Path(__file__).read_bytes()),
 limits='Strict binary32 sequential CPU dot/divide models and exact Fraction algebra only. GLSL compiler may reassociate, fuse and use its permitted division error. Mathematical predicted clips are not observed GPU outputs, and no transform feedback or actual hardware clip capture is added. Native per-pixel equivalence requires the separate21color/23UV physical browser captures; gameplay/whole-memory/pixels/audio/loading1:1 remain pending.')
path=ROOT/'docs/porting/th14-stage-homogeneous-viewport-arithmetic-verified-oct14.json'
path.write_text(json.dumps(report,indent=2)+'\n',encoding='utf8')
print(json.dumps(dict(diagnosticEvidenceVerified=True,fullControlVertices=vertices,fullControlNegativeW=negative,fullControlZeroW=zero,cpuClipXYWordDifferences=clip_xy_difference,cpuScreenWordDifferences=screen_difference)))
