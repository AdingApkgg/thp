"""Trace the actual451760->453a90->452050 chain and its scratch writer.

Synthetic allocation addresses are declared ABI interventions. This is not a
live process capture or a native address stream supplied to the portable game.
"""
from pathlib import Path
import argparse
import collections,hashlib,importlib,itertools,json,struct,sys
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools'))
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--output',type=Path,required=True)
args=parser.parse_args();out=args.output.resolve()
assert out.is_relative_to(R/'artifacts/th14')and not out.exists()
out.mkdir(parents=True)
from unicorn import Uc,UC_ARCH_X86,UC_MODE_32,UC_HOOK_CODE,UC_HOOK_MEM_READ,UC_HOOK_MEM_WRITE,UC_MEM_READ
from unicorn.x86_const import *
im=importlib.import_module('th12-pe').Image('H:/Games/th/14/th14.exe');SHA=lambda raw:hashlib.sha256(raw).hexdigest()
assert SHA(im.data)=='f08e885e28d2e0fc8c579e88034dd7de8f2a648d8f08ce781cf08eadc9ffe353'
m=Uc(UC_ARCH_X86,UC_MODE_32)
for _,address,size,offset,length in im.sections:
 first=address&~4095;m.mem_map(first,((address+size+4095)&~4095)-first);m.mem_write(address,im.data[offset:offset+length])
base=0x70000000;m.mem_map(base,0x100000)
ret,shot,area,player,visual,spec,stack=base,base+0x1000,base+0x2000,base+0x10000,base+0x30000,base+0x40000,base+0xff000
items=0x72000000;m.mem_map(items,0xe00000)
targets=[0x08000030,0x0d801234,0x19000678,0x30001234,0x3f001234]
for target in targets:m.mem_map(target&~4095,4096)
put=lambda p,value:m.mem_write(p,struct.pack('<I',value&0xffffffff))
get=lambda p:struct.unpack('<I',m.mem_read(p,4))[0]
floats=lambda p,*values:m.mem_write(p,struct.pack('<'+'f'*len(values),*values))
events=[];effects=[];writes=[];accesses=[];focused_entries=[];scratch=stack-56;skip_rewards=False
def memory_hook(machine,access,address,size,value,user):
 pc=m.reg_read(UC_X86_REG_EIP)
 if access==UC_MEM_READ:
  accesses.append(dict(pc=pc,address=address,size=size,value=get(scratch),lastWrite=writes[-1]if writes else None))
 else:writes.append(dict(pc=pc,address=address,size=size,value=value&0xffffffff))
m.hook_add(UC_HOOK_MEM_READ|UC_HOOK_MEM_WRITE,memory_hook,begin=scratch,end=scratch+3)
def code_hook(machine,pc,size,user):
 sp=m.reg_read(UC_X86_REG_ESP)
 if pc==0x453a90:
  if skip_rewards:
   m.reg_write(UC_X86_REG_EAX,0);m.reg_write(UC_X86_REG_ESP,sp+4);m.reg_write(UC_X86_REG_EIP,get(sp))
  return
 if pc==0x452050:
  focused_entries.append(dict(esp=sp,scratch=sp-16,value=get(sp-16)));return
 if pc==0x47f140:events.append(dict(kind='interrupt',label=get(sp+8)));cleanup=8
 elif pc==0x46e470:events.append(dict(kind='sound',sound=get(sp+4)));cleanup=4
 else:
  pointer=get(sp+12);effects.append(dict(script=get(sp+8),position=[get(pointer+i*4)for i in range(3)],rotation=get(sp+16)));events.append(dict(kind='factory',script=get(sp+8)));cleanup=28
 m.reg_write(UC_X86_REG_EAX,0);m.reg_write(UC_X86_REG_ESP,sp+4+cleanup);m.reg_write(UC_X86_REG_EIP,get(sp))
