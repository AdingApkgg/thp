"""Execute the original shake destructor with controlled heap and lock services."""
from pathlib import Path
import argparse,hashlib,importlib,json,struct
from unicorn import Uc,UC_ARCH_X86,UC_MODE_32,UC_HOOK_CODE
from unicorn.x86_const import *
R=Path(__file__).resolve().parents[1];sha=lambda b:hashlib.sha256(b).hexdigest()
def observe():
 im,*_=importlib.import_module('th-anm-handlers').handlers(14);dll=importlib.import_module('th12-pe').Image('C:/Windows/SysWOW64/ntdll.dll')
 assert sha(im.data)=='f08e885e28d2e0fc8c579e88034dd7de8f2a648d8f08ce781cf08eadc9ffe353' and sha(dll.data)=='23d7772221e7a763ccf3f3fe39592086eb3091603554c4981f0ab430fa2ca686'
 m=Uc(UC_ARCH_X86,UC_MODE_32)
 for image in [im,dll]:
  for _,address,size,raw,n in image.sections:
   first=address&~4095;m.mem_map(first,((address+size+4095)&~4095)-first);m.mem_write(address,image.data[raw:raw+n])
 base,stack,manager=0x70000000,0x7000f000,0x70003000;m.mem_map(base,0x10000);m.mem_map(0,0x1000)
 enter=base+0x100;leave=dll.image_base+333408;free=0x4854fe;m.mem_write(enter,bytes.fromhex('c20400'))
 assert dll.read(leave,18).hex()=='8bff558bec83ec0853568b750857834608ff'
 put=lambda a,v:m.mem_write(a,struct.pack('<I',v&0xffffffff));get=lambda a:struct.unpack('<I',m.mem_read(a,4))[0]
 put(0x18,base+0x3000);put(0x4b1078,enter);put(0x4b107c,leave)
 free_args=[];observations=[];enters=[]
 def hook(machine,pc,size,user):
  if pc==enter:
   cs=get(m.reg_read(UC_X86_REG_ESP)+4);assert cs==0x4f56d0;put(cs+4,-2);put(cs+8,1);enters.append(cs)
  elif pc==free:
   sp=m.reg_read(UC_X86_REG_ESP);free_args.append(get(sp+4));m.reg_write(UC_X86_REG_EIP,get(sp));m.reg_write(UC_X86_REG_ESP,sp+4)
  elif pc==leave+10:
   sp=m.reg_read(UC_X86_REG_ESP);observations.append({'savedEsi':get(sp),'registerEsi':m.reg_read(UC_X86_REG_ESI),'returnPc':get(sp+20)})
 m.hook_add(UC_HOOK_CODE,hook,begin=enter,end=enter);m.hook_add(UC_HOOK_CODE,hook,begin=free,end=free);m.hook_add(UC_HOOK_CODE,hook,begin=leave+10,end=leave+10)
 rows=[]
 for object_offset,node_offset in [(0x1000,0x2000),(0x1400,0x2400),(0x1800,0x2800),(0x1c00,0x2c00)]:
  obj,node=base+object_offset,base+node_offset;assert obj!=node
  m.mem_write(obj,bytes(128));m.mem_write(node,bytes(64));m.mem_write(manager,bytes(128));m.mem_write(stack-0x300,bytes(0x400))
  put(obj+8,node);put(obj+12,0);put(node+4,1);put(node+8,0x12345678);put(manager+0x14,node);put(manager+0x18,0);put(manager+0x1c,manager+0x20);put(manager+0x24,0);put(0x4db51c,manager);m.mem_write(0x4f5815,b'\1');m.mem_write(0x4f5808,b'\0');put(stack,base)
  free_args.clear();observations.clear();enters.clear();m.reg_write(UC_X86_REG_ESP,stack);m.reg_write(UC_X86_REG_ECX,obj);m.reg_write(UC_X86_REG_ESI,0x13572468);m.reg_write(UC_X86_REG_EBX,0x24681357)
  m.emu_start(0x46d180,base,count=10000);assert m.reg_read(UC_X86_REG_EIP)==base
  assert free_args==[node,obj] and len(enters)==1 and len(observations)==1
  o=observations[0];assert o['savedEsi']==o['registerEsi']==obj and o['returnPc']==0x46d4a7 and o['savedEsi']!=node,(o,hex(obj),hex(node))
  rows.append({'object':obj,'node':node,'freeArgs':list(free_args),'savedEsi':o['savedEsi'],'leaveReturnPc':hex(o['returnPc'])})
 return {'passed':True,'originalExecutableSha256':sha(im.data),'ntdllSha256':sha(dll.data),'cases':rows,'actualOriginalDestructorAndLeaveInstructions':True,'declaredServices':'uncontended lock entry and CRT free are controlled stubs; no Windows heap allocator is emulated','objectAddressesSynthetic':True,'dynamicHeapAddressPredictionImplemented':False,'historicalExactAddressNotPredicted':True,'completeGame':False,'nativeEquivalent':False,'toolSha256':sha(Path(__file__).read_bytes())}
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);a=p.parse_args();out=a.output.resolve();assert out.is_relative_to(R/'artifacts/th14') and not out.exists();out.parent.mkdir(parents=True,exist_ok=True);result=observe();out.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'passed':True,'cases':len(result['cases']),'originalInstructionsExecuted':True,'completeGame':False}))
