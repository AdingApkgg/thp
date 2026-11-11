"""Execute retail updates on a declared clone of the captured backdrop VM.

No game process: retain opaque native words, rebind pointers to the same loaded
resource, change only the five physical fields differing in the C++ observation.
This is a component counterfactual, never an input to the live portable engine.
"""
from pathlib import Path
import hashlib,importlib,importlib.util,json,struct,sys
from unicorn import Uc,UC_ARCH_X86,UC_MODE_32,UC_HOOK_MEM_WRITE
from unicorn.x86_const import *
R=Path(__file__).resolve().parents[1]
H=R/'artifacts/th14/current-first-present-vm303-nov12/embedded195-native-v2'
assert not H.exists();H.mkdir()
sys.path.insert(0,str(R/'tools'))
load=lambda p:json.loads(p.read_bytes())
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
parent=R/'artifacts/th14/current-first-present-vm303-nov12'
qualified=load(parent/'private-vms-qualified.json')
for p,d in qualified['bindings'].items():assert sha(R/p)==d,p
retained=load(parent/'private-embedded-canonical.json')[4]
assert retained['index']==4
native_meta=R/'artifacts/th14/current-startup-prefix-nov10/native/transition-before-readback.json'
raw=bytes.fromhex(load(native_meta)['geometryHex'])[4*1484:5*1484]
assert len(raw)==1484
fields=retained['fields'];native_words=retained['native'];cpp_words=retained['cpp']
changes=[i for i,(a,b) in enumerate(zip(native_words,cpp_words)) if a!=b]
patch_offsets={'nativeVmWord0x55c':0x55c,'nativeVmWord0x560':0x560,'nativeVmWord0x564':0x564,
 'nativeVmWord0x88':0x88,'nativeVmWord0x8c':0x8c}
assert {fields[i] for i in changes}==set(patch_offsets)|{'ageCurrent'}
assert native_words[1:3]==cpp_words[1:3]==[8,195]
distance=native_words[fields.index('ageCurrent')]-cpp_words[fields.index('ageCurrent')]
assert distance==qualified['nativeTransitionCounter']-qualified['cppTransitionCounter']==3
image,*_=importlib.import_module('th-anm-handlers').handlers(14)
assert hashlib.sha256(image.data).hexdigest()=='f08e885e28d2e0fc8c579e88034dd7de8f2a648d8f08ce781cf08eadc9ffe353'
m=Uc(UC_ARCH_X86,UC_MODE_32)
for _,base,size,offset,n in image.sections:
 first=base&~4095;m.mem_map(first,((base+size+4095)&~4095)-first);m.mem_write(base,image.data[offset:offset+n])
loader_path=R/'tools/th14-native-transition-resource-loader-nov09.py'
loader=importlib.import_module('th14-native-transition-resource-loader-nov09').install(m)
B=0x78000000;VM=B+0x1000;STACK=B+0xff000;STOP=B+0xfe000;m.mem_map(B,0x100000)
put=lambda at,v:m.mem_write(at,struct.pack('<I',v&0xffffffff))
get=lambda at:struct.unpack('<I',m.mem_read(at,4))[0]
def run(entry,owner=VM,args=()):
 m.mem_write(STACK,struct.pack('<'+'I'*(len(args)+1),STOP,*args))
 for reg,value in [(UC_X86_REG_ESP,STACK),(UC_X86_REG_ECX,owner),(UC_X86_REG_MXCSR,0x1f80),
  (UC_X86_REG_FPCW,0x37f),(UC_X86_REG_FPSW,0),(UC_X86_REG_FPTAG,0xffff)]:m.reg_write(reg,value)
 m.emu_start(entry,STOP,count=5000000);assert m.reg_read(UC_X86_REG_EIP)==STOP
 return m.reg_read(UC_X86_REG_EAX)
