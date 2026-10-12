"""Read FFP UV at the same selected pixels as the raw sampler probe."""
import hashlib,json,runpy,shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];INPUT=ROOT/'artifacts/th14/stage-gpu-stream-replay';OUT=INPUT/'sampler-uv';OUT.mkdir(exist_ok=True)
shutil.copyfile(INPUT/'sampler-raw/inputs.json',OUT/'inputs.json');base=ROOT/'tools/th14-stage-sampler-raw-hal.py';s=base.read_text().replace("OUT=INPUT/'sampler-raw'","OUT=INPUT/'sampler-uv'")
anchor="shader_source=b'ps_2_0\\ndcl t0.xy\\ndcl_2d s0\\ntexld r0,t0,s0\\nmov oC0,r0\\n'";assert anchor in s
s=s.replace(anchor,"shader_source=b'ps_2_0\\ndcl t0.xy\\ndcl_2d s0\\ndef c0,0,1,0,1\\ntexld r1,t0,s0\\nmov r0.xy,t0\\nmov r0.zw,c0\\nmov oC0,r0\\n'")
s=s.replace('raw texture samples to RGBA32F','interpolated texture coordinates to RGBA32F')
generated=ROOT/'tools/th14-stage-sampler-uv-hal.py';generated.write_text(s);runpy.run_path(str(generated),run_name='__main__')
sha=lambda b:hashlib.sha256(b).hexdigest();(OUT/'generation.json').write_text(json.dumps(dict(generatorSha256=sha(Path(__file__).read_bytes()),baseSourceSha256=sha(base.read_bytes()),halSourceSha256=sha(generated.read_bytes()),inputsSha256=sha((OUT/'inputs.json').read_bytes()),nativeSha256=sha((OUT/'native.json').read_bytes()),assemblySha256=sha((OUT/'probe.asm').read_bytes()),shaderSha256=sha((OUT/'probe.pso').read_bytes())),indent=2)+'\n')
