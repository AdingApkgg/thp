"""Compare captured unregistered compositor and type-0 VMs, without new games."""
from pathlib import Path
import hashlib,importlib.util,json,struct
R=Path(__file__).resolve().parents[1]
H=R/'artifacts/th14/current-first-present-vm303-nov12'
N=R/'artifacts/th14/current-startup-prefix-nov10/native'
C=R/'artifacts/th14/control-main-stop-nov12/first-present/candidate-owner-replay'
load=lambda p:json.loads(p.read_bytes())
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
parent=load(H/'qualified.json')
for p,d in parent['bindings'].items():assert sha(R/p)==d,p
tool=R/'tools/th14-native-title-live-compare-oct27.py'
source=tool.read_text();needle='        assert not address or address in by_address'
assert source.count(needle)==1
source=source.replace(needle,"        if address and address not in by_address:return {'unmeasuredNativeVmAddress':address}")
spec=importlib.util.spec_from_file_location('private_vm303',tool)
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);exec(compile(source,str(tool),'exec'),m.__dict__)
live=load(N/'live-vms-before-readback.json')
addresses={struct.unpack_from('<I',bytes.fromhex(r['rawVmHex']),0x570)[0]:r['handle'] for r in live['rows']}
def native(raw):
 assert len(raw)==1484
 w=lambda a:struct.unpack_from('<I',raw,a)[0]
 row=dict(handle=w(0x540),file=struct.unpack_from('<H',raw,0x36)[0],script=struct.unpack_from('<h',raw,0x4aa)[0]&0xffffffff,
  timerPrevious=w(0x548),timerCurrent=w(0x54c),timerFraction=w(0x550),pendingInterrupt=w(0x4a0),ageCurrent=w(0x560),rawVmHex=raw.hex())
 return m.native_words(row,addresses)
geometry=bytes.fromhex(load(N/'transition-before-readback.json')['geometryHex'])
assert len(geometry)==5*1484+8
# The five VMs start at zero; the two scalar words are at the end.
# Interpreting the first eight bytes as a header is invalid.
state,counter=struct.unpack_from('<2I',geometry,5*1484)
cpp=load(C/'transition-after-draw.json')['words'];assert cpp[4:7]==[29,6,303] and len(cpp)==7+6*303
embedded=[];private_rows=[]
for i in range(5):
 fields,a=native(geometry[i*1484:(i+1)*1484]);b=cpp[7+(i+1)*303:7+(i+2)*303]
 unknown=[fields[j] for j,x in enumerate(a) if isinstance(x,dict)]
 changes=[dict(field=f,native=x,cpp=y) for f,x,y in zip(fields,a,b) if not isinstance(x,dict) and x!=y]
 embedded.append(dict(index=i,wordsCompared=303-len(unknown),unknownFields=unknown,differences=changes))
 private_rows.append(dict(index=i,fields=fields,native=a,cpp=b))
copies=load(N/'compositor-before-readback.json');assert copies['readOnly'] and copies['readBeforeDiagnosticCalls']
cw=load(C/'compositor-after-draw.json')['words'];assert cw[1]==4 and len(copies['copies'])==4
offset=2;copy_results=[]
extra_offsets=[0x3c,0x40,0x44,0x48,0x4c,0x50,0x54,0x58,0x5c,0x60,0x64,0x68,0x6c,0x78,0x7c,0x88,0x8c,0x3d8,0x3dc,0x80,0x84,*range(0x3b8,0x3d8,4),*range(0x4ac,0x4cc,4)]
for i,entry in enumerate(copies['copies']):
 assert entry['index']==i
 raw=bytes.fromhex(entry['rawVmHex']);assert len(raw)==1484
 w=lambda at:struct.unpack_from('<I',raw,at)[0]
 head=cw[offset:offset+5];offset+=5;assert head[4]==51
 b=cw[offset:offset+51];offset+=51;flags=w(0x18)
 a=[struct.unpack_from('<h',raw,0x34)[0]&0xffffffff if w(0x30) else 0xffffffff,flags&1,(flags>>25)&31,
  w(0x534),w(0x538),w(0x24),w(0x1c),w(0x548),w(0x54c),w(0x550),w(0x55c),w(0x560),w(0x564),
  *[w(at) for at in extra_offsets],(w(0x28)-w(0x38))&0xffffffff if w(0x28) else 0xffffffff]
 assert len(a)==len(b)==51 and head[2]==b[6]
 changes=[dict(index=j,native=x,cpp=y) for j,(x,y) in enumerate(zip(a,b)) if x!=y]
 copy_results.append(dict(index=i,nativeScript=struct.unpack_from('<h',raw,0x4aa)[0]&0xffffffff,cppScript=head[0],
  measuredWords=51,differentWords=len(changes),differences=changes,wholeNativeFlagsNotCompared=True))
assert offset==len(cw)
paths=[Path(__file__),tool,N/'transition-before-readback.json',N/'compositor-before-readback.json',C/'transition-after-draw.json',C/'compositor-after-draw.json',H/'qualified.json']
out=dict(nativeTransitionState=state,cppTransitionState=cpp[2],nativeTransitionCounter=counter,cppTransitionCounter=cpp[3],
 embedded=embedded,compositorCopies=copy_results,geometryArrayStartsAtZeroAndStateCounterFollowFiveVms=True,
 wrongHeaderOffsetPreviewNotUsed=True,newGameRuns=0,newGpuRuns=0,productionChanged=False,
 wholeFirstPresentPixelsAccepted=False,wholeGameAccepted=False,completeGame=False,
 bindings={p.relative_to(R).as_posix():sha(p) for p in paths})
for name,value in [('private-vms-qualified.json',out),('private-embedded-canonical.json',private_rows)]:
 p=H/name;assert not p.exists();p.write_text(json.dumps(value,indent=2)+'\n')
print(json.dumps(dict(embeddedDifferentWords=[len(x['differences']) for x in embedded],copyDifferentWords=[x['differentWords'] for x in copy_results],nativeCounter=counter,cppCounter=cpp[3])))
