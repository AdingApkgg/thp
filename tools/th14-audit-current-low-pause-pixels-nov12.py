"""Compare raw pixels and VM state only after both real applications retire."""
from pathlib import Path
import collections,hashlib,importlib.util,json,struct

R=Path(__file__).resolve().parents[1]
H=R/'artifacts/th14/current-low-pause-pixels-nov12'
OLD=R/'artifacts/th14/low-pause-present-capture-nov09'
N,C=OLD/'native-three-sites',H/'current'
load=lambda p:json.loads(p.read_bytes())
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
nr,cr=load(N/'report.json'),load(C/'report.json')
for home,report in [(N,nr),(C,cr)]:
    receipt=load(home/'terminal-receipt.json')
    assert receipt['reaped'] and receipt['exitCode']==0 and receipt['pid']==report['pid']
assert nr['childExited'] and nr['frameReadbackCompleted'] and not nr['error']
assert not nr['debuggerAttached'] and nr['originalAttractFlagPreserved']
assert nr['originalCodeWrites']==21 and nr['gameStateWrites']==nr['rngOrCounterWrites']==0
assert sha(N/'observer-source.py')==nr['sourceSha256']
assert cr['terminal'] and cr['closed'] and cr['captureComplete'] and not cr['exception'] and not cr['errors']
assert cr['gpuContextClosed'] and cr['platformRetired'] and not cr['resourceLeaks']
assert all(w['closed'] and w['exitCode']==0 for w in cr['physicalWorkers'])
assert not cr['referenceRowsOrPixelsReadDuringExecution']
build=load(H/'component/build.json')
assert cr['wasmSha256']==build['wasmSha256']=='5077fb209e0dfef46cd3bb17d80168b39be699a4b3f9da75c539410249486169'
assert sha(H/'component/candidate.wasm')==build['wasmSha256']
for p,d in {**build['sourceBindingsByMode']['candidate'],**build['objectBindings']}.items():assert sha(R/p)==d,p
assert load(H/'prepared.json')['driverSha256']==sha(R/'tools/th14-run-current-low-pause-pixels-nov12.mjs')
assert load(H/'host-preflight.json')['setupBindingsVerified']

native=load(N/'live-vms-before-readback.json')
assert native['readOnly'] and native['readBeforeDiagnosticD3dCalls'] and native['complete']
tool=R/'tools/th14-native-title-live-compare-oct27.py'
assert sha(tool)=='c7866f2c3d6e030bae1e4c5153b196f7500436b43e710fc181730bf087a3f9cc'
spec=importlib.util.spec_from_file_location('native303',tool)
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
# Retain genuinely absent native links explicitly, without inventing an ID.
source=tool.read_text()
old='        assert not address or address in by_address'
assert source.count(old)==1
source=source.replace(old,"        if address and address not in by_address:return {'unmeasuredNativeVmAddress':address}")
exec(compile(source,str(tool),'exec'),m.__dict__)
address_map={r['address']:r['handle'] for r in native['rows']}
nrows={};unmeasured=[];fields=None
for row in native['rows']:
    fields,words=m.native_words(row,address_map)
    assert len(fields)==len(words)==303
    assert row['handle'] not in nrows
    nrows[row['handle']]=words
    for i,x in enumerate(words):
        if isinstance(x,dict):unmeasured.append(dict(handle=row['handle'],field=fields[i],**x))
