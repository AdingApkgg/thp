"""Capture installed D3D9 m4x4 arithmetic using uniform varyings plus MOV controls."""
import hashlib,json,runpy,struct
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];INPUT=ROOT/'artifacts/th14/stage-gpu-stream-replay';base=ROOT/'tools/th14-stage-world-uv-matrix-float-hal.py'
for mode in ('matrix','mov-control'):
    out=INPUT/('clip-dot-native-'+mode);out.mkdir(exist_ok=True);s=base.read_text().replace("OUT=INPUT/'world-uv-native-float'","OUT=INPUT/'clip-dot-native-%s'"%mode)
    anchor="prepared=json.loads(prepared_bytes)";assert anchor in s
    s=s.replace(anchor,anchor+"\n    prepared['frames']=[dict(f,corner=corner) for f in prepared['frames'] for corner in range(4)]")
    s=s.replace('[640,480,116,0,0,0,C.byref(rt),None]','[32,32,116,0,0,0,C.byref(rt),None]').replace('[640,480,80,0,0,1,C.byref(depth),None]','[32,32,80,0,0,1,C.byref(depth),None]').replace('[640,480,116,2,C.byref(readback),None]','[32,32,116,2,C.byref(readback),None]')
    s=s.replace("shader_source=b'ps_2_0\\ndcl t0.xy\\ndcl_2d s0\\ndef c0,0,1,0,1\\ntexld r1,t0,s0\\nmov r0.xy,t0\\nmov r0.zw,c0\\nmov oC0,r0\\n'","shader_source=b'ps_2_0\\ndcl t0\\nmov oC0,t0\\n'")
    original="vertex_source=b'vs_2_0\\ndcl_position v0\\ndcl_texcoord v1\\nm4x4 oPos,v0,c0\\nmov oT0,v1\\n'";assert original in s
    arithmetic="mov r0,c4\\nm4x4 oT0,r0,c0\\n" if mode=='matrix' else "mov oT0,c4\\n"
    s=s.replace(original,"vertex_source=b'vs_2_0\\ndcl_position v0\\n"+arithmetic+"mov oPos,v0\\n'")
    anchor="                        call(device,'IDirect3DDevice9','SetVertexShader',[P],[vertex_shader]);call(device,'IDirect3DDevice9','SetVertexShaderConstantF',[U,P,U],[0,C.byref(constants),4])";assert anchor in s
    s=s.replace(anchor,anchor+'''
                        corner=frame['corner'];source_words=c['words'][corner*5:corner*5+3]+[0x3f800000]
                        source_values=[struct.unpack('<f',struct.pack('<I',w))[0] for w in source_words];source_constant=(F*4)(*source_values)
                        call(device,'IDirect3DDevice9','SetVertexShaderConstantF',[U,P,U],[4,C.byref(source_constant),1])
                        input_records.append(dict(stage=frame['stage'],frame=frame['frame'],corner=corner,sourceWords=source_words,matrixWords=[struct.unpack('<I',struct.pack('<f',v))[0] for v in combined]))
                        vp=t.Viewport(0,0,32,32,0,1);call(device,'IDirect3DDevice9','SetViewport',[P],[C.byref(vp)])
                        word=lambda v:struct.unpack('<I',struct.pack('<f',v))[0]
                        c=dict(c,words=[word(v) for v in (-.5,-.5,.5,0,0,.5,-.5,.5,0,0,-.5,.5,.5,0,0,.5,.5,.5,0,0)])
''')
    s=s.replace('MODE=\'float\'','MODE=\'float\';input_records=[]')
    s=s.replace('640*16) for y in range(480)','32*16) for y in range(32)').replace('width=640,height=480','width=32,height=32')
    s=s.replace("originalDrawIndex=selected_draw","originalDrawIndex=selected_draw,corner=frame['corner']")
    anchor="        (OUT/'native.rgba32f').write_bytes(pixels)";assert anchor in s;s=s.replace(anchor,anchor+"\n        (OUT/'inputs.json').write_text(json.dumps(input_records,indent=2)+'\\n')")
    s=s.replace("scope='Two captured world quads, authored vs2 combined-matrix vertex shader and original matrix inputs. Mode float. This is not the FFP reference.","scope='Authored vs2 uniform varying arithmetic probe with fixed NDC geometry, captured matrix and vertex constants; mode %s. This is not a raster coverage or original FFP frame reference."%mode)
    generated=ROOT/('tools/th14-stage-clip-dot-'+mode+'-hal.py');generated.write_text(s);runpy.run_path(str(generated),run_name='__main__')
    data=(out/'native.rgba32f').read_bytes();n=json.loads((out/'native.json').read_bytes());inputs=json.loads((out/'inputs.json').read_bytes());results=[]
    for row,inp in zip(n['frames'],inputs,strict=True):
        offset=row['offset']+(16*32+16)*16;words=list(struct.unpack_from('<4I',data,offset));values=list(struct.unpack_from('<4f',data,offset));results.append(dict(**inp,resultWords=words,resultValues=values))
        if mode=='mov-control':assert words==inp['sourceWords']
    sha=lambda b:hashlib.sha256(b).hexdigest();(out/'generation.json').write_text(json.dumps(dict(mode=mode,generatorSha256=sha(Path(__file__).read_bytes()),baseSourceSha256=sha(base.read_bytes()),halSourceSha256=sha(generated.read_bytes()),pixelsSha256=sha(data),nativeSha256=sha((out/'native.json').read_bytes()),results=results),indent=2)+'\n');print(mode,[r['resultWords'] for r in results])
