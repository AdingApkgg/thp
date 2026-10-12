"""Compare matrix associations against FFP UV at all102 selected pixels."""
import hashlib,json,runpy,struct,shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];INPUT=ROOT/'artifacts/th14/stage-gpu-stream-replay';base=ROOT/'tools/th14-stage-sampler-uv-hal.py';sha=lambda b:hashlib.sha256(b).hexdigest()
for mode in ('float','pair','double','viewproj'):
    OUT=INPUT/('sampler-matrix-'+mode);OUT.mkdir(exist_ok=True);shutil.copyfile(INPUT/'sampler-uv/inputs.json',OUT/'inputs.json');s=base.read_text().replace("OUT=INPUT/'sampler-uv'","OUT=INPUT/'sampler-matrix-%s'"%mode)
    s=s.replace("'IDirect3DPixelShader9'):","'IDirect3DPixelShader9','IDirect3DVertexShader9'):").replace('pixel_shader=P();textures={}','pixel_shader=P();vertex_shader=P();matrices={};textures={}')
    anchor="            call(device,'IDirect3DDevice9','CreatePixelShader',[P,C.POINTER(P)],[buffer,C.byref(pixel_shader)])";assert anchor in s
    s=s.replace(anchor,anchor+'''
            blob_method(blob,2,U)(blob);blob=P()
            vertex_source=b'vs_2_0\\ndcl_position v0\\ndcl_texcoord v1\\ndef c8,1,0,1,0\\nm4x4 oPos,v0,c0\\nmov r0,v1\\nmov r0.zw,c8\\nm4x4 oT0,r0,c4\\n'
            (OUT/'probe.vs.asm').write_bytes(vertex_source);source=C.create_string_buffer(vertex_source)
            hr=compiler.D3DAssemble(source,len(vertex_source),b'sampler-matrix.asm',None,None,0,C.byref(blob),C.byref(errors));assert hr>=0,hex(hr&0xffffffff)
            code=C.string_at(blob_method(blob,3,P)(blob),blob_method(blob,4,C.c_size_t)(blob));(OUT/'probe.vso').write_bytes(code);buffer=C.create_string_buffer(code)
            call(device,'IDirect3DDevice9','CreateVertexShader',[P,C.POINTER(P)],[buffer,C.byref(vertex_shader)])
''')
    anchor="            elif kind=='transform':\n";assert s.count(anchor)==1;s=s.replace(anchor,anchor+"                matrices[c['key']]=[struct.unpack('<f',struct.pack('<I',w))[0] for w in c['words']]\n")
    anchor="        def execute(c):\n";assert s.count(anchor)==1
    s=s.replace(anchor,'''
        f32=lambda x:struct.unpack('<f',struct.pack('<f',x))[0]
        def multiply(a,b):
            result=[]
            for col in range(4):
                for row in range(4):
                    terms=[a[k*4+row]*b[col*4+k] for k in range(4)]
                    if MODE=='double':v=f32(sum(terms))
                    elif MODE=='pair':v=f32(f32(f32(terms[0])+f32(terms[1]))+f32(f32(terms[2])+f32(terms[3])))
                    else:
                        v=f32(terms[0])
                        for tvalue in terms[1:]:v=f32(v+f32(tvalue))
                    result.append(v)
            return result
        def execute(c):
''')
    anchor="                        call(device,'IDirect3DDevice9','SetPixelShader',[P],[pixel_shader]);execute(c)";assert anchor in s
    s=s.replace(anchor,'''
                        combined=multiply(multiply(matrices[3],matrices[2]),matrices[256]) if MODE=='viewproj' else multiply(matrices[3],multiply(matrices[2],matrices[256]))
                        constants=(F*32)(*[a[row+col*4] for a in (combined,matrices[16]) for row in range(4) for col in range(4)])
                        call(device,'IDirect3DDevice9','SetVertexShader',[P],[vertex_shader]);call(device,'IDirect3DDevice9','SetVertexShaderConstantF',[U,P,U],[0,C.byref(constants),8])
                        call(device,'IDirect3DDevice9','SetPixelShader',[P],[pixel_shader]);execute(c)
''')
    anchor="        if pixel_shader.value:method(pixel_shader,'IDirect3DPixelShader9','Release',[])(pixel_shader)";assert anchor in s;s=s.replace(anchor,"        if vertex_shader.value:method(vertex_shader,'IDirect3DVertexShader9','Release',[])(vertex_shader)\n"+anchor)
    s=s.replace('def main():',"MODE=%r\ndef main():"%mode).replace('interpolated texture coordinates to RGBA32F','interpolated texture coordinates from authored vs2 combined-matrix mode %s to RGBA32F'%mode)
    generated=ROOT/('tools/th14-stage-sampler-matrix-'+mode+'-hal.py');generated.write_text(s);runpy.run_path(str(generated),run_name='__main__')
    actual=(OUT/'samples.rgba32f').read_bytes();reference=(INPUT/'sampler-uv/samples.rgba32f').read_bytes();assert len(actual)==len(reference)==1632;different=sum(actual[i:i+4]!=reference[i:i+4] for i in range(0,len(actual),4))
    report=dict(mode=mode,generatorSha256=sha(Path(__file__).read_bytes()),baseSourceSha256=sha(base.read_bytes()),halSourceSha256=sha(generated.read_bytes()),nativeSha256=sha((OUT/'native.json').read_bytes()),ffpSampleSha256=sha(reference),sampleSha256=sha(actual),floatWords=408,differentWords=different,strictWordsEqual=different==0)
    (OUT/'generation.json').write_text(json.dumps(report,indent=2)+'\n');print('Native matrix mode',mode,different,'/408 differences')
