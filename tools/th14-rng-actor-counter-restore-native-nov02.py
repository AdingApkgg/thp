"""Observe original shake stack writes through the pinned real ntdll leave path.

Synthetic callback inputs and a declared uncontended EnterCriticalSection
service. Original shake, timer, RNG and RtlLeaveCriticalSection run intact.
No OS process, game input, window or physical device is created.
"""
from pathlib import Path
import argparse,hashlib,importlib,itertools,json,struct
from unicorn import Uc,UC_ARCH_X86,UC_MODE_32,UC_HOOK_CODE,UC_HOOK_MEM_WRITE,UC_HOOK_MEM_INVALID
from unicorn.x86_const import *
R=Path(__file__).resolve().parents[1];SHA=lambda b:hashlib.sha256(b).hexdigest()
EXE='f08e885e28d2e0fc8c579e88034dd7de8f2a648d8f08ce781cf08eadc9ffe353'
DLL='23d7772221e7a763ccf3f3fe39592086eb3091603554c4981f0ab430fa2ca686'

def observe():
 image,*_=importlib.import_module('th-anm-handlers').handlers(14)
 dll=importlib.import_module('th12-pe').Image('C:/Windows/SysWOW64/ntdll.dll')
 assert SHA(image.data)==EXE and SHA(dll.data)==DLL
 leave=dll.image_base+333408
 assert dll.read(leave,18).hex()=='8bff558bec83ec0853568b750857834608ff'
 m=Uc(UC_ARCH_X86,UC_MODE_32)
 for im in [image,dll]:
  for _,address,size,raw,length in im.sections:
   first=address&~4095;m.mem_map(first,((address+size+4095)&~4095)-first);m.mem_write(address,im.data[raw:raw+length])
 base,obj,stage=0x70000000,0x70001000,0x70002000
 m.mem_map(base,0x10000);m.mem_map(0,0x1000);enter=base+0x100
 # The declared acquisition establishes only an uncontended critical section.
 # Leave executes original DLL bytes, including both saved-register writes.
 m.mem_write(enter,bytes.fromhex('c20400'))
 put=lambda p,v:m.mem_write(p,struct.pack('<I',v&0xffffffff))
 get=lambda p:struct.unpack('<I',m.mem_read(p,4))[0]
 bits=lambda f:struct.unpack('<I',struct.pack('<f',f))[0]
 # Declared synthetic TEB: Unicorn's FS base is zero. No critical-section
 # per-thread tracking table is installed; the original DLL reads that zero.
 put(0x18,base+0x3000)
 put(0x4b1078,enter);put(0x4b107c,leave)
 writes=[];draws=[];slot=0;active=False;enters=0;leaves=0;restored=False
 invalid=[]
 def invalid_memory(machine,access,address,size,value,user):
  invalid.append(dict(pc=m.reg_read(UC_X86_REG_EIP),access=access,address=address,size=size));return False
 m.hook_add(UC_HOOK_MEM_INVALID,invalid_memory)
 def code(machine,pc,size,user):
  nonlocal enters,leaves
  if pc==0x403336 and not restored:m.emu_stop()
  elif pc==enter:
   cs=get(m.reg_read(UC_X86_REG_ESP)+4);assert cs==0x4f57c0
   put(cs+4,-2);put(cs+8,1);enters+=1
  elif pc==leave:leaves+=1
  elif pc in [0x46ce4f,0x46cecf,0x46d042,0x46d0c9]:
   draws.append(dict(returnPc=pc,value=m.reg_read(UC_X86_REG_EAX),esp=m.reg_read(UC_X86_REG_ESP)))
 def memory(machine,access,address,size,value,user):
  if not active or address>=slot+4 or address+size<=slot-4:return
  assert size<=8,'Inspect any wider stack write rather than guessing its high words'
  writes.append(dict(pc=m.reg_read(UC_X86_REG_EIP),address=address,size=size,value=value))
 m.hook_add(UC_HOOK_CODE,code,begin=0x403336,end=0x403336)
 m.hook_add(UC_HOOK_CODE,code,begin=enter,end=enter)
 m.hook_add(UC_HOOK_CODE,code,begin=leave,end=leave)
 for pc in [0x46ce4f,0x46cecf,0x46d042,0x46d0c9]:m.hook_add(UC_HOOK_CODE,code,begin=pc,end=pc)
 m.hook_add(UC_HOOK_MEM_WRITE,memory,begin=base+0xed00,end=base+0xff00)
 rows=[]
 for kind,rate,seed,timer,flags,stopped,prior,alignment in itertools.product(
  ['normal','phased'],[.5,1.,1.25],[0,1337,65535],[-1,0,15,28,48,50,52],[0,1],[0,1],[0,0xdeadbeef],[0,4]):
  active=False;stack=base+0xf000+alignment;slot=stack-56
  m.mem_write(stack-0x400,bytes(0x500));m.mem_write(obj,bytes(0x100));m.mem_write(stage,bytes(0x100))
  put(slot,prior);put(slot-4,prior);put(stack,base)
  put(0x4db558,stage);put(stage+0x80,flags);put(0x4f56c8,stopped);put(0x4d8f58,bits(rate))
  put(0x4db508,seed);put(0x4db50c,4);put(0x4db510,seed);put(0x4db514,4)
  put(0x4f5814,0x100);put(0x4f7a6c,bits(1.5));put(0x4d9610,bits(3.));put(0x4d9614,bits(-5.))
  fields={0x1c:6 if kind=='phased'else 48,0x20:17 if kind=='phased'else 12,
   0x24:31 if kind=='phased'else 0,0x28:3,0x30:timer-1,0x34:timer,0x38:bits(float(timer)),0x3c:0x4d8f58,0x40:1}
  for offset,value in fields.items():put(obj+offset,value)
  for reg,value in [(UC_X86_REG_ESP,stack),(UC_X86_REG_ECX,obj),(UC_X86_REG_EBP,base+0xe000),
   (UC_X86_REG_ESI,0x13572468),(UC_X86_REG_EDI,0x24681357),(UC_X86_REG_EBX,0x31415926),
   (UC_X86_REG_MXCSR,0x1f80),(UC_X86_REG_FPCW,0x37f),(UC_X86_REG_FPSW,0),(UC_X86_REG_FPTAG,0xffff)]:m.reg_write(reg,value)
  writes.clear();draws.clear();invalid.clear();enters=leaves=0;restored=False;active=True
  try:
   m.emu_start(0x46cf60 if kind=='phased'else 0x46cda0,base,count=20000)
   if m.reg_read(UC_X86_REG_EIP)==0x403336:
    assert get(0x4db514)==4
    saved=m.context_save()
    assert image.read(0x456129,10).hex()=='c70514b54d0000000000'
    m.emu_start(0x456129,0x456133,count=1)
    assert m.reg_read(UC_X86_REG_EIP)==0x456133 and get(0x4db514)==0
    m.context_restore(saved);restored=True
    m.emu_start(0x403336,base,count=20000)
  except Exception as exc:raise RuntimeError(json.dumps(dict(error=str(exc),pc=hex(m.reg_read(UC_X86_REG_EIP)),kind=kind,rate=rate,seed=seed,timer=timer,flags=flags,stopped=stopped,invalid=invalid)))from exc
  active=False
  assert m.reg_read(UC_X86_REG_EIP)==base
  target=get(slot);neighbor=get(slot-4);rng=0x4db510 if kind=='phased'else 0x4db508
  assert enters==leaves==len(draws) and len(draws)in [0,2]
  last=[w for w in writes if w['address']<=slot and slot+4<=w['address']+w['size']]
  if draws:
   expected=(draws[-1]['value']&65535)if kind=='phased'else rng
   assert target==expected,(kind,rate,seed,timer,hex(target),hex(expected))
   assert last and last[-1]['pc']==leave+(8 if kind=='phased'else 9)
   if kind=='phased':assert neighbor==rng and neighbor!=target
  rows.append(dict(kind=kind,rate=rate,seed=seed,timer=timer,stageFlags=flags,stopped=stopped,prior=prior,
   alignment=alignment,initialCalls=4,workerCounterRestoreDelivered=restored,callbackEntryEsp=stack,observedSlot=slot,result=m.reg_read(UC_X86_REG_EAX),
   stackWord=target,neighborWord=neighbor,lastWrites=writes[:],rngReturns=draws[:],rng=[get(rng)&65535,get(rng+4)],
   timerWords=[get(obj+o)for o in [0x30,0x34,0x38]],offsetWords=[get(0x4d9610),get(0x4d9614)],lockEnterCalls=enters,lockLeaveCalls=leaves))
 assert len(rows)==2016
 return dict(schema='th14/rng-actor-counter-restore-original/1',executableSha256=EXE,ntdllSha256=DLL,
  ntdllImageBase=dll.image_base,rtlLeaveRva=333408,rtlLeavePrefixSha256=SHA(dll.read(leave,18)),
  shakeCodeSha256=SHA(image.read(0x46cda0,0x3d1)),toolSha256=SHA(Path(__file__).read_bytes()),
  cases=rows,originalInstructionsUnmodified=True,actualNtdllLeaveExecuted=True,
  declaredUncontendedAcquisitionService=True,syntheticCallbackInputsAndStackDeclared=True,
  actualOriginalWorkerCounterStoreExecuted=True,workerCounterStorePc=0x456129,controlledInterleaveBeforeFirstRead=True,
  syntheticTebWithoutCriticalSectionTrackingDeclared=True,
  liveOriginalProcess=False,actualControllerReaderExecuted=False,productionChanged=False,
  completeGame=False,nativeEquivalent=False)

if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 out=a.output.resolve();assert out.is_relative_to(R/'artifacts/th14')and not out.exists();out.parent.mkdir(parents=True,exist_ok=True)
 try:result=observe()
 except Exception as exc:
  out.with_suffix('.error.json').write_text(json.dumps(dict(error=str(exc),toolSha256=SHA(Path(__file__).read_bytes())),indent=2)+'\n',encoding='utf8')
  out.with_suffix('.error-source.py').write_bytes(Path(__file__).read_bytes());raise
 out.write_text(json.dumps(result,indent=2)+'\n',encoding='utf8')
 print(json.dumps(dict(cases=len(result['cases']),rngActive=sum(bool(r['rngReturns'])for r in result['cases']),originalNtdllExecuted=True,productionChanged=False)))
