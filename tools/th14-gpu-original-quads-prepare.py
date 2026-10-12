"""Prepare actual retail-recorded quads for a geometry-to-GPU comparison.

The original draw dispatcher was executed by the existing native oracle.
Its batch boundary remains recorded; this is not a native full-game capture.
"""
import json,hashlib,math
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent;OUT=ROOT/'artifacts/th14/gpu-original-quads';OUT.mkdir(parents=True,exist_ok=True)
sha=lambda b:hashlib.sha256(b).hexdigest()
def once(s,a,b):
    assert s.count(a)==1,(a,s.count(a))
    return s.replace(a,b)
oracle_path=ROOT/'artifacts/th14/gpu-original-quads/geometry/native.json'
proof_path=ROOT/'docs/porting/th14-gpu-original-quads-geometry-verified-oct11.json'
oracle_bytes=oracle_path.read_bytes();oracle=json.loads(oracle_bytes);proof=json.loads(proof_path.read_text())
assert proof['passed'] and proof['nativeQuadCases']==640
assert oracle['executableSha256']==sha(Path('H:/Games/th/14/th14.exe').read_bytes())==proof['nativeExecutableSha256']
for path,hash in proof['sourceHashes'].items():assert sha((ROOT/'runtimes/th12/th12_web'/path).read_bytes())==hash,path
for path,hash in proof['toolHashes'].items():assert sha((ROOT/path).read_bytes())==hash,path
cases=[];offset=0;rows=[]
for index,c in enumerate(oracle['quads']):
    vertices=[v for draw in c['draws'] for v in draw];assert len(c['draws'])<=1
    if vertices:
        left=max(0,math.floor(min(v[0] for v in vertices))-2);top=max(0,math.floor(min(v[1] for v in vertices))-2)
        right=min(640,math.ceil(max(v[0] for v in vertices))+3);bottom=min(480,math.ceil(max(v[1] for v in vertices))+3)
        if left>=right or top>=bottom:left=top=0;right=bottom=1
    else:left=top=0;right=bottom=1
    crop=[left,top,right-left,bottom-top];size=crop[2]*crop[3]*4
    row=dict(index=index,**{k:c[k] for k in ['mode','colorMode','relation','tinted','visibility','sample','status']},drawCount=len(c['draws']),crop=crop,offset=offset,size=size)
    cases.append(row);offset+=size
    rows.append('{'+','.join(str(row[k])+'u' for k in ['mode','colorMode','relation','tinted','visibility','sample'])+',{'+','.join(str(v)+'u' for v in crop)+'}}')
data='struct OriginalQuadCase {u32 mode,colorMode,relation,tinted,visibility,sample;u32 crop[4];};\nstatic constexpr OriginalQuadCase original_quad_cases[]={'+','.join(rows)+'};\n'
(ROOT/'runtimes/th12/th12_web/tests/cpp/th14-gpu-original-quads-data.hpp').write_text(data,encoding='utf8')
(OUT/'prepared.json').write_text(json.dumps(dict(cases=cases,bytes=offset,width=640,height=480,originalRecordedQuads=640,submittedQuadCases=sum(c['drawCount'] for c in cases),renderOracleSha256=sha(oracle_bytes),renderProofSha256=sha(proof_path.read_bytes()),prepareToolSha256=sha(Path(__file__).read_bytes()),completeGame=False,nativeEquivalent=False,limits='Original recorded four-corner quads are submitted as D3D9 strips; production independently generates its triangles from the same VM inputs. Controlled 4x4 texture and non-fog pipeline. Original batch implementation and full draw loop are not captured. Crops include a margin around every native quad and preserve the original 640x480 pixel grid.'),indent=2)+'\n',encoding='utf8')
native=(ROOT/'tools/th14-gpu-raster-native.py').read_text(encoding='utf-8-sig')
native=once(native,"OUT=ROOT/'artifacts/th14/gpu-raster'","OUT=ROOT/'artifacts/th14/gpu-original-quads'")
native=once(native,"materials_path=ROOT/'artifacts/th14/render-native.json'","materials_path=ROOT/'artifacts/th14/gpu-original-quads/geometry/native.json'")
native=once(native,'pp=Present(32,32,','pp=Present(640,480,');assert native.count('[32,32,21,')==2;native=native.replace('[32,32,21,','[640,480,21,')
native=once(native,'window,0x20,','window,0x40,');native=once(native,'vp=Viewport(0,0,32,32,','vp=Viewport(0,0,640,480,')
native=once(native,'((7,0),(14,0),(15,0),','((7,0),(14,0),(15,1),')
start=native.index('        colors=[');end=native.index("        (OUT/'native.bgra')",start)
native=native[:start]+'''        rs(24,1);rs(25,7)
        prepared=json.loads((OUT/'prepared.json').read_text())
        for row in prepared['cases']:
            source=materials['quads'][row['index']]
            for k,v in ((19,5),(20,6),(171,1)):rs(k,v)
            for k,v in ((1,1),(2,1),(5,2),(6,2)):sampler(k,v)
            for kind,key,value in source['events']:
                if kind=='state':rs(key,value)
                elif kind=='sampler':sampler(key,value)
                else:raise AssertionError(kind)
            call(device,'IDirect3DDevice9','Clear',[U,P,U,U,F,U],[0,None,1,0xff42678b,1,0])
            call(device,'IDirect3DDevice9','BeginScene',[],[])
            for draw in source['draws']:
                assert len(draw)==4
                vertices=(Vertex*4)(*(Vertex(*v) for v in draw))
                call(device,'IDirect3DDevice9','DrawPrimitiveUP',[U,U,P,U],[5,2,C.byref(vertices),C.sizeof(Vertex)])
            call(device,'IDirect3DDevice9','EndScene',[],[])
            call(device,'IDirect3DDevice9','GetRenderTargetData',[P,P],[rt,readback])
            call(readback,'IDirect3DSurface9','LockRect',[P,P,U],[C.byref(lock),None,16])
            left,top,width,height=row['crop'];raw=b''.join(C.string_at(lock.bits+y*lock.pitch+left*4,width*4) for y in range(top,top+height))
            call(readback,'IDirect3DSurface9','UnlockRect',[],[])
            cases.append(dict(**row,pixelsSha256=hashlib.sha256(raw).hexdigest()));pixels+=raw
'''+native[end:]
native=once(native,'width=32,height=32,','width=640,height=480,behaviorFlags=64,vertexProcessing="Hardware",preparedSha256=hashlib.sha256((OUT/"prepared.json").read_bytes()).hexdigest(),')
scope="scope='Offscreen actual Direct3D9 HAL rasterization"
start=native.index(scope);end=native.index("')",start)
native=native[:start]+"scope='Actual HAL rasterization of recorded original quad geometry at 640x480, cropped without rescaling; synthetic 4x4 texture and controlled blend/alpha/sampler pipeline. Independent production geometry is compared separately. Original batch function and full native draw loop are not executed"+native[end:]
(ROOT/'tools/th14-gpu-original-quads-native.py').write_text(native,encoding='utf8')
print(f'Prepared 640 original-recorded quad cases, {offset} cropped BGRA bytes, 256 submitted cases')