for pc in [0x453a90,0x452050,0x47f140,0x46e470,0x47ed10]:m.hook_add(UC_HOOK_CODE,code_hook,begin=pc,end=pc)
cases=[];controls=[]
main_inputs=[(*values,False,0)for values in itertools.product(targets,[0.,.1,-.1],[0,499,500,1200],[0,99,100,501],[0,0x9630],[8,32])]
control_inputs=[(target,0.,0,0,0,8,True,poison)for target,poison in itertools.product(targets,[0,0x3f800000,0x67800000])]
for target,shot_z,plain,focused,seed,age,skip_rewards,poison in main_inputs+control_inputs:
 for p,n in [(shot,0x100),(area,0x100),(player,0x19000),(spec,0x80),(stack-0x2000,0x2100)]:m.mem_write(p,bytes(n))
 put(0x4db67c,player);put(0x4db660,items);put(0x4db53c,visual);put(visual+0x10,visual+0x100)
 put(shot+0x14,73);put(shot+0xc0,area);put(shot+0xbc,spec);put(spec+0x34,0x452050)
 put(area+0x98,shot);floats(area+0x2c,240,123,.2);floats(target,240,123,.3)
 put(shot+0x18,age-1);put(shot+0x1c,age);floats(shot+0x54,17,123,shot_z);floats(shot+0x6c,8,-1.25)
 floats(shot+0xb8,8);put(shot+0x40,9);put(shot+0x44,10);floats(shot+0x48,10);put(shot+0x4c,0x4d8f58);put(shot+0x50,1)
 floats(area+0x14,32);put(area+0x84,19);put(player+0x184b4,plain);put(player+0x184b8,focused)
 put(0x4f5858,160);put(0x4f5860,40);put(0x4db508,seed);put(0x4db50c,123);put(0x4db510,54321);put(0x4db514,17);floats(0x4d8f58,1)
 put(stack,ret);put(stack+4,0);put(stack+8,0);put(stack+12,0)
 for register,value in [(UC_X86_REG_ESP,stack),(UC_X86_REG_ECX,area),(UC_X86_REG_EDX,target),(UC_X86_REG_EDI,0x10203040),(UC_X86_REG_ESI,0x20304050),(UC_X86_REG_EBX,0x30405060),(UC_X86_REG_FPCW,0x37f),(UC_X86_REG_FPSW,0),(UC_X86_REG_FPTAG,0xffff),(UC_X86_REG_MXCSR,0x1f80)]:m.reg_write(register,value)
 put(scratch,poison)
 events.clear();effects.clear();writes.clear();accesses.clear();focused_entries.clear()
 m.emu_start(0x451760,ret,count=1000000);assert m.reg_read(UC_X86_REG_EIP)==ret
 assert len(focused_entries)==len(effects)==1 and effects[0]['script']==149
 expected=poison if skip_rewards else target
 assert focused_entries[0]==dict(esp=stack-40,scratch=scratch,value=expected),focused_entries
 first_read=next(row for row in accesses if row['pc']==0x4520f2)
 assert first_read['value']==expected
 if skip_rewards:assert first_read['lastWrite']is None,first_read
 else:assert first_read['lastWrite']==dict(pc=0x453aae,address=scratch,size=4,value=target),first_read
 assert effects[0]['position'][2]==get(scratch)
 if shot_z==0:assert effects[0]['position'][2]==expected
 (controls if skip_rewards else cases).append(dict(skippedRewardConsumer=skip_rewards,declaredPriorScratch=poison,targetAddress=target,shotZ=shot_z,plain=plain,focused=focused,seed=seed,age=age,firstRead=first_read,factory=effects[0],focusedEntry=focused_entries[0],targetSlotAccesses=accesses,targetSlotWrites=writes))
assert len(cases)==960 and len(controls)==15
result=dict(schema='th14/focused-hit-stack-producer/1',originalExecutableSha256=SHA(im.data),cases=len(cases),allLastWriters453aaePushEdi=True,allScratchInputsEqualTargetPointer=True,originalRewardChainExecuted=True,instructionBytesPatched=0,controlledBoundaries=['47f140 ANM interrupt','47ed10 effect allocation','46e470 sound'],declaredSyntheticAddresses=targets,skippedRewardControls=len(controls),allSkippedRewardControlsRetainPriorScratch=True,controlRows=controls,rows=cases,toolSha256=SHA(Path(__file__).read_bytes()),liveStackProducerObserved=False,productionChanged=False,completeGame=False,nativeEquivalent=False)
(out/'run-tool.py').write_bytes(Path(__file__).read_bytes())
(out/'common-hit-native.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:result[k]for k in ['cases','allLastWriters453aaePushEdi','allScratchInputsEqualTargetPointer','liveStackProducerObserved']}))
