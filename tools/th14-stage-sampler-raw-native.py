"""Sample native raw texture results at first failing no-fog pixel locations."""
import hashlib,json,runpy
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];INPUT=ROOT/'artifacts/th14/stage-gpu-stream-replay';OUT=INPUT/'sampler-raw';OUT.mkdir(exist_ok=True)
first=json.loads((INPUT/'viewport-color-trace/first-divergences.json').read_bytes());cases=[]
for r in first:
    case=next((c for c in cases if (c['stage'],c['frame'],c['draw'])==(r['stage'],r['frame'],r['draw'])),None)
    if case is None:case=dict(stage=r['stage'],frame=r['frame'],draw=r['draw'],points=[],texture=r['texture'],factor=r['factor'],fvf=r['fvf']);cases.append(case)
    if r['point'] not in case['points']:case['points'].append(r['point'])
(OUT/'inputs.json').write_text(json.dumps(dict(cases=cases),indent=2)+'\n');base=ROOT/'tools/th14-stage-world-uv-hal.py';s=base.read_text().replace("OUT=INPUT/'world-uv'","OUT=INPUT/'sampler-raw'")
anchor="prepared=json.loads(prepared_bytes)";assert anchor in s
s=s.replace(anchor,anchor+"\n    case_inputs=json.loads((OUT/'inputs.json').read_bytes())['cases'];prepared['frames']=[dict(next(f for f in prepared['frames'] if (f['stage'],f['frame'])==(c['stage'],c['frame'])),case=c) for c in case_inputs]")
anchor="selected_draw={(3,599):68,(3,1199):45}.get((frame['stage'],frame['frame']))";assert anchor in s;s=s.replace(anchor,"selected_draw=frame['case']['draw']")
start=s.index("        shader_source=b'");end=s.index("\n        (OUT/'probe.asm')",start);assert start>=0 and end>start;s=s[:start]+"        shader_source=b'ps_2_0\\ndcl t0.xy\\ndcl_2d s0\\ntexld r0,t0,s0\\nmov oC0,r0\\n'"+s[end:]
anchor="frames.append(dict(stage=frame['stage'],frame=frame['frame'],offset=len(pixels),bytes=len(raw),sha256=sha(raw),directDraws=1,originalDrawIndex=selected_draw,controlledScreenQuadsExcluded=frame['controlledScreenQuadsExcluded']))";assert anchor in s
s=s.replace(anchor,"            ".strip()+"samples=[dict(x=x,y=y,words=list(struct.unpack_from('<4I',raw,(y*640+x)*16)),values=list(struct.unpack_from('<4f',raw,(y*640+x)*16))) for x,y in frame['case']['points']]\n            frames.append(dict(stage=frame['stage'],frame=frame['frame'],originalDrawIndex=selected_draw,texture=frame['case']['texture'],factor=frame['case']['factor'],fvf=frame['case']['fvf'],samples=samples,fullFloatFrameSha256=sha(raw)))")
s=s.replace("pixels.extend(raw)","pixels.extend(b''.join(struct.pack('<4I',*p['words']) for p in samples))")
s=s.replace("(OUT/'native.rgba32f')","(OUT/'samples.rgba32f')")
s=s.replace("scope='Two captured world quads, FFP vertices and original matrices. Authored ps2 shader outputs interpolated UV and coverage alpha1 to RGBA32F, clears all other pixels to zero. Depth/alpha/blend/fog disabled, other draws excluded. This is an independent varying probe, not original game rendering.'","scope='Original first-failure draw inputs. Authored ps2 shader outputs raw texture samples to RGBA32F; alpha/depth/blend/fog disabled and all other draws omitted. Selected pixel float samples are stored; full intermediate frame hashes only. No original FFP pixel shader, retail framebuffer or whole-game equivalence claim.'")
generated=ROOT/'tools/th14-stage-sampler-raw-hal.py';generated.write_text(s);runpy.run_path(str(generated),run_name='__main__')
sha=lambda b:hashlib.sha256(b).hexdigest();(OUT/'generation.json').write_text(json.dumps(dict(generatorSha256=sha(Path(__file__).read_bytes()),baseSourceSha256=sha(base.read_bytes()),halSourceSha256=sha(generated.read_bytes()),inputsSha256=sha((OUT/'inputs.json').read_bytes()),nativeSha256=sha((OUT/'native.json').read_bytes()),assemblySha256=sha((OUT/'probe.asm').read_bytes()),shaderSha256=sha((OUT/'probe.pso').read_bytes())),indent=2)+'\n')
