"""Prepare independent native-recorded untextured shape GPU comparisons."""
import json,hashlib,math
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'artifacts/th14/gpu-original-shapes';OUT.mkdir(parents=True,exist_ok=True)
sha=lambda b:hashlib.sha256(b).hexdigest()
oracle_path=ROOT/'artifacts/th14/gpu-original-quads/geometry/native.json'
proof_path=ROOT/'docs/porting/th14-gpu-original-quads-geometry-verified-oct11.json'
oracle=json.loads(oracle_path.read_bytes());proof=json.loads(proof_path.read_bytes())
assert proof['passed'] and proof['nativeShapeCases']==810
for p,h in proof['sourceHashes'].items():assert sha((ROOT/'runtimes/th12/th12_web'/p).read_bytes())==h,p
for p,h in proof['toolHashes'].items():assert sha((ROOT/p).read_bytes())==h,p
cases=[];offset=0;rows=[]
for i,c in enumerate(oracle['shapes']):
 vertices=[v for d in c['draws'] for v in d['vertices']]
 assert vertices and all(d['stride']==20 for d in c['draws'])
 left=max(0,math.floor(min(v[0] for v in vertices))-2);top=max(0,math.floor(min(v[1] for v in vertices))-2)
 right=min(640,math.ceil(max(v[0] for v in vertices))+3);bottom=min(480,math.ceil(max(v[1] for v in vertices))+3)
 if left>=right or top>=bottom:left=top=0;right=bottom=1
 crop=[left,top,right-left,bottom-top];size=crop[2]*crop[3]*4
 row=dict(index=i,**{k:c[k] for k in ['mode','anchor','parent','resolution']},status=0,drawCount=len(c['draws']),crop=crop,offset=offset,size=size)
 cases.append(row);offset+=size
 rows.append('{'+','.join(str(row[k])+'u' for k in ['mode','anchor','parent','resolution'])+',{'+','.join(str(v)+'u' for v in crop)+'}}')
(ROOT/'runtimes/th12/th12_web/tests/cpp/th14-gpu-original-shapes-data.hpp').write_text('struct OriginalShapeCase {u32 mode,anchor,parent,resolution;u32 crop[4];};\nstatic constexpr OriginalShapeCase original_shape_cases[]={'+','.join(rows)+'};\n',encoding='utf8')
(OUT/'prepared.json').write_text(json.dumps(dict(cases=cases,bytes=offset,width=640,height=480,renderOracleSha256=sha(oracle_path.read_bytes()),renderProofSha256=sha(proof_path.read_bytes()),prepareToolSha256=sha(Path(__file__).read_bytes()),completeGame=False,nativeEquivalent=False,limits='Recorded original untextured shape vertices rasterized independently at 640x480, with controlled alpha/blend and fog/depth disabled; current production independently calculates shapes from VM inputs. Original draw-loop ordering and full frames are not captured.'),indent=2)+'\n',encoding='utf8')
native=(ROOT/'tools/th14-gpu-original-quads-native.py').read_text(encoding='utf8')
native=native.replace("OUT=ROOT/'artifacts/th14/gpu-original-quads'","OUT=ROOT/'artifacts/th14/gpu-original-shapes'")
native=native.replace("class Vertex(C.Structure):_fields_=[(n,F) for n in ('x','y','z','rhw')]+[('color',U),('u',F),('v',F)]","class Vertex(C.Structure):_fields_=[(n,F) for n in ('x','y','z','rhw')]+[('color',U)]")
native=native.replace("SetFVF',[U],[0x144]","SetFVF',[U],[0x44]")
native=native.replace("SetTexture',[U,P],[0,texture]","SetTexture',[U,P],[0,None]")
native=native.replace('((1,4),(2,2),(3,0),(4,4),(5,2),(6,0))','((1,2),(2,0),(3,0),(4,2),(5,0),(6,0))')
start=native.index("        rs(24,1);rs(25,7)");end=native.index("        (OUT/'native.bgra')",start)
native=native[:start]+'''        rs(24,1);rs(25,7)
        for key,value in ((19,5),(20,6),(171,1)):rs(key,value)
        prepared=json.loads((OUT/'prepared.json').read_text())
        for row in prepared['cases']:
            source=materials['shapes'][row['index']]
            call(device,'IDirect3DDevice9','Clear',[U,P,U,U,F,U],[0,None,1,0xff42678b,1,0])
            call(device,'IDirect3DDevice9','BeginScene',[],[])
            for draw in source['draws']:
                assert draw['stride']==20
                vertices=(Vertex*len(draw['vertices']))(*(Vertex(*v) for v in draw['vertices']))
                call(device,'IDirect3DDevice9','DrawPrimitiveUP',[U,U,P,U],[draw['topology'],draw['count'],C.byref(vertices),C.sizeof(Vertex)])
            call(device,'IDirect3DDevice9','EndScene',[],[])
            call(device,'IDirect3DDevice9','GetRenderTargetData',[P,P],[rt,readback])
            call(readback,'IDirect3DSurface9','LockRect',[P,P,U],[C.byref(lock),None,16])
            left,top,width,height=row['crop'];raw=b''.join(C.string_at(lock.bits+y*lock.pitch+left*4,width*4) for y in range(top,top+height))
            call(readback,'IDirect3DSurface9','UnlockRect',[],[])
            cases.append(dict(**row,pixelsSha256=hashlib.sha256(raw).hexdigest()));pixels+=raw
'''+native[end:]
native=native.replace('Actual HAL rasterization of recorded original quad geometry at 640x480, cropped without rescaling; synthetic 4x4 texture and controlled blend/alpha/sampler pipeline. Independent production geometry is compared separately. Original batch function and full native draw loop are not executed','Actual HAL rasterization of recorded original untextured rectangle, gradient, bordered rectangle, circle fan and line strip geometry at 640x480, cropped without rescaling; controlled blend/alpha and disabled fog/depth. Independent production geometry is compared separately. Original full draw loop is not executed')
(ROOT/'tools/th14-gpu-original-shapes-native.py').write_text(native,encoding='utf8')
print(f'Prepared {len(cases)} native-recorded shapes, {offset} cropped bytes')
