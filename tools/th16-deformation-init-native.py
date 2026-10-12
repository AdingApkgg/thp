"""TH16 original deformation constructor and strip factory with controlled VM creation/allocator."""
import hashlib,importlib,json,struct
from pathlib import Path
from unicorn import *
from unicorn.x86_const import *
ROOT=Path(__file__).resolve().parents[1]
OBJ,STACK,RETURN,VMBASE=0x70001000,0x700ff000,0x70000000,0x70100000
def main():
 img,t,d=importlib.import_module('th-anm-handlers').handlers(16);m=Uc(UC_ARCH_X86,UC_MODE_32)
 for _,base,size,raw,n in img.sections:
  start=base&~4095;m.mem_map(start,((base+size+4095)&~4095)-start);m.mem_write(base,img.data[raw:raw+n])
 m.mem_map(RETURN,0x200000)
 put=lambda p,v:m.mem_write(p,struct.pack('<I',v&0xffffffff))
 get=lambda p:struct.unpack('<I',m.mem_read(p,4))[0]
 allocations=[];creations=[];cursor=[0x70010000]
 def boundary(machine,address,size,user):
  sp=m.reg_read(UC_X86_REG_ESP)
  if address==0x477fa7:
   n=get(sp+4);p=cursor[0];cursor[0]=(p+n+127)&~127;m.mem_write(p,bytes(n));allocations.append(n);m.reg_write(UC_X86_REG_EAX,p)
  elif address==0x406380:
   out,script,layer,flag=(get(sp+4+n*4) for n in range(4));idx=len(creations);vm=VMBASE+idx*0x1000;put(out,idx+1);put(vm+0x18,layer);put(vm+0x530,6);creations.append(dict(script=script,layer=layer,flag=flag,vm=vm));m.reg_write(UC_X86_REG_EAX,out)
  else:m.reg_write(UC_X86_REG_EAX,VMBASE+(get(sp+4)-1)*0x1000)
 for addr,cleanup in ((0x477fa7,0),(0x406380,16),(0x46efa0,4)):
  m.mem_write(addr,b'\xc2'+struct.pack('<H',cleanup) if cleanup else b'\xc3');m.hook_add(UC_HOOK_CODE,boundary,begin=addr,end=addr)
 rows=[]
 for height in (7,17,25,33):
  m.mem_write(OBJ,bytes(0x100));m.mem_write(VMBASE,bytes(17*0x1000));cursor[0]=0x70010000;allocations.clear();creations.clear();put(0x4c127c,1);m.mem_write(STACK,struct.pack('<IIII',RETURN,17,height,0));m.reg_write(UC_X86_REG_ESP,STACK);m.reg_write(UC_X86_REG_ECX,OBJ)
  m.emu_start(0x418c70,RETURN,count=1000000);assert m.reg_read(UC_X86_REG_EIP)==RETURN
  vms=[]
  for n,c in enumerate(creations):
   vm=c['vm'];words=list(struct.unpack('<'+'I'*(height*56//4),m.mem_read(get(vm+0x5b8),height*56))) if n else []
   vms.append(dict(script=c['script'],layer=get(vm+0x18),size=get(vm+0x5bc),flags=get(vm+0x530),flags2=get(vm+0x534),segments=get(vm+0x4a0),selectors=[get(vm+0x5c4+i*4) for i in range(6)],hasContext=get(vm+0x5ec)==OBJ,words=words))
  for i in range(17*height):
   m.mem_write(get(OBJ+0x14)+i*28,struct.pack('<ffffIff',i*.25,-float(i)*.5,float(i%3),1+(i%2)*.125,0xff001000+i,i/1024,-float(i)/256))
  put(STACK,RETURN);m.reg_write(UC_X86_REG_ESP,STACK);m.reg_write(UC_X86_REG_ECX,VMBASE)
  m.emu_start(0x418c60,RETURN,count=1000000);assert m.reg_read(UC_X86_REG_EIP)==RETURN;assert m.reg_read(UC_X86_REG_EAX)==0
  for n,v in enumerate(vms):
   if n:v['copyWords']=list(struct.unpack('<'+'I'*(height*56//4),m.mem_read(get(VMBASE+n*0x1000+0x5b8),height*56)))
  rows.append(dict(height=height,columns=get(OBJ),rows=get(OBJ+4),allocations=allocations,vms=vms))
 out=ROOT/'artifacts/th16/deformation-init-native.json';out.write_text(json.dumps(dict(executableSha256=hashlib.sha256(img.data).hexdigest(),scope='Original constructor418c70 and strip factory43d8b0 execute. VM factory/lookup and malloc are controlled; native calls request script59/layer34, control VM and sixteen strips, dimensions/allocation, modes, callback selector4/context and strip z/rhw/color initialization are compared. Full retail resource/template binding, Control draw callback418c60 and complete strip copy418f40 execute with deterministic vertex inputs. Rectangle/deformation updates, render targets, draw schedule and GPU are excluded.',rows=rows),separators=(',',':'))+'\n');print(len(rows),'native deformation initializer cases')
if __name__=='__main__':main()
