"""Retail47e810 layer traversal into actual478f60 before invisible rejection."""
import hashlib,importlib,itertools,json,struct
from pathlib import Path
from unicorn import Uc,UC_ARCH_X86,UC_MODE_32,UC_HOOK_CODE
from unicorn.x86_const import *
ROOT=Path(__file__).resolve().parents[1]
def main():
 img=importlib.import_module('th-anm-handlers').handlers(14)[0];m=Uc(UC_ARCH_X86,UC_MODE_32)
 for _,b,size,raw,n in img.sections:
  start=b&~4095;m.mem_map(start,((b+size+4095)&~4095)-start);m.mem_write(b,img.data[raw:raw+n])
 base=0x70000000;manager=0x71000000;m.mem_map(base,0x20000);m.mem_map(manager,0x1000000);vms=[base+0x1000+i*0x1000 for i in range(6)];stack=base+0x1f000;callback=base+0x100;events=[];mutation=0
 def put(p,v):m.mem_write(p,struct.pack('<I',v&0xffffffff))
 def get(p):return struct.unpack('<I',m.mem_read(p,4))[0]
 def hook(uc,a,n,u):
  vm=uc.reg_read(UC_X86_REG_ECX);events.append(vms.index(vm));target=get(vm+0x590) if mutation==1 else vm if mutation==2 else 0
  if target:put(target+0x1c,get(target+0x1c)|0x20)
  sp=uc.reg_read(UC_X86_REG_ESP);uc.reg_write(UC_X86_REG_EAX,0);uc.reg_write(UC_X86_REG_EIP,get(sp));uc.reg_write(UC_X86_REG_ESP,sp+4)
 m.hook_add(UC_HOOK_CODE,hook,begin=callback,end=callback);m.mem_write(0x4f5815,b'\0');rows=[]
 for order,layer,mask,mutation in itertools.product(range(2),(0,3,13,20,23,28,34,35),range(64),range(3)):
  chain=list(range(6)) if order==0 else [5,2,4,1,3,0]
  for i,vm in enumerate(vms):m.mem_write(vm,bytes(0x700));put(vm+0x1c,0x20 if mask&(1<<i) else 0);put(vm+0x5bc,callback)
  for a,b in zip(chain,chain[1:]):put(vms[a]+0x590,vms[b])
  put(manager+0xfe87a8+layer*0x5cc,vms[chain[0]]);put(stack,base);put(stack+4,layer);events.clear();m.reg_write(UC_X86_REG_ESP,stack);m.reg_write(UC_X86_REG_ECX,manager);m.emu_start(0x47e810,base,count=10000);assert m.reg_read(UC_X86_REG_EIP)==base
  rows.append(dict(input=[order,layer,mask,mutation],status=m.reg_read(UC_X86_REG_EAX),events=list(events),flags=[get(vm+0x1c) for vm in vms]))
 report=dict(executableSha256=hashlib.sha256(img.data).hexdigest(),rows=rows,scope='Whole original47e810 layer traversal and478f60 dispatcher through callback then native invisible rejection. Six synthetic invisible VMs with nontrivial chain order, eight real layer slots, all64 retirement masks and callback mutations retiring self/next. Synthetic callbacks record execution and mutate native VM retirement bit20, lock disabled. No sprite geometry, GPU, registration/list construction or full original scene claim.')
 (ROOT/'artifacts/th14/draw-layer-native.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print('PASS native draw layer',len(rows))
if __name__=='__main__':main()
