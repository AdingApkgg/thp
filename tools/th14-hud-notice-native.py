"""Retail 434430 and actual family deletion/visibility helpers.
ANM allocation, resource bind/tick, lookup/registration and sprite bind are
controlled boundaries. No original resource pixels or font rendering claim.
"""
import hashlib,importlib,json,struct
from pathlib import Path
from unicorn import Uc,UC_ARCH_X86,UC_MODE_32,UC_HOOK_CODE
from unicorn.x86_const import *
ROOT=Path(__file__).resolve().parents[1]
BASE,GAME,ASCII,FRONT,TEXT,VMBASE,STACK=0x70000000,0x70001000,0x70004000,0x70020000,0x70022000,0x70030000,0x700ef000
OFFSETS=[*[0xa4+4*i for i in range(8)],0xc4,0xc8,0xcc,0xd0,0x118]
def main():
 img,_,_=importlib.import_module('th-anm-handlers').handlers(14);m=Uc(UC_ARCH_X86,UC_MODE_32)
 for _,b,size,raw,n in img.sections:
  start=b&~4095;m.mem_map(start,((b+size+4095)&~4095)-start);m.mem_write(b,img.data[raw:raw+n])
 m.mem_map(BASE,0xf0000)
 def put(p,v):m.mem_write(p,struct.pack('<I',v&0xffffffff))
 def get(p):return struct.unpack('<I',m.mem_read(p,4))[0]
 handles={};allocated=[];bindings=[];sprites={}
 def sink(machine,a,size,user):
  sp=m.reg_read(UC_X86_REG_ESP);ecx=m.reg_read(UC_X86_REG_ECX)
  if a==0x47fcb0:
   vm=VMBASE+(13+len(allocated))*0x2000;allocated.append(vm);put(vm+0x18,2);m.reg_write(UC_X86_REG_EAX,vm)
  elif a==0x40af00:
   vm,script=get(sp+4),get(sp+8);bindings.append([2 if ecx==TEXT else 5,script]);put(vm+0x30,ecx);put(vm+0x580,vm)
  elif a==0x47e890:
   out,vm=get(sp+4),get(sp+8);handle=14+len(allocated)-1;handles[handle]=vm;put(out,handle);m.reg_write(UC_X86_REG_EAX,out)
  elif a==0x47f0a0:m.reg_write(UC_X86_REG_EAX,handles.get(get(sp+4),0))
  elif a==0x46f1e0:sprites[get(sp+4)]=get(sp+8)
 for a,cleanup in ((0x47fcb0,0),(0x40af00,8),(0x47e890,8),(0x47f0a0,4),(0x46f1e0,8),(0x46fe50,0)):
  m.mem_write(a,b'\xc2'+struct.pack('<H',cleanup) if cleanup else b'\xc3');m.hook_add(UC_HOOK_CODE,sink,begin=a,end=a)
 cases=[]
 for kind in range(7):
  for value in (-2147483648,-1000000,-1,0,1,9,999,1000,999999,1000000,12345678,99999999,999999999,2147483647):
   for mode in range(4):
    m.mem_write(BASE,bytes(0xee000));handles.clear();allocated.clear();bindings.clear();sprites.clear()
    put(GAME+0x2a4,FRONT);put(0x4db520,ASCII);put(ASCII+0x191e4,TEXT);put(0x4f56cc,BASE+0x25000);m.mem_write(0x4f5815,b'\0')
    put(GAME+0x11c,mode%2)
    for i,off in enumerate(OFFSETS):
     vm=VMBASE+i*0x2000;handles[i+1]=vm;put(GAME+off,i+1 if mode else 0);put(vm+0x580,vm)
     put(vm+0x584,vm+0x680 if mode>=2 else 0);put(vm+0x588,1 if mode==3 else 0)
     put(vm+0x680,vm+0x700);put(vm+0x684,vm+0x690);put(vm+0x690,vm+0x780);put(vm+0x694,0)
    put(STACK,BASE);put(STACK+4,value);put(STACK+8,kind);m.reg_write(UC_X86_REG_ESP,STACK);m.reg_write(UC_X86_REG_ECX,GAME)
    m.emu_start(0x434430,BASE,count=20000);assert m.reg_read(UC_X86_REG_EIP)==BASE
    created=[]
    for row,vm in zip(bindings,allocated):created.append([*row,get(vm+0x1c)&0x200,*[get(vm+o) for o in (0x59c,0x5a0,0x5a4,0x50)],sprites.get(vm,0xffffffff),get(vm+0x18)&2])
    erased=[(get(VMBASE+i*0x2000+o+0x1c)>>5)&1 for i in range(13) for o in (0,0x700,0x780)]
    cases.append(dict(kind=kind,value=value,mode=mode,slots=[*[get(GAME+o) for o in OFFSETS],get(GAME+0x11c)],erased=erased,created=created))
 # Execute the original icon allocation loop, then both display routines.
 m.mem_write(BASE,bytes(0xee000));handles.clear();allocated.clear();bindings.clear();sprites.clear()
 put(GAME+0x2a4,FRONT);put(0x4f56cc,BASE+0x25000);m.mem_write(0x4f5815,b'\0')
 m.reg_write(UC_X86_REG_ESP,STACK);m.reg_write(UC_X86_REG_EDI,GAME)
 m.emu_start(0x42edf6,0x42efb5,count=100000);assert m.reg_read(UC_X86_REG_EIP)==0x42efb5
 icons=[[*row,get(vm+0x1c)&0x200,*[get(vm+o) for o in (0x59c,0x5a0,0x5a4,0x50)],get(vm+0x18)&2] for row,vm in zip(bindings,allocated)]
 displays=[];put(0x4f586c,0)
 for count in (-2,0,1,2,7,8):
  for fragments in (-2147483648,-1,0,1,2,3,7,8,2147483647):
   for vm in allocated:put(vm+0x4a0,0x12345678)
   for address in (0x434ef0,0x434fd0):
    put(STACK,BASE);put(STACK+4,count);put(STACK+8,fragments)
    m.reg_write(UC_X86_REG_ESP,STACK);m.reg_write(UC_X86_REG_ECX,GAME)
    m.emu_start(address,BASE,count=20000);assert m.reg_read(UC_X86_REG_EIP)==BASE
   displays.append(dict(count=count,fragments=fragments,pending=[get(vm+0x4a0) for vm in allocated]))
 out=ROOT/'artifacts/th14/hud-notice-native.json';out.write_text(json.dumps(dict(executableSha256=hashlib.sha256(img.data).hexdigest(),cases=cases,icons=icons,displays=displays))+'\n',encoding='utf8');print(f'{len(cases)} retail HUD notice cases, {len(icons)} icons and {len(displays)} display cases.')
if __name__=='__main__':main()
