"""Audit a bounded current call-role trace against retained native Main calls."""
from pathlib import Path
from collections import Counter
import hashlib,json,struct
R=Path(__file__).resolve().parents[1]
H=R/'artifacts/th14/option-call-roles-nov12'
C=H/'current'
N=R/'artifacts/th14/option-startup-update-nov09/native'
load=lambda p:json.loads(p.read_bytes())
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
receipt=load(C/'terminal-receipt.json')
assert receipt['reaped'] and receipt['exitCode']==0
report=load(C/'report.json')
assert receipt['pid']==report['pid']
assert all(w['closed'] and w['exitCode']==0 for w in report['physicalWorkers'])
assert report['terminal'] and report['closed'] and report['captureComplete']
assert report['callbacks']==3 and report['stoppedBy']=='declared-target'
assert report['platformRetired'] and not report['resourceLeaks'] and report['gpuContextClosed']
assert not report['exception'] and not report['errors']
native_meta=load(N/'report.json')
native_raw=N/'option-update-prefix.u32'
assert sha(native_raw)==native_meta['readback']['optionUpdateSha256']
native=list(struct.iter_unpack('<32I',native_raw.read_bytes()))
rows=list(struct.iter_unpack('<32I',(C/'option-call-roles.u32').read_bytes()))
assert len(rows)==load(C/'option-call-roles.json')['count']
assert all(r[0]==i+1 and r[1]<3 and r[5:7]==(9,10) for i,r in enumerate(rows))
assert all(r[25]==0 for r in rows), 'Real VM must return success in this bounded trace'
# A registry scope can contain nested factory/interpreter calls. Depth is retained.
main=[r for r in rows if r[2]==1 and r[3]==0 and r[17]==1 and r[30]==0]
handles=sorted({r[4] for r in main})
assert handles==sorted({r[3] for r in native}) and len(handles)==4
fields=[('agePrevious',13,7),('ageCurrent',14,8),('ageFraction',15,9),
 ('rotationZ',16,13),('angularVelocityZ',17,14),('timerPrevious',18,10),
 ('timerCurrent',19,11),('timerFraction',20,12),('flags2',24,27),('pendingInterrupt',25,15)]
differences=[];details=[];compared=0
for handle in handles:
 a=[r for r in native if r[3]==handle]
 b=[r for r in main if r[4]==handle]
 assert [r[8] for r in b]==list(range(b[0][8],b[-1][8]+1))
 assert all(r[18]==r[8] and r[19]==r[8]+1 for r in b)
 by={(r[8],r[1]):r for r in b}
 assert len(by)==len(b)
 for n in a:
  c=by.get((n[14],n[5]))
  if c is None:continue
  for name,ni,ci in fields:
   compared+=1
   if n[ni]!=c[ci]:differences.append(dict(handle=handle,age=n[14],publishedPlayer=n[5],field=name,native=n[ni],cpp=c[ci]))
 details.append(dict(handle=handle,nativeBeforePlayerCalls=sum(r[5]==0 for r in a),
  currentBeforePlayerCalls=sum(r[1]==0 for r in b),firstCurrentRegistryAge=b[0][8],
  nativeUnpairedCoordinates=sorted(set((r[14],r[5]) for r in a)-by.keys()),
  cppUnpairedCoordinates=sorted(by.keys()-set((r[14],r[5]) for r in a))))
raw_native=list(struct.iter_unpack('<132I',(N/'logger-rows.u32').read_bytes()))
raw_current=list(struct.iter_unpack('<114I',(C/'observations.u32').read_bytes()))
assert len(raw_current)==3
raw_differences=[]
for i,c in enumerate(raw_current):
 n=raw_native[i];assert n[0]==c[0]==i+1 and n[110]&31==31
 left=list(n[1:110])+list(n[117:119])+[n[113],n[119]]
 raw_differences.extend(dict(callback=i+1,index=j,native=a,cpp=b) for j,(a,b) in enumerate(zip(left,c[1:])) if a!=b)
initialization=[]
for r in rows:
 if r[2]==0:
  later=[x for x in main if x[31]==r[31] and x[0]>r[0]]
  initialization.append(dict(sequence=r[0],worker=bool(r[3]),ageBefore=r[8],ageAfter=r[19],
   laterRegistryHandles=sorted({x[4] for x in later}),
   firstLaterRegistryAge=later[0][8] if later else None))
bindings={p.relative_to(R).as_posix():sha(p) for p in [Path(__file__),
 R/'tools/th14-option-call-roles-nov12.inc.cpp',R/'tools/th14-build-option-call-roles-nov12.py',
 R/'tools/th14-run-option-call-roles-nov12.mjs',H/'component/build.json',C/'report.json',
 C/'option-call-roles.u32',C/'observations.u32',C/'terminal-receipt.json',native_raw,N/'logger-rows.u32',N/'report.json']}
out=dict(actualCurrentApplication=True,actualRegisteredAndNonregisteredCallsObserved=True,
 boundedPlayerCallbacks=3,currentRows=len(rows),nativeRows=len(native),
 roleCounts=[dict(registryScope=k[0],worker=k[1],nestedDepth=k[2],rows=v)
  for k,v in sorted(Counter((r[2],r[3],r[30]) for r in rows).items())],
 registeredMainRows=len(main),nonregisteredInitialization=initialization,
 rawPlayerWordsCompared=3*113,rawPlayerDifferentWords=len(raw_differences),details=details,sameAgeAndSamePlayerWordsCompared=compared,
 sameAgeAndSamePlayerDifferentWords=len(differences),
 fullNativeFlagWordNotCompared=True,nativeNonregisteredCallsNotMeasured=True,
 schedulingDifferenceNotRepairedByAgeOrRngPadding=True,
 productionChanged=False,audibleOutput=False,newOriginalProcessStarted=False,
 bindings=bindings,completeGame=False)
for name,obj in [('qualified.json',out),('differences.json',differences),('raw-player-differences.json',raw_differences)]:
 p=H/name;assert not p.exists();p.write_text(json.dumps(obj,indent=2)+'\n')
print(json.dumps({k:v for k,v in out.items() if k not in ('bindings','details')}))
