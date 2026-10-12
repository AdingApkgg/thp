"""Archive a complete UV framebuffer for the selected failing long strip."""
import hashlib,json,runpy
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];BASE=ROOT/'artifacts/th14/stage-gpu-stream-replay';OUT=BASE/'sampler-uv-strip';OUT.mkdir(exist_ok=True)
parent=ROOT/'tools/th14-stage-sampler-uv-hal.py';s=parent.read_text().replace("OUT=INPUT/'sampler-uv'","OUT=INPUT/'sampler-uv-strip'")
cases=json.loads((BASE/'sampler-uv/inputs.json').read_bytes())['cases'];selected=[c for c in cases if (c['stage'],c['frame'],c['draw'])==(2,1199,44)];assert len(selected)==1
(OUT/'inputs.json').write_text(json.dumps(dict(cases=selected),indent=2)+'\n')
anchor="            pixels.extend(b''.join(struct.pack('<4I',*p['words']) for p in samples))";assert anchor in s
s=s.replace(anchor,"            (OUT/'full.rgba32f').write_bytes(raw)\n"+anchor)
generated=ROOT/'tools/th14-stage-sampler-uv-strip-hal.py';generated.write_text(s);runpy.run_path(str(generated),run_name='__main__')
sha=lambda b:hashlib.sha256(b).hexdigest();n=json.loads((OUT/'native.json').read_bytes());raw=(OUT/'full.rgba32f').read_bytes();assert len(raw)==640*480*16;assert sha(raw)==n['frames'][0]['fullFloatFrameSha256']
(OUT/'generation.json').write_text(json.dumps(dict(diagnosticOnly=True,completeGame=False,nativeEquivalent=False,generatorSha256=sha(Path(__file__).read_bytes()),baseSourceSha256=sha(parent.read_bytes()),halSourceSha256=sha(generated.read_bytes()),nativeSha256=sha((OUT/'native.json').read_bytes()),inputsSha256=sha((OUT/'inputs.json').read_bytes()),fullPixelsSha256=sha(raw),bytes=len(raw),scope='One captured long strip, authored PS2 UV output; all other draws skipped and alpha/depth/blend/fog disabled. Full Native RGBA32F bytes archived; no original game pixel shader or framebuffer claim.'),indent=2)+'\n');print('Saved complete strip UV frame',len(raw),'bytes')
