"""Retail43014e..430c55 two boss rows, with real normalization/libm."""
import hashlib,importlib,itertools,json,struct
from pathlib import Path
from unicorn import Uc,UC_ARCH_X86,UC_MODE_32,UC_HOOK_CODE
from unicorn.x86_const import *
ROOT=Path(__file__).resolve().parents[1]

def main():
 img,_,_=importlib.import_module('th-anm-handlers').handlers(14);m=Uc(UC_ARCH_X86,UC_MODE_32)
 for _,b,size,raw,n in img.sections:
  start=b&~4095;m.mem_map(start,((b+size+4095)&~4095)-start);m.mem_write(b,img.data[raw:raw+n])
 base,game,front,manager,player,boss_base,vm_base,stack=0x70000000,0x70001000,0x70002000,0x70003000,0x70004000,0x70008000,0x70020000,0x7006f000;m.mem_map(base,0x70000)
 def put(p,v):m.mem_write(p,struct.pack('<I',v&0xffffffff))
 def get(p):return struct.unpack('<I',m.mem_read(p,4))[0]
 def bits(v):return struct.unpack('<I',struct.pack('<f',v))[0]
 handles={};allocated=[];bindings=[];interrupts=[];name_calls=0
 def hook(uc,a,size,data):
  nonlocal name_calls
  sp=uc.reg_read(UC_X86_REG_ESP);cleanup=0
  if a==0x47fcb0:vm=vm_base+len(allocated)*0x1000;allocated.append(vm);uc.reg_write(UC_X86_REG_EAX,vm)
  elif a==0x40af00:vm=get(sp+4);bindings.append(get(sp+8));put(vm+0x580,vm);put(vm+0x18,7);cleanup=8
  elif a==0x46fe50:pass
  elif a==0x47e890:p,vm=get(sp+4),get(sp+8);handle=100+len(allocated);handles[handle]=vm;put(p,handle);uc.reg_write(UC_X86_REG_EAX,p);cleanup=8
  elif a==0x47f0a0:uc.reg_write(UC_X86_REG_EAX,handles.get(get(sp+4),0));cleanup=4
  elif a==0x47f140:
   handle,label=get(sp+4),get(sp+8);interrupts.append([handle,label]);vm=handles.get(handle)
   if vm:put(vm+0x4a0,label)
   cleanup=8
  elif a==0x4350b0:name_calls+=1;return
  else:return
  uc.reg_write(UC_X86_REG_EIP,get(sp));uc.reg_write(UC_X86_REG_ESP,sp+4+cleanup)
 m.hook_add(UC_HOOK_CODE,hook);rows=[]
 # Missing/eligible/health-limit/flags/damage-immunity/dialogue branches,
 # both slots, fresh and retained circles, float smoothing and proximity edges.
 cases=[]
 for variant,prior in itertools.product(range(10),range(2)):cases.append((variant,prior,0,0,0))
 for position,displayed,hidden in itertools.product(range(9),range(6),range(2)):cases.append((1,1,position,displayed,hidden))
 for variant,prior,position,displayed,hidden in cases:
  m.mem_write(base,bytes(0x6e000));handles.clear();allocated.clear();bindings.clear();interrupts.clear();name_calls=0
  for p,v in ((game+0x2a4,front),(0x4db544,manager),(0x4db67c,player),(0x4f56cc,base),(game+0x194,1 if variant==8 else 0),(manager+0x9c,1 if variant==9 else 0)):put(p,v)
  m.mem_write(0x4f5815,b'\0');put(stack+0x14,game)
  for p,v in ((0x4f58a4,1),(0x4f58ac,5),(0x4f5844,-1),(0x4f582c,0),(0x4db69c,0x4d5988+0xcc)):put(p,v)
  positions=[(12.25,-14.5,4.75),(0,0,0),(80,0,0),(96,0,0),(79.999,0,0),(95.999,0,0),(0,80,0),(0,96,0),(-32.125,40.5,-3.25)]
  x,y,z=positions[position];initial=(0,.024,.025,.25,.75,1)[displayed];prior_vms={}
  for slot in range(2):
   boss=boss_base+slot*0x7000;row=game+slot*0x54
   present=variant!=0 and (variant!=2 or slot==1) and (variant!=3 or slot==0)
   put(manager+0x5c+slot*4,boss if present else 0);health=(100000 if variant==4 else 50);flags=0x10 if variant==5 else 0x21 if variant==6 else 0
   for off,val in ((0x5164,health),(0x5168,100),(0x5244,flags),(0x51e0,1 if variant==7 else 0)):put(boss+off,val)
   for off,val in zip((0x1234,0x1238,0x123c),(x+slot*13,y-slot*7,z)):put(boss+off,bits(val))
   for off,val in ((0x1a8,bits(initial)),(0x1ac,bits(.75)),(0x1b0,77),(0x1f4,prior),(0x1f8,hidden)):put(row+off,val)
   for n,fraction in enumerate((0,.125,.25,.5)):put(row+0x1b8+n*8,bits(fraction));put(row+0x1bc+n*8,9+n)
   for n in range(7):
    handle=1+slot*7+n;vm=vm_base+0x20000+handle*0x800;prior_vms[handle]=vm;handles[handle]=vm;put(row+0x1d8+n*4,handle if prior else 0);put(vm+0x18,7);put(vm+0x1c,0x200)
  # A live old name lets caller count/retirement be checked without an ANM name factory.
  handles[99]=vm_base+0x30000;put(game+0xdc,99);put(handles[99]+0x1c,0x200)
  m.reg_write(UC_X86_REG_ESP,stack);m.reg_write(UC_X86_REG_EDI,game);m.reg_write(UC_X86_REG_MXCSR,0x1f80)
  m.emu_start(0x43014e,0x430c55,count=200000);assert m.reg_read(UC_X86_REG_EIP)==0x430c55
  observed=[]
  for slot in range(2):
   row=game+slot*0x54;ids=[get(row+0x1d8+n*4) for n in range(7)]
   observed.append(dict(state=[get(row+off) for off in (0x1a8,0x1ac,0x1b0,0x1f4,0x1f8)],marks=[get(row+0x1b8+n*8) for n in range(4)],vms=[[get(handles[h]+off) for off in (0x18,0x48,0x50,0x59c,0x5a0,0x5a4,0x4a0)] if h else None for h in ids]))
  rows.append(dict(variant=variant,prior=prior,position=position,displayed=displayed,hidden=hidden,created=bindings[:],nameCalls=name_calls,nameRetained=bool(get(game+0xdc)),nameRetired=bool(get(handles[99]+0x1c)&0x20),observed=observed,retirementFlagWords=[get(prior_vms[1+slot*7+n]+0x1c)for slot in range(2)for n in range(7)]+[get(handles[99]+0x1c)],retired=[bool(get(prior_vms[1+slot*7+n]+0x1c)&0x20) for slot in range(2) for n in range(7)]))
 result=dict(executableSha256=hashlib.sha256(img.data).hexdigest(),rows=rows,toolSha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),scope='Retail43014e..430c55 two boss rows. Actual SSE health ratio/smoothing, angle403590, retail sin/cos and full4350b0 name helper execute. Cases cover boss absence in either slot, eligibility exclusions, dialogue/manager gate, fresh/retained seven-script rings232/233/234/235x4, four marks, proximity80/96 and adjacent float positions, hidden-state hysteresis, missing-boss clears and direct VM retirement. ANM allocation/binding/first update/registry/interrupt controlled boundaries; name selection additionally proved separately. No real ANM/GPU or allocation failure proof.')
 out=ROOT/'artifacts/th14/stage-owner-retirement-oct24/unit/native.json';out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print(f'PASS {len(rows)} original two-boss ring cases')
if __name__=='__main__':main()