archive_meta=R/'artifacts/archive-differential/th14.json';extraction=Path(load(archive_meta)['extraction'])
ascii_path=extraction/'ascii.anm';effect_path=extraction/'effect.anm'
assert sha(ascii_path)=='fc1c2295fda07140b475b2ddd45d221920534e4a011c529e76578609d69a9284'
assert sha(effect_path)=='bbd7205654c87677c4a582fc5e99c2884e724f501b3d281c75bf207a76095559'
ascii_resource=loader.load('ascii.anm',ascii_path.read_bytes(),2,1.)
put(loader.manager+0x191e4,ascii_resource.resource)
resource=loader.load('effect.anm',effect_path.read_bytes(),8,1.)
m.mem_write(VM,bytes(1484));run(0x40af00,resource.resource,(VM,195))
# Construct resident script/sprite pointers using actual code; opaque captured
# words remain inputs to the later clone. This is not a reconstructed full run.
for _ in range(11):assert run(0x46fe50)==0
fresh=bytes(m.mem_read(VM,1484));word=lambda data,at:struct.unpack_from('<I',data,at)[0]
assert fresh[0x34:0x38]==raw[0x34:0x38]
script_begin=word(fresh,0x38)
instruction_offset=word(raw,0x28)-word(raw,0x38)
assert instruction_offset==native_words[fields.index('scriptInstructionOffset')]==cpp_words[fields.index('scriptInstructionOffset')]
base=bytearray(raw)
struct.pack_into('<I',base,0x30,word(fresh,0x30))
struct.pack_into('<I',base,0x38,script_begin)
struct.pack_into('<I',base,0x28,script_begin+instruction_offset)
mapper_path=R/'tools/th14-native-title-live-compare-oct27.py'
spec=importlib.util.spec_from_file_location('embedded195_mapper',mapper_path)
mapper=importlib.util.module_from_spec(spec);spec.loader.exec_module(mapper)
def canonical(data):
 w=lambda at:word(data,at)
 row=dict(handle=w(0x540),file=struct.unpack_from('<H',data,0x36)[0],script=struct.unpack_from('<h',data,0x4aa)[0]&0xffffffff,
  timerPrevious=w(0x548),timerCurrent=w(0x54c),timerFraction=w(0x550),pendingInterrupt=w(0x4a0),ageCurrent=w(0x560),rawVmHex=data.hex())
 f,v=mapper.native_words(row,{})
 assert f==fields;return v
assert canonical(base)==native_words
cpp_clone=bytearray(base)
for name,offset in patch_offsets.items():struct.pack_into('<I',cpp_clone,offset,cpp_words[fields.index(name)])
assert canonical(cpp_clone)==cpp_words
external_writes=[];watch=False
def write(machine,access,address,size,value,user):
 if watch and not (VM<=address and address+size<=VM+1484) and not (B+0xf0000<=address and address+size<=STACK+64):
  external_writes.append(dict(pc=machine.reg_read(UC_X86_REG_EIP),address=address,size=size))
m.hook_add(UC_HOOK_MEM_WRITE,write)
cases=[];outputs=[]
for steps,rate in [(0,1.),(2,1.),(distance,1.),(4,1.),(distance,0.),(distance,.5),(distance,1.5),(distance,2.)]:
 m.mem_write(VM,bytes(cpp_clone));m.mem_write(0x4d8f58,struct.pack('<f',rate));rng=bytes(m.mem_read(0x4db508,16));external_writes.clear()
 watch=True
 try:statuses=[run(0x46fe50) for _ in range(steps)]
 finally:watch=False
 actual=canonical(bytes(m.mem_read(VM,1484)))
 assert all(s==0 for s in statuses) and bytes(m.mem_read(0x4db508,16))==rng
 diffs=[dict(field=f,actual=a,expected=b) for f,a,b in zip(fields,actual,native_words) if a!=b]
 cases.append(dict(steps=steps,declaredRate=rate,statuses=statuses,differentCanonicalWords=len(diffs),differences=diffs,
  rngUnchanged=True,externalWrites=list(external_writes)))
 outputs.append(actual)
assert next(x for x in cases if x['steps']==distance and x['declaredRate']==1.)['differentCanonicalWords']==0
assert all(x['differentCanonicalWords']>0 for x in cases if (x['steps'],x['declaredRate'])!=(distance,1.))
paths=[Path(__file__),loader_path,mapper_path,archive_meta,native_meta,parent/'private-vms-qualified.json',parent/'private-embedded-canonical.json',ascii_path,effect_path]
out=dict(actualRetailInterpreter=True,originalUpdateEntry='46fe50',declaredCloneOnly=True,
 sameLoadedEffectScript195=True,residentScriptAndSpritePointersRebound=True,opaqueNativeWordsRetained=True,
 canonicalCppInputMatchesAll303Words=True,fivePhysicalFieldsPatchedOnly=True,
 actualObservedAgeAndTransitionCounterDifference=distance,cases=cases,
 threeActualUpdatesMatchAll303NativeWords=True,noLiveEnginePadding=True,newOriginalGameRuns=0,newGpuRuns=0,
 productionChanged=False,audibleOutput=False,wholeFirstPresentPixelsAccepted=False,completeGame=False,
 bindings={str(p.relative_to(R)).replace('\\','/'):sha(p) for p in paths if p.is_relative_to(R)})
(H/'qualified.json').write_text(json.dumps(out,indent=2)+'\n')
(H/'actual-outputs.json').write_text(json.dumps(outputs)+'\n')
print(json.dumps(dict(cases=len(cases),differentWords=[x['differentCanonicalWords'] for x in cases],distance=distance,actualRetailInterpreter=True)))
