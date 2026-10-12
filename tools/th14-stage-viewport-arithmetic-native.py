"""Read authored vs2 reciprocal/viewport arithmetic for captured world vertices."""
import hashlib,json,runpy,struct,math
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];BASE=ROOT/'artifacts/th14/stage-gpu-stream-replay';OUT=BASE/'viewport-arithmetic';OUT.mkdir(exist_ok=True)
parent=ROOT/'tools/th14-stage-sampler-vertices-hal.py';s=parent.read_text().replace("OUT=INPUT/'sampler-vertices'","OUT=INPUT/'viewport-arithmetic'")
(OUT/'inputs.json').write_bytes((BASE/'sampler-vertices/inputs.json').read_bytes())
anchor="mov r0,c4\\nm4x4 oT0,r0,c0\\nmov oPos,v0"
assert anchor in s
s=s.replace(anchor,"mov r0,c4\\nm4x4 r2,r0,c0\\nmov r0,r2\\nrcp r1.w,r0.w\\nmul r1.xy,r0,r1.w\\nmov r3,c6\\nmad oT0.xy,r1,c5,r3\\nmov oT0.z,r1.w\\nmov oT0.w,r0.w\\nmov oPos,v0")
anchor="call(device,'IDirect3DDevice9','SetVertexShaderConstantF',[U,P,U],[4,C.byref(source_constant),1])";assert anchor in s
s=s.replace(anchor,anchor+"\n                        viewport_constants=(F*8)(320,-240,0,0,320,240,0,0);call(device,'IDirect3DDevice9','SetVertexShaderConstantF',[U,P,U],[5,C.byref(viewport_constants),2])")
s=s.replace('assert hr>=0,hex(hr&0xffffffff)', 'assert hr>=0,C.string_at(blob_method(errors,3,P)(errors),blob_method(errors,4,C.c_size_t)(errors)).decode()')
generated=ROOT/'tools/th14-stage-viewport-arithmetic-hal.py';generated.write_text(s);runpy.run_path(str(generated),run_name='__main__')
sha=lambda b:hashlib.sha256(b).hexdigest();native=json.loads((OUT/'native.json').read_bytes());clips=json.loads((BASE/'sampler-vertices/generation.json').read_bytes())['results'];results=[];div_dif=0;mad_dif=0;snap_dif=0
f32=lambda v:struct.unpack('<f',struct.pack('<f',v))[0];word=lambda v:struct.unpack('<I',struct.pack('<f',v))[0]
for n,c in zip(native['frames'],clips,strict=True):
 sample=n['samples'][0];q=c['resultValues'];reciprocal=f32(1/q[3]);xy=[f32(math.fma(f32(q[0]/q[3]),320,320)),f32(math.fma(f32(q[1]/q[3]),-240,240))]
 div_dif+=word(reciprocal)!=sample['words'][2];mad_dif+=sum(word(v)!=sample['words'][i] for i,v in enumerate(xy));snap_dif+=sum(round(v*256)!=round(sample['values'][i]*256) for i,v in enumerate(xy))
 results.append(dict(stage=c['stage'],frame=c['frame'],draw=c['draw'],corner=c['corner'],sourceWords=c['sourceWords'],matrixWords=c['matrixWords'],clipWords=c['resultWords'],resultWords=sample['words'],resultValues=sample['values'],nativeWords=sample['words'],nativeValues=sample['values'],divisionReciprocalWord=word(reciprocal),divisionViewportWords=list(map(word,xy))))
(OUT/'generation.json').write_text(json.dumps(dict(diagnosticOnly=True,completeGame=False,nativeEquivalent=False,generatorSha256=sha(Path(__file__).read_bytes()),baseSourceSha256=sha(parent.read_bytes()),halSourceSha256=sha(generated.read_bytes()),nativeSha256=sha((OUT/'native.json').read_bytes()),sampleSha256=sha((OUT/'samples.rgba32f').read_bytes()),clipReferenceSha256=sha((BASE/'sampler-vertices/generation.json').read_bytes()),results=results,vertices=len(results),reciprocalDifferentWords=div_dif,viewportDifferentWords=mad_dif,snap8DifferentCoordinates=snap_dif,scope='Authored vs2 m4x4/rcp/mul/mad at captured world vertices with independent NDC geometry; does not recover or prove the native FFP viewport implementation.'),indent=2)+'\n');print(json.dumps(dict(vertices=len(results),reciprocalDifferentWords=div_dif,viewportDifferentWords=mad_dif,snap8DifferentCoordinates=snap_dif)))
