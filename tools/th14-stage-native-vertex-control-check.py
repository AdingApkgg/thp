import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];BASE='artifacts/th14/stage-gpu-stream-replay/';evidence={};sha=lambda b:hashlib.sha256(b).hexdigest()
def track(p):
 b=(ROOT/p).read_bytes();evidence[p]=dict(bytes=len(b),sha256=sha(b));return b
def read(p):return json.loads(track(p))
prefix=BASE+'native-vertex-control/';g=read(prefix+'generation.json');n=read(prefix+'native.json');pixels=track(prefix+'native.bgra');ref=read(BASE+'variants/no-fog/native.json');reference=track(BASE+'variants/no-fog/native.bgra');prepared=read(BASE+'prepared.json')
for key,p in [('generatorSha256','tools/th14-stage-native-vertex-control.py'),('baseSourceSha256','tools/th14-stage-gpu-stream-hal.py'),('halSourceSha256','tools/th14-stage-native-vertex-control-hal.py'),('nativeSha256',prefix+'native.json')]:assert g[key]==sha(track(p))
assert g['pixelsSha256']==n['pixelsSha256']==sha(pixels);assert g['referencePixelsSha256']==ref['pixelsSha256']==sha(reference);assert pixels==reference;assert len(pixels)==21*640*480*4;assert n['preparedSha256']==ref['preparedSha256']==sha(track(BASE+'prepared.json'));assert n['toolSha256']==sha(track('tools/th14-stage-native-vertex-control-hal.py'))
assert len(n['frames'])==len(ref['frames'])==21
for a,b in zip(n['frames'],ref['frames'],strict=True):
 assert (a['stage'],a['frame'],a['offset'],a['bytes'],a['sha256'])==(b['stage'],b['frame'],b['offset'],b['bytes'],b['sha256']);assert sha(pixels[a['offset']:a['offset']+a['bytes']])==a['sha256']
assert g['exactFrames']==21 and g['differentChannels']==0 and g['maxDelta']==0
for p in ['plain.vs.asm','colored.vs.asm','plain.vso','colored.vso']:track(prefix+p)
for t in prepared['textures']:assert t['sha256']==sha(track(BASE+t['file']))
out=dict(diagnosticEvidenceVerified=True,productionChanged=False,completeGame=False,nativeEquivalent=False,frames=21,bytes=len(pixels),exactFrames=21,differentChannels=0,maxDelta=0,strictPixelsEqual=True,evidence=evidence,toolSha256=sha(Path(__file__).read_bytes()),scope=g['scope']+' Both complete color buffers independently compared. This control replaces the FFP vertex path, not the native pixel path; fog is disabled on both sides. No full original framebuffer or whole-game equivalence.')
(ROOT/'docs/porting/th14-stage-native-vertex-control-observed-oct12.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({k:out[k] for k in ['diagnosticEvidenceVerified','frames','bytes','exactFrames','differentChannels']}))
