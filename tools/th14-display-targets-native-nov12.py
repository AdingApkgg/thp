"""Derive a six-resource original loader probe for three display sizes."""
from pathlib import Path
import hashlib,json,subprocess,sys,os
R=Path(__file__).resolve().parents[1];H=R/'artifacts/th14/display-mode-entry-nov12/targets-native-v2';H.mkdir(exist_ok=False)
parent=R/'tools/th14-anm-physical-resource-loader-native.py';raw=parent.read_bytes();s=raw.decode()
changes=[
 ("ROOT=Path(__file__).resolve().parents[1]","ROOT=Path(__file__).resolve().parents[4]"),
 ("OUT=ROOT/'artifacts/th14/anm-physical-resource-loader'","OUT=ROOT/'artifacts/th14/display-mode-entry-nov12/targets-native-v2'"),
 ("names=[r['name'] for r in archive['decoded'] if r['name'].endswith('.anm')];assert len(names)==57", "names=['ascii.anm','text.anm']"),
 ("for name,rate in [(name,rate) for name in names for rate in (.3,.5,.99,1,1.01,1.25)]:",
  "for width,height,scale,name in [(w,h,s,n) for w,h,s in [(640,480,1.),(960,720,1.5),(1280,960,2.)] for n in names]:\n  rate=1.0;put(0x4f7a64,width);put(0x4f7a68,height);m.mem_write(0x4f7a6c,struct.pack('<f',scale))"),
 ("rows.append(dict(name=name,file=3,rate=rate,", "rows.append(dict(name=name,renderWidth=width,renderHeight=height,scale=scale,file=3,rate=rate,"),
 ("scope='Original ASCII resource retained", "scope='Three display sizes; exact text/ascii resources only. Original ASCII resource retained")]
for old,new in changes:assert s.count(old)==1,old;s=s.replace(old,new)
s=s.replace('Six rates,','Rate1,').replace('All57 original ANM resources,','ASCII/text only at three sizes,')
p=H/'run-native.py';p.write_text(s,encoding='utf8',newline='\n')
(H/'derivation.json').write_text(json.dumps(dict(parent=str(parent.relative_to(R)),parentSha256=hashlib.sha256(raw).hexdigest(),derivedSha256=hashlib.sha256(p.read_bytes()).hexdigest(),wrapperSha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),noGameOrGpuStarted=True),indent=2)+'\n')
subprocess.run([sys.executable,'-Xutf8',str(p)],cwd=R,check=True,env={**os.environ,'PYTHONPATH':str(R/'tools')})
j=json.loads((H/'native.json').read_bytes());assert len(j['rows'])==6
for row in j['rows']:
 for upload in row['uploads']:
  if upload['kind']=='renderTarget':assert [upload['width'],upload['height']]==[row['renderWidth'],row['renderHeight']]
print(json.dumps(dict(resources=6,actualNativeRenderTargetRequests=6,threeSizes=True,newGameOrGpuRuns=0)))
