"""Locate first per-draw color mismatches in the independently scoped no-fog run."""
import hashlib,json,runpy
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];INPUT=ROOT/'artifacts/th14/stage-gpu-stream-replay';OUT=INPUT/'viewport-color-trace';OUT.mkdir(exist_ok=True)
sha=lambda b:hashlib.sha256(b).hexdigest();browser=json.loads((INPUT/'variants/viewport-no-fog/browser-result.json').read_bytes());native=json.loads((INPUT/'variants/no-fog/native.json').read_bytes());selected=[]
for row in browser['reports']:
    if not row['differentChannels']:continue
    points=[]
    for d in row['first']:
        p=[d['x'],d['y']]
        if p not in points and len(points)<12:points.append(p)
    nr=next(r for r in native['frames'] if (r['stage'],r['frame'])==(row['stage'],row['frame']))
    selected.append(dict(stage=row['stage'],frame=row['frame'],points=points,expectedFinalSha256=nr['sha256'],portableFinalSha256=row['portableSha256']))
inputs=dict(frames=selected,controlledFog=False,nativeProofSha256=sha((INPUT/'variants/no-fog/native.json').read_bytes()),browserProofSha256=sha((INPUT/'variants/viewport-no-fog/browser-result.json').read_bytes()),toolSha256=sha(Path(__file__).read_bytes()))
(OUT/'inputs.json').write_text(json.dumps(inputs,indent=2)+'\n');base=ROOT/'tools/th14-stage-gpu-pixel-trace-hal.py';s=base.read_text().replace("OUT=INPUT/'pixel-trace'","OUT=INPUT/'viewport-color-trace'");anchor="            elif kind=='draw':\n";assert s.count(anchor)==1;s=s.replace(anchor,anchor+"                rs(28,0)\n")
s=s.replace('Selected mismatching pixel coordinates after each direct draw;','Selected no-fog mismatching pixel coordinates after each direct draw; fog is independently disabled and final frames must match the earlier no-fog control;')
generated=ROOT/'tools/th14-stage-viewport-color-trace-hal.py';generated.write_text(s);runpy.run_path(str(generated),run_name='__main__')
(OUT/'generation.json').write_text(json.dumps(dict(generatorSha256=sha(Path(__file__).read_bytes()),baseSourceSha256=sha(base.read_bytes()),halSourceSha256=sha(generated.read_bytes()),inputsSha256=sha((OUT/'inputs.json').read_bytes()),traceSha256=sha((OUT/'trace.json').read_bytes()),scope='Independent no-fog color isolation; not original game behavior. Final Native color buffers strictly preserve the old no-fog reference.'),indent=2)+'\n')
