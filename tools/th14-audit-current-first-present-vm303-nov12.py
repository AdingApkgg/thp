"""Strictly compare retained first-Present registries without remapping handles."""
from pathlib import Path
from collections import Counter
import hashlib,importlib.util,json,struct
R=Path(__file__).resolve().parents[1]
H=R/'artifacts/th14/current-first-present-vm303-nov12'
N=R/'artifacts/th14/current-startup-prefix-nov10/native'
C=R/'artifacts/th14/control-main-stop-nov12/first-present/candidate-owner-replay'
B=R/'artifacts/th14/control-main-stop-nov12/first-present/probe-v2/candidate'
P=R/'artifacts/th14/current-low-pause-pixels-nov12/component'
assert not H.exists()
bindings={}
def read(p):
 b=p.read_bytes();bindings[p.relative_to(R).as_posix()]=hashlib.sha256(b).hexdigest();return b
def load(p):return json.loads(read(p))
nr,cr=load(N/'report.json'),load(C/'report.json')
assert nr['childExited'] and nr['frameReadbackCompleted'] and not nr['error']
assert cr['terminal'] and cr['closed'] and cr['stoppedBy']=='declared-target'
assert not cr['exception'] and not cr['errors'] and cr['platformRetired'] and not cr['resourceLeaks']
assert all(x['returned'] and not x['error'] for x in cr['workers'])
assert all(x['closed'] and x['exitCode']==0 for x in cr['physicalWorkers'])
build=load(B/'build.json');current=load(P/'build.json');plan=load(C/'plan.json')
assert build['objectBindings']==current['objectBindings']
assert build['outputs']['candidate']['wasmSha256']==plan['wasmSha256']==hashlib.sha256(read(B/'candidate.wasm')).hexdigest()
assert hashlib.sha256(read(N/'report.json')).hexdigest()==plan['referenceMetadataSha256']
for name,digest in {**current['sourceBindingsByMode']['candidate'],**current['objectBindings']}.items():
 assert hashlib.sha256((R/name).read_bytes()).hexdigest()==digest,name
native=load(N/'live-vms-before-readback.json')
assert native['readOnly'] and native['readBeforeDiagnosticCalls'] and native['ordinaryAndOverlayRegistryWalk']
tool=R/'tools/th14-native-title-live-compare-oct27.py';source=read(tool).decode()
assert bindings[tool.relative_to(R).as_posix()]=='c7866f2c3d6e030bae1e4c5153b196f7500436b43e710fc181730bf087a3f9cc'
spec=importlib.util.spec_from_file_location('first_present_native303',tool)
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
needle='        assert not address or address in by_address'
assert source.count(needle)==1
source=source.replace(needle,"        if address and address not in by_address:return {'unmeasuredNativeVmAddress':address}")
exec(compile(source,str(tool),'exec'),m.__dict__)
addresses={struct.unpack_from('<I',bytes.fromhex(r['rawVmHex']),0x570)[0]:r['handle'] for r in native['rows']}
assert len(addresses)==len(native['rows']) and 0 not in addresses
nrows={};unknown=[];fields=None
for row in native['rows']:
 fields,words=m.native_words(row,addresses);assert len(words)==303
 nrows[row['handle']]=words
 for i,v in enumerate(words):
  if isinstance(v,dict):unknown.append(dict(handle=row['handle'],field=fields[i],**v))
raw=read(C/'target-live-vms.u32');w=struct.unpack('<'+'I'*(len(raw)//4),raw)
assert w[:3]==(1,1,1) and w[4:6]==(1,303) and len(w)==6+w[3]*303
assert hashlib.sha256(raw).hexdigest()==load(C/'target-live-vms.json')['sha256']
cpp=[list(w[i:i+303]) for i in range(6,len(w),303)];crows={r[0]:r for r in cpp}
assert len(crows)==len(cpp) and len(nrows)==len(native['rows'])
missing=sorted(nrows.keys()-crows.keys());extra=sorted(crows.keys()-nrows.keys())
diffs=[];compared=0;by_family=Counter();type_changes=[]
for handle in sorted(nrows.keys()&crows.keys()):
 a,b=nrows[handle],crows[handle]
 if a[1:3]!=b[1:3]:type_changes.append(dict(handle=handle,native=a[1:3],cpp=b[1:3]))
 for i,(x,y) in enumerate(zip(a,b)):
  if isinstance(x,dict):continue
  compared+=1
  if x!=y:
   diffs.append(dict(handle=handle,nativeFile=a[1],nativeScript=a[2],cppFile=b[1],cppScript=b[2],field=fields[i],native=x,cpp=y))
   by_family[(a[1],a[2],b[1],b[2])]+=1
summary=dict(productionGameSource='e6b15d27768ee4da293c81c3c239e3d42880020b',
 currentWasmSha256=plan['wasmSha256'],nativeVms=len(nrows),cppVms=len(crows),
 commonLiteralHandles=len(nrows.keys()&crows.keys()),missingLiteralHandles=missing,extraLiteralHandles=extra,
 registryOrderExact=[r['handle'] for r in native['rows']]==[r[0] for r in cpp],
 commonHandlesWithDifferentFileOrScript=type_changes,measuredCommonWords=compared,differentCommonWords=len(diffs),
 unmeasuredNativeLinks=len(unknown),differentWordsByFamilies=[dict(nativeFile=k[0],nativeScript=k[1],cppFile=k[2],cppScript=k[3],words=v) for k,v in sorted(by_family.items())],
 nativeInventory=[dict(file=k[0],script=k[1],count=v) for k,v in sorted(Counter((r[1],r[2]) for r in nrows.values()).items())],
 cppInventory=[dict(file=k[0],script=k[1],count=v) for k,v in sorted(Counter((r[1],r[2]) for r in crows.values()).items())],
 handlesNotRemapped=True,agesNotNormalized=True,referenceStateNotFedBack=True,
 newGameRuns=0,newGpuRuns=0,productionChanged=False,audibleOutput=False,strictPassed=not(missing or extra or diffs or unknown) and [r['handle'] for r in native['rows']]==[r[0] for r in cpp],completeGame=False,bindings=bindings)
H.mkdir()
for name,value in [('qualified.json',summary),('private-differences.json',diffs),('private-unmeasured-links.json',unknown),('native-canonical.json',dict(fields=fields,rows=list(nrows.values())) )]:
 (H/name).write_text(json.dumps(value,indent=2)+'\n')
print(json.dumps({k:v for k,v in summary.items() if k not in ['bindings','nativeInventory','cppInventory','missingLiteralHandles','extraLiteralHandles','differentWordsByFamilies']}))
