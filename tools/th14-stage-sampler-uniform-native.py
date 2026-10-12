"""Sample original textures at captured constant UVs, excluding interpolation."""
import hashlib,json,runpy
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];BASE=ROOT/'artifacts/th14/stage-gpu-stream-replay';OUT=BASE/'sampler-uniform';OUT.mkdir(exist_ok=True)
parent=ROOT/'tools/th14-stage-sampler-corners-hal.py';s=parent.read_text().replace("OUT=INPUT/'sampler-corners'","OUT=INPUT/'sampler-uniform'")
cases=json.loads((BASE/'sampler-uv/inputs.json').read_bytes())['cases'];uv=json.loads((BASE/'sampler-uv/native.json').read_bytes());expanded=[]
for c,row in zip(cases,uv['frames'],strict=True):
 assert (c['stage'],c['frame'],c['draw'])==(row['stage'],row['frame'],row['originalDrawIndex'])
 for i,sample in enumerate(row['samples']):expanded.append(dict(c,points=[[16,16]],corner=i,uvWords=sample['words'],originalPoint=[sample['x'],sample['y']]))
assert len(expanded)==102
(OUT/'inputs.json').write_text(json.dumps(dict(cases=expanded),indent=2)+'\n')
anchor="source_words=c['words'][corner*(c['stride']//4):corner*(c['stride']//4)+3]+[0x3f800000]";assert anchor in s;s=s.replace(anchor,"source_words=frame['case']['uvWords']")
s=s.replace("ps_2_0\\ndcl t0\\nmov oC0,t0\\n","ps_2_0\\ndcl t0.xy\\ndcl_2d s0\\ntexld r0,t0,s0\\nmov oC0,r0\\n")
s=s.replace("mov r0,c4\\nm4x4 oT0,r0,c0","mov oT0,c4")
generated=ROOT/'tools/th14-stage-sampler-uniform-hal.py';generated.write_text(s);runpy.run_path(str(generated),run_name='__main__')
sha=lambda b:hashlib.sha256(b).hexdigest();native=json.loads((OUT/'native.json').read_bytes());clip_inputs=json.loads((OUT/'clip-inputs.json').read_bytes());results=[]
for row,inp,case in zip(native['frames'],clip_inputs,expanded,strict=True):
 sample=row['samples'][0];results.append(dict(**inp,resultWords=sample['words'],resultValues=sample['values'],originalPoint=case['originalPoint']))
(OUT/'generation.json').write_text(json.dumps(dict(generatorSha256=sha(Path(__file__).read_bytes()),baseSourceSha256=sha(parent.read_bytes()),halSourceSha256=sha(generated.read_bytes()),nativeSha256=sha((OUT/'native.json').read_bytes()),sampleSha256=sha((OUT/'samples.rgba32f').read_bytes()),uvReferenceSha256=sha((BASE/'sampler-uv/native.json').read_bytes()),results=results,scope='Constant captured UVs supplied via vs2 constant varyings; independent geometry and original textures/sampler state, no original rasterized interpolation.'),indent=2)+'\n');print('Native constant UV samples',len(results))