raw=(C/'target-live-vms.u32').read_bytes()
w=struct.unpack('<'+'I'*(len(raw)//4),raw)
assert w[1:3]==(3,1200) and w[4:6]==(1,303) and len(w)==6+w[3]*303
cpp=[list(w[i:i+303]) for i in range(6,len(w),303)]
byid={row[0]:row for row in cpp}
assert len(byid)==len(cpp)
missing=sorted(nrows.keys()-byid.keys());extra=sorted(byid.keys()-nrows.keys())
differences=[];measured=0
for h,a in nrows.items():
    if h not in byid:continue
    for i,(x,y) in enumerate(zip(a,byid[h])):
        if isinstance(x,dict):continue
        measured+=1
        if x!=y:differences.append(dict(handle=h,file=a[1],script=a[2],index=i,field=fields[i],native=x,cpp=y))
order=[r['handle'] for r in native['rows']]==[r[0] for r in cpp]
an=(N/'native-before-present-1200.bgra').read_bytes()
ac=(C/'application-stage3-frame1200.bgra').read_bytes()
assert len(an)==len(ac)==640*480*4
assert hashlib.sha256(an).hexdigest()==nr['readback']['pixelSha256']
different_pixels=sum(an[i:i+4]!=ac[i:i+4] for i in range(0,len(an),4))
channels=[sum(an[i]!=ac[i] for i in range(k,len(an),4)) for k in range(4)]
ncam=struct.unpack('<75I',(N/'present-world-camera.u32').read_bytes())
ccam=struct.unpack('<75I',(C/'present-world-camera.u32').read_bytes())
camera_diffs=[dict(index=i,native=a,cpp=b) for i,(a,b) in enumerate(zip(ncam,ccam)) if a!=b]
nraw=(N/'logger-rows.u32').read_bytes();craw=(C/'observations.u32').read_bytes()
assert len(nraw)%528==len(craw)%456==0
nn,cn=len(nraw)//528,len(craw)//456
raw_diffs=collections.Counter();first={};prefix=0
for i in range(min(nn,cn)):
    n=struct.unpack_from('<132I',nraw,i*528);c=struct.unpack_from('<114I',craw,i*456)
    assert n[0]==c[0]==i+1
    assert n[110]&31==31, 'All native replay cursor coordinates must be actually measured'
    left=list(n[1:110])+list(n[117:119])+[n[113],n[119]]
    assert len(left)==113
    changed=False
    for j,(a,b) in enumerate(zip(left,c[1:])):
        if a!=b:
            changed=True;raw_diffs[j]+=1
            first.setdefault(j,dict(callback=i+1,native=a,cpp=b))
    if not changed and prefix==i:prefix+=1

result=dict(terminal=True,nativeVms=len(nrows),cppVms=len(cpp),wordsPerVm=303,
    measuredVmWords=measured,unmeasuredNativeLinks=len(unmeasured),
    missingVmHandles=missing,extraVmHandles=extra,strictRegistryOrderEqual=order,
    differentVmWords=len(differences),strictVmEqual=not(missing or extra or differences or unmeasured) and order,
    groupedDifferences=[dict(file=k[0],script=k[1],field=k[2],count=v) for k,v in collections.Counter((d['file'],d['script'],d['field']) for d in differences).most_common()],
    fullBufferPixelsExact=an==ac,differentPixels=different_pixels,differentChannels=channels,
    postFrameCameraWordsExact=not camera_diffs,postFrameCameraDifferences=camera_diffs,
    nativeCallbacks=nn,cppCallbacks=cn,beforePlayerStrict113AllExact=nn==cn and not raw_diffs,
    beforePlayerStrict113Prefix=prefix,raw113DifferenceCounts=dict(raw_diffs),raw113FirstDifferences=first,
    nativePlayerCallbacksAtPresent=nr['readback']['playerCallbacks'],cppCallbacksAtFrameCommit=w[0],
    noDebuggerOrAfterResumeSuspensions=True,noReferenceGameplayValuesSupplied=True,
    noPixelToleranceOrExcludedRegions=True,allOwnedResourcesRetired=True,
    originalPresentNotCompletedAndNativeExitNotNatural=True,allModesAccepted=False,completeGame=False,
    wasmSha256=cr['wasmSha256'],productionChanged=False,currentGameSource='e6b15d27768ee4da293c81c3c239e3d42880020b',
    originalNativeReferenceReused=True,newOriginalGameOrAssets=False,allFourCursorCoordinatesActuallyMeasured=True,
    bindings={p.relative_to(R).as_posix():sha(p) for p in [Path(__file__),tool,N/'report.json',N/'observer-source.py',
        N/'terminal-receipt.json',C/'report.json',C/'terminal-receipt.json',H/'prepared.json',H/'component/build.json',H/'host-preflight.json',
        N/'logger-rows.u32',C/'observations.u32',N/'target-vms.raw',C/'target-live-vms.u32',
        N/'native-before-present-1200.bgra',C/'application-stage3-frame1200.bgra',
        N/'present-world-camera.u32',C/'present-world-camera.u32']})
for name,value in [('vm-private-differences.json',differences),('vm-private-unmeasured-links.json',unmeasured),('qualified.json',result)]:
    p=H/name;assert not p.exists();p.write_text(json.dumps(value,indent=2)+'\n')
print(json.dumps({k:v for k,v in result.items() if k not in ['bindings','groupedDifferences','raw113FirstDifferences']}))
print(json.dumps(result['groupedDifferences'][:15]))
