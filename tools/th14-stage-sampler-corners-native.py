"""Read native GPU clip results for all84 corners in the failing draw corpus."""
import hashlib,json,runpy,struct,shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];INPUT=ROOT/'artifacts/th14/stage-gpu-stream-replay';OUT=INPUT/'sampler-corners';OUT.mkdir(exist_ok=True);base=ROOT/'tools/th14-stage-sampler-matrix-float-hal.py';s=base.read_text().replace("OUT=INPUT/'sampler-matrix-float'","OUT=INPUT/'sampler-corners'")
cases=json.loads((INPUT/'sampler-uv/inputs.json').read_bytes())['cases'];expanded=[]
for c in cases:
    for corner in range(4):expanded.append(dict(c,points=[[16,16]],corner=corner))
(OUT/'inputs.json').write_text(json.dumps(dict(cases=expanded),indent=2)+'\n')
s=s.replace('MODE=\'float\'','MODE=\'float\';clip_inputs=[]')
s=s.replace('[640,480,116,0,0,0,C.byref(rt),None]','[32,32,116,0,0,0,C.byref(rt),None]').replace('[640,480,80,0,0,1,C.byref(depth),None]','[32,32,80,0,0,1,C.byref(depth),None]').replace('[640,480,116,2,C.byref(readback),None]','[32,32,116,2,C.byref(readback),None]')
start=s.index("        shader_source=b'");end=s.index("\n        (OUT/'probe.asm')",start);s=s[:start]+"        shader_source=b'ps_2_0\\ndcl t0\\nmov oC0,t0\\n'"+s[end:]
start=s.index("            vertex_source=b'");end=s.index("\n            (OUT/'probe.vs.asm')",start);s=s[:start]+"            vertex_source=b'vs_2_0\\ndcl_position v0\\nmov r0,c4\\nm4x4 oT0,r0,c0\\nmov oPos,v0\\n'"+s[end:]
anchor="call(device,'IDirect3DDevice9','SetVertexShaderConstantF',[U,P,U],[0,C.byref(constants),8])";assert anchor in s
s=s.replace(anchor,anchor+'''
                        corner=frame['case']['corner'];source_words=c['words'][corner*(c['stride']//4):corner*(c['stride']//4)+3]+[0x3f800000]
                        source_values=[struct.unpack('<f',struct.pack('<I',w))[0] for w in source_words];source_constant=(F*4)(*source_values)
                        call(device,'IDirect3DDevice9','SetVertexShaderConstantF',[U,P,U],[4,C.byref(source_constant),1])
                        clip_inputs.append(dict(stage=frame['stage'],frame=frame['frame'],draw=selected_draw,corner=corner,fvf=frame['case']['fvf'],sourceWords=source_words,matrixWords=[struct.unpack('<I',struct.pack('<f',v))[0] for v in combined]))
                        vp=t.Viewport(0,0,32,32,0,1);call(device,'IDirect3DDevice9','SetViewport',[P],[C.byref(vp)])
                        word=lambda v:struct.unpack('<I',struct.pack('<f',v))[0]
                        vertices=[]
                        for x,y in ((-.5,-.5),(.5,-.5),(-.5,.5),(.5,.5)):
                            vertices.extend([word(x),word(y),word(.5)]+([0xffffffff] if c['stride']==24 else [])+[0,0])
                        c=dict(c,count=2,words=vertices)
''')
s=s.replace('640*16) for y in range(480)','32*16) for y in range(32)').replace('(y*640+x)*16','(y*32+x)*16').replace('width=640,height=480','width=32,height=32')
anchor="        (OUT/'samples.rgba32f').write_bytes(pixels)";assert anchor in s;s=s.replace(anchor,anchor+"\n        (OUT/'clip-inputs.json').write_text(json.dumps(clip_inputs,indent=2)+'\\n')")
s=s.replace('interpolated texture coordinates from authored vs2 combined-matrix mode float to RGBA32F','uniform-varying vs2 m4x4 clip results with independent NDC geometry to RGBA32F')
generated=ROOT/'tools/th14-stage-sampler-corners-hal.py';generated.write_text(s);runpy.run_path(str(generated),run_name='__main__')
sha=lambda b:hashlib.sha256(b).hexdigest();n=json.loads((OUT/'native.json').read_bytes());data=(OUT/'samples.rgba32f').read_bytes();result=[]
for row,inp in zip(n['frames'],json.loads((OUT/'clip-inputs.json').read_bytes()),strict=True):
    assert len(row['samples'])==1;sample=row['samples'][0];result.append(dict(**inp,resultWords=sample['words'],resultValues=sample['values']))
(OUT/'generation.json').write_text(json.dumps(dict(generatorSha256=sha(Path(__file__).read_bytes()),baseSourceSha256=sha(base.read_bytes()),halSourceSha256=sha(generated.read_bytes()),nativeSha256=sha((OUT/'native.json').read_bytes()),sampleSha256=sha(data),results=result),indent=2)+'\n');print('Native GPU corner results',len(result),len(data),'bytes')
