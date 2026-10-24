"""Retail411980..411a60 animation retirement block; declared handle resolver."""
import hashlib,importlib,itertools,json,struct,argparse
from pathlib import Path
from unicorn import Uc,UC_ARCH_X86,UC_MODE_32,UC_HOOK_CODE
from unicorn.x86_const import *
ROOT=Path(__file__).resolve().parents[1]
def main():
 parser=argparse.ArgumentParser();parser.add_argument('--out',type=Path,default=ROOT/'artifacts/th14/bomb-animation-retirement-oct24/unit/native.json');args=parser.parse_args()
 image,*_=importlib.import_module('th-anm-handlers').handlers(14);m=Uc(UC_ARCH_X86,UC_MODE_32)
 for _,base,size,raw,n in image.sections:
  first=base&~4095;m.mem_map(first,((base+size+4095)&~4095)-first);m.mem_write(base,image.data[raw:raw+n])
 base=0x70000000;m.mem_map(base,0x100000);bomb=base+0x1000;vms=[base+0x10000+i*0x1000 for i in range(6)];nodes=base+0x20000;stack=base+0xf0000
 put=lambda p,v:m.mem_write(p,struct.pack('<I',v&0xffffffff));get=lambda p:struct.unpack('<I',m.mem_read(p,4))[0]
 def resolver(uc,address,size,user):
  sp=uc.reg_read(UC_X86_REG_ESP);handle=get(sp+4);uc.reg_write(UC_X86_REG_EAX,{100:vms[0],200:vms[1]}.get(handle,0));uc.reg_write(UC_X86_REG_EIP,get(sp));uc.reg_write(UC_X86_REG_ESP,sp+8)
 m.hook_add(UC_HOOK_CODE,resolver,begin=0x47f0a0,end=0x47f0a0)
 rows=[]
 for main,aux,nonroot,active,flags in itertools.product(range(3),range(3),range(2),range(3),(0,0x100040)):
  m.mem_write(bomb,bytes(0x700));m.mem_write(nodes,bytes(0x100));put(bomb+0x40,active);put(bomb+0x44,[0,100,999][main]);put(bomb+0x48,0);put(bomb+0x4c,[0,200,999][aux]);put(0x4f56cc,base+0x30000)
  for p in vms:m.mem_write(p,bytes(0x5cc));put(p+0x1c,flags)
  put(vms[0]+0x584,nodes);put(vms[0]+0x588,1 if nonroot else 0);put(nodes,vms[2]);put(nodes+4,nodes+12);put(nodes+12,vms[3]);put(nodes+16,0)
  put(vms[1]+0x584,nodes+24);put(nodes+24,vms[4]);put(nodes+28,0)
  put(stack,base);m.reg_write(UC_X86_REG_ESP,stack);m.reg_write(UC_X86_REG_ECX,bomb);m.emu_start(0x411980,0x411a60,count=10000);assert m.reg_read(UC_X86_REG_EIP)==0x411a60
  rows.append(dict(args=[main,aux,nonroot,active,flags],flags2=[get(p+0x1c)for p in vms],clearedHandles=[get(bomb+o)for o in(0x44,0x48,0x4c)]))
 report=dict(passed=True,rows=rows,instructionBytesPatched=0,executableSha256=hashlib.sha256(image.data).hexdigest(),toolSha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),scope='Original411980..411a60 animation-family retirement block. Handle lookup47f0a0 is an explicit resolver for valid100/200, zero and stale999. Middle handle+48 is zero, matching the two represented production handles. Root and nonroot child topology, unrelated VM, active0/1/2 and flag preservation are controlled. Callback unregistration, native manager construction, allocator and whole destructor tail are excluded.',completeGame=False,nativeEquivalent=False)
 args.out.parent.mkdir(parents=True,exist_ok=True);args.out.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(nativeCases=len(rows),instructionBytesPatched=0)))
if __name__=='__main__':main()
