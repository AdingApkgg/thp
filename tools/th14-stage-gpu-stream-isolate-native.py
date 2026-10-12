"""Generate and execute our own isolated HAL reference variants."""
import hashlib,json,runpy
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sha=lambda b:hashlib.sha256(b).hexdigest()
base=ROOT/'tools/th14-stage-gpu-stream-hal.py'
for variant in ('no-fog','no-depth'):
    out=ROOT/'artifacts/th14/stage-gpu-stream-replay/variants'/variant;out.mkdir(parents=True,exist_ok=True)
    text=base.read_text(encoding='utf8')
    text=text.replace("OUT=ROOT/'artifacts/th14/stage-gpu-stream-replay'", "INPUT=ROOT/'artifacts/th14/stage-gpu-stream-replay';OUT=INPUT/'variants'/'"+variant+"'")
    text=text.replace("(OUT/'prepared.json').read_bytes()","(INPUT/'prepared.json').read_bytes()").replace("(OUT/n['file']).read_bytes()","(INPUT/n['file']).read_bytes()")
    anchor="            elif kind=='draw':\n"
    assert text.count(anchor)==1
    override="                rs(28,0)\n" if variant=='no-fog' else "                rs(7,0);rs(14,0)\n"
    text=text.replace(anchor,anchor+override)
    text=text.replace("report=dict(generated=True,","report=dict(variant='"+variant+"',diagnosticOnly=True,generatorSha256='"+sha(Path(__file__).read_bytes())+"',baseSourceSha256='"+sha(base.read_bytes())+"',generated=True,")
    text=text.replace("scope=prepared['scope'])","scope=prepared['scope']+' Diagnostic override "+variant+" applied before every direct draw; not native game behavior.')")
    generated=ROOT/'tools'/('th14-stage-gpu-stream-'+variant+'-hal.py')
    generated.write_text(text,encoding='utf8');runpy.run_path(str(generated),run_name='__main__')
