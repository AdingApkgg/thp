"""Read per-draw incoming D16 where coverage/alpha permits, with depth Always."""
import hashlib,json,runpy
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];INPUT=ROOT/'artifacts/th14/stage-gpu-stream-replay';OUT=INPUT/'depth-always-trace';OUT.mkdir(exist_ok=True)
sha=lambda b:hashlib.sha256(b).hexdigest();source=INPUT/'depth-trace/inputs.json';inputs=json.loads(source.read_bytes());reference=json.loads((INPUT/'variants/no-depth/native.json').read_bytes());portable=json.loads((INPUT/'variants/no-depth/browser-result.json').read_bytes())
for row in inputs['frames']:
    row['expectedFinalSha256']=next(r['sha256'] for r in reference['frames'] if (r['stage'],r['frame'])==(row['stage'],row['frame']))
    row['portableFinalSha256']=next(r['portableSha256'] for r in portable['reports'] if (r['stage'],r['frame'])==(row['stage'],row['frame']))
inputs['controlledDepthCompare']=8;inputs['noDepthReferenceSha256']=sha((INPUT/'variants/no-depth/native.json').read_bytes());inputs['noDepthBrowserSha256']=sha((INPUT/'variants/no-depth/browser-result.json').read_bytes());(OUT/'inputs.json').write_text(json.dumps(inputs,indent=2)+'\n')
base=ROOT/'tools/th14-stage-gpu-depth-trace-hal.py';s=base.read_text().replace("OUT=INPUT/'depth-trace'","OUT=INPUT/'depth-always-trace'")
anchor="            elif kind=='draw':\n";assert s.count(anchor)==1;s=s.replace(anchor,anchor+"                rs(23,8);rs(7,1);rs(14,1)\n")
s=s.replace('final color frames must still match the unchanged HAL reference.','Depth comparison is independently overridden to Always with writes enabled; final color frames must equal the separately measured no-depth color reference. Incoming depth is observed only where coverage and alpha allow a write.')
generated=ROOT/'tools/th14-stage-gpu-depth-incoming-hal.py';generated.write_text(s);runpy.run_path(str(generated),run_name='__main__')
(OUT/'generation.json').write_text(json.dumps(dict(generatorSha256=sha(Path(__file__).read_bytes()),baseSourceSha256=sha(base.read_bytes()),halSourceSha256=sha(generated.read_bytes()),inputsSha256=sha((OUT/'inputs.json').read_bytes()),traceSha256=sha((OUT/'trace.json').read_bytes()),scope='Independent depth Always override, not original game behavior. Per-draw depth cannot establish incoming values if the fragment is uncovered or discarded by alpha.'),indent=2)+'\n')
