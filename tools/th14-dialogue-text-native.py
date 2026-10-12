"""Retail MSG text dispatch and panel sizing; controlled ANM delivery only."""
import hashlib, importlib, itertools, json, struct
from pathlib import Path
from unicorn import Uc, UC_ARCH_X86, UC_MODE_32, UC_HOOK_CODE
from unicorn.x86_const import *
ROOT=Path(__file__).resolve().parents[1]
def main():
 img=importlib.import_module('th-anm-handlers').handlers(14)[0]; m=Uc(UC_ARCH_X86,UC_MODE_32)
 for _,b,size,raw,n in img.sections:
  start=b&~4095;m.mem_map(start,((b+size+4095)&~4095)-start);m.mem_write(b,img.data[raw:raw+n])
 base=0x70000000;m.mem_map(base,0x30000);dialogue=base;instruction=base+0x1000;manager=base+0x2000;stack=base+0x2e000
 def put(p,v):m.mem_write(p,struct.pack('<I',v&0xffffffff))
 def get(p):return struct.unpack('<I',m.mem_read(p,4))[0]
 def signed(v):return struct.unpack('<i',struct.pack('<I',v))[0]
 def cstr(p):
  result=bytearray()
  while m.mem_read(p,1)!=b'\0':result+=m.mem_read(p,1);p+=1
  return bytes(result)
 vms={103+n:base+0x4000+n*0x800 for n in range(4)};panel=base+0x8000;children=[base+0x9000,base+0xa000];old=base+0xb000;oldchild=base+0xc000
 vms.update({200:panel,201:old});put(0x4f56cc,manager);put(0x4db550,base+0x3000);put(base+0x32a4,base+0xd000)
 writes=[];interrupts=[];allocations=[]
 def hook(uc,a,n,u):
  if a not in (0x47f0a0,0x47f420,0x47f730,0x47f140,0x47f1b0,0x47db50,0x47ed10,0x486016,0x486040):return
  sp=uc.reg_read(UC_X86_REG_ESP);pop=0;result=0;ecx=uc.reg_read(UC_X86_REG_ECX)
  if a==0x47f0a0:result=vms.get(get(sp+4),0);pop=4
  elif a==0x47f420:result=vms.get(get(ecx),0)
  elif a==0x47f730:
   p=get(sp+4);m.mem_write(vms[get(ecx)]+0x59c,bytes(m.mem_read(p,12)));pop=4
  elif a in (0x47f140,0x47f1b0):interrupts.append([get(sp+4),get(sp+8)]);pop=8
  elif a==0x47db50:
   args=[get(sp+i*4) for i in range(1,9)];writes.append([next(k for k,v in vms.items() if v==args[1])-100,args[2],signed(args[5]),signed(args[6]),signed(args[4]),cstr(args[7]).hex(),get(args[1]+0x1c)&0x800])
  elif a==0x47ed10:
   script=get(sp+8);position=[get(get(sp+12)+i*4) for i in range(3)];allocations.append([script,*position]);put(get(sp+4),200);put(panel+0x580,panel);put(panel+0x584,children[0]+0x580);put(panel+0x588,0)
   for i,vm in enumerate(children):put(vm+0x580,vm);put(vm+0x584,children[i+1]+0x580 if i==0 else 0);m.mem_write(vm+0x4aa,struct.pack('<h',script-216+(168 if i==0 else 200)))
   pop=28
  elif a==0x486016:result=int(cstr(get(sp+4)).split(b',')[0])
  elif a==0x486040:result=get(sp+4)+cstr(get(sp+4)).index(bytes([get(sp+8)&255]))
  uc.reg_write(UC_X86_REG_EAX,result&0xffffffff);uc.reg_write(UC_X86_REG_EIP,get(sp));uc.reg_write(UC_X86_REG_ESP,sp+4+pop)
 for a in (0x47f0a0,0x47f420,0x47f730,0x47f140,0x47f1b0,0x47db50,0x47ed10,0x486016,0x486040):m.hook_add(UC_HOOK_CODE,hook,begin=a,end=a)
 rows=[]
 for op,speaker,flags,line,initialized,profile in itertools.product((15,16,17,18,28),range(3),range(16)[::2],range(2),range(2),range(5)):
  # Layout 16 has no matching children in retail front.anm, so exclude this
  # invalid allocation request from the controlled successful-allocation set.
  if op==17 and speaker+2*((flags>>2)&15)+(8 if line else 0)>=16 and profile!=2:continue
  plain=(b'Long text 012345',bytes.fromhex('938c95fb926e97ec'),b'|3,2,ruby',b'A',b'')[profile];key=0x77;step=7;encoded=bytearray()
  for c in plain+b'\0':encoded.append(c^key);key=(key+step)&255;step=(step+16)&255
  m.mem_write(dialogue,bytes(0x200));m.mem_write(instruction,bytes(256));m.mem_write(instruction+4,bytes(encoded));put(dialogue+0x158,instruction)
  if op==28:m.mem_write(instruction+4,struct.pack('<ff',*((112,288),(224,144),(-0.,0.),(.125,-3.75),(-112,288))[profile]))
  for n in range(4):put(dialogue+0x58+n*4,103+n);m.mem_write(vms[103+n],bytes(0x700));m.mem_write(vms[103+n]+0x59c,struct.pack('<fff',50+n,70+n,0))
  for p in (panel,*children,old,oldchild):m.mem_write(p,bytes(0x700))
  put(old+0x580,old);put(old+0x584,oldchild+0x580);put(oldchild+0x580,oldchild);put(dialogue+0x6c,201)
  for off,value in ((0x184,flags),(0x188,line),(0x18c,initialized),(0x190,speaker),(0x194,0xf8f08f),(0x198,0x8088ff),(0x19c,0xd8d8d8),(0x1a0,0x42e00000),(0x1a4,0x43900000),(0x1ac,0x42700000)):put(dialogue+off,value)
  m.mem_write(stack,bytes(512));put(stack+0xc,dialogue);m.reg_write(UC_X86_REG_ESP,stack);m.reg_write(UC_X86_REG_EDI,dialogue);m.reg_write(UC_X86_REG_ESI,manager);m.reg_write(UC_X86_REG_ECX,instruction);m.reg_write(UC_X86_REG_XMM1,img.u32(0x4c1a78))
  writes.clear();interrupts.clear();allocations.clear();start=img.u32(0x433930+op*4);m.emu_start(start,0x43369d,count=20000);assert m.reg_read(UC_X86_REG_EIP)==0x43369d
  rows.append(dict(input=[op,speaker,flags,line,initialized,profile],writes=writes[:],interrupts=[[h-100,label] for h,label in interrupts],allocations=allocations[:],state=[get(dialogue+o) for o in (0x188,0x18c,0x1ac,0x1b4,0x1a0,0x1a4)],positions=[[get(vms[103+n]+0x59c+i*4) for i in range(3)] for n in range(4)],widths=[get(p+0x4bc) for p in children],retired=[get(p+0x1c)&0x20 for p in (old,oldchild)],backgroundPresent=int(get(dialogue+0x6c)!=0)))
 out=ROOT/'artifacts/th14/dialogue-text-native.json';out.write_text(json.dumps(dict(executableSha256=hashlib.sha256(img.data).hexdigest(),cases=rows),indent=2)+'\n');print('PASS retail dialogue text',len(rows))
if __name__=='__main__':main()
