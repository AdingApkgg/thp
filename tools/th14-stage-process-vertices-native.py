"""Observe D3D9 ProcessVertices independently; never infer its equality to raster processing."""
from pathlib import Path
import hashlib,json,runpy,sys
replay='--replay-no-fog' in sys.argv
ROOT=Path(__file__).resolve().parents[1];BASE=ROOT/'artifacts/th14/stage-gpu-stream-replay';OUT=BASE/('process-vertices-no-fog-replay' if replay else 'process-vertices');OUT.mkdir(exist_ok=True)
parent=ROOT/'tools/th14-stage-gpu-stream-hal.py';s=parent.read_text(encoding='utf-8')
s=s.replace("OUT=ROOT/'artifacts/th14/stage-gpu-stream-replay'","INPUT=ROOT/'artifacts/th14/stage-gpu-stream-replay';OUT=INPUT/'process-vertices'")
s=s.replace("(OUT/'prepared.json').read_bytes()","(INPUT/'prepared.json').read_bytes()").replace("(OUT/n['file']).read_bytes()","(INPUT/n['file']).read_bytes()")
if replay:s=s.replace("OUT=INPUT/'process-vertices'","OUT=INPUT/'process-vertices-no-fog-replay'")
s=s.replace("'IDirect3DTexture9'):","'IDirect3DTexture9','IDirect3DVertexBuffer9'):")
s=s.replace('pixels=bytearray();frames=[]','pixels=bytearray();frames=[];captures=[];layout=0x102;draw_index=0')
s=s.replace("prepared=json.loads(prepared_bytes)","prepared=json.loads(prepared_bytes);prepared['frames']=[f for f in prepared['frames'] if (f['stage'],f['frame'])==(3,599)]")
s=s.replace("        def execute(c):\n","        def execute(c):\n            nonlocal layout,draw_index\n")
s=s.replace("elif kind=='fvf':call(device,'IDirect3DDevice9','SetFVF',[U],[c['value']])","elif kind=='fvf':\n                layout=c['value'];call(device,'IDirect3DDevice9','SetFVF',[U],[layout])")
anchor="            elif kind=='draw':\n";assert s.count(anchor)==1
s=s.replace(anchor,anchor+'''
                if draw_index==5 and layout in (0x102,0x142):
                    source_buffer=P();target_buffer=P();count=len(c['words'])*4//c['stride'];size=count*28
                    try:
                        call(device,'IDirect3DDevice9','CreateVertexBuffer',[U,U,U,U,C.POINTER(P),P],[len(c['words'])*4,0,layout,1,C.byref(source_buffer),None])
                        call(device,'IDirect3DDevice9','CreateVertexBuffer',[U,U,U,U,C.POINTER(P),P],[size,0,0x144,1,C.byref(target_buffer),None])
                        ptr=P();call(source_buffer,'IDirect3DVertexBuffer9','Lock',[U,U,C.POINTER(P),U],[0,len(c['words'])*4,C.byref(ptr),0]);data=struct.pack('<'+'I'*len(c['words']),*c['words']);C.memmove(ptr,data,len(data));call(source_buffer,'IDirect3DVertexBuffer9','Unlock',[],[])
                        call(device,'IDirect3DDevice9','SetStreamSource',[U,P,U,U],[0,source_buffer,0,c['stride']])
                        result=method(device,'IDirect3DDevice9','ProcessVertices',[U,U,U,P,P,U])(device,0,0,count,target_buffer,None,0)
                        if result<0:captures.append(dict(drawIndex=draw_index,result=hex(result&0xffffffff),vertexCount=count))
                        else:
                            call(target_buffer,'IDirect3DVertexBuffer9','Lock',[U,U,C.POINTER(P),U],[0,size,C.byref(ptr),16]);raw=C.string_at(ptr,size);call(target_buffer,'IDirect3DVertexBuffer9','Unlock',[],[]);(OUT/'processed-vertices.bin').write_bytes(raw);captures.append(dict(drawIndex=draw_index,result=0,vertexCount=count,fvf=0x144,stride=28,sha256=sha(raw),words=list(struct.unpack('<'+'I'*(size//4),raw))))
                    finally:
                        call(device,'IDirect3DDevice9','SetStreamSource',[U,P,U,U],[0,None,0,0])
                        for buffer in (target_buffer,source_buffer):
                            if buffer.value:method(buffer,'IDirect3DVertexBuffer9','Release',[])(buffer)
                draw_index+=1
''')
s=s.replace("        for frame in prepared['frames']:\n","        for frame in prepared['frames']:\n            draw_index=0\n")
s=s.replace("(OUT/'native.bgra').write_bytes(pixels)","(OUT/'captures.json').write_text(json.dumps(captures,indent=2));(OUT/'native.bgra').write_bytes(pixels)")
if replay:
 s=s.replace("            elif kind=='draw':\n","            elif kind=='draw':\n                rs(28,0);replacement=None\n")
 s=s.replace("raw=C.string_at(ptr,size);", "raw=C.string_at(ptr,size);replacement=raw;")
 s=s.replace("                draw_index+=1\n", "                draw_index+=1\n                if replacement is not None:\n                    converted=C.create_string_buffer(replacement);call(device,'IDirect3DDevice9','SetFVF',[U],[0x144]);call(device,'IDirect3DDevice9','DrawPrimitiveUP',[U,U,P,U],[c['topology'],c['count'],converted,28]);call(device,'IDirect3DDevice9','SetFVF',[U],[layout]);return\n")
generated=ROOT/('tools/th14-stage-process-vertices-replay-hal.py' if replay else 'tools/th14-stage-process-vertices-hal.py');generated.write_text(s,encoding='utf-8');runpy.run_path(str(generated),run_name='__main__')
sha=lambda b:hashlib.sha256(b).hexdigest();ref=BASE/'variants/no-fog' if replay else BASE;meta=json.loads((ref/'native.json').read_bytes());frame=next(f for f in meta['frames'] if (f['stage'],f['frame'])==(3,599));expected=(ref/'native.bgra').read_bytes()[frame['offset']:frame['offset']+frame['bytes']];actual=(OUT/'native.bgra').read_bytes();captures=json.loads((OUT/'captures.json').read_bytes())
report=dict(diagnosticOnly=True,completeGame=False,nativeEquivalent=False,processedVertexReplay=replay,generatorSha256=sha(Path(__file__).read_bytes()),parentSourceSha256=sha(parent.read_bytes()),halSourceSha256=sha(generated.read_bytes()),captures=captures,instrumentationPreservesFinalFrame=actual==expected,differentChannels=sum(a!=b for a,b in zip(actual,expected)),nativeSha256=sha(actual),referenceSha256=sha(expected),scope='Independent hidden HAL ProcessVertices of stage3 frame599 draw5. Control retains original draw; replay control substitutes returned XYZRHW/diffuse/UV and forces fog off on both sides. API processing may differ from actual raster vertex processing; full frame equality checked separately. No production changes, original-process framebuffer or whole-game equivalence.')
(OUT/'report.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(json.dumps({k:v for k,v in report.items() if k!='captures'}));print(json.dumps(captures))
