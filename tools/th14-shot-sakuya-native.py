"""Retail Sakuya A knife callbacks; start with the allocation gate 452f30."""
import hashlib,importlib,itertools,json,struct
from pathlib import Path
from unicorn import Uc,UC_ARCH_X86,UC_MODE_32,UC_HOOK_CODE
from unicorn.x86_const import *
ROOT=Path(__file__).resolve().parents[1]
def main():
 img,*_=importlib.import_module('th-anm-handlers').handlers(14);m=Uc(UC_ARCH_X86,UC_MODE_32)
 for _,b,size,raw,n in img.sections:
  s=b&~4095;m.mem_map(s,((b+size+4095)&~4095)-s);m.mem_write(b,img.data[raw:raw+n])
 end,obj,spec,player,stack=0x70000000,0x70001000,0x70002000,0x70010000,0x700ff000;m.mem_map(end,0x100000)
 put=lambda p,v:m.mem_write(p,struct.pack('<I',v&0xffffffff));get=lambda p:struct.unpack('<I',m.mem_read(p,4))[0];bits=lambda v:struct.unpack('<I',struct.pack('<f',v))[0]
 rows=[]
 for count,limit,flags,timer_flags,rate in itertools.product((-2,0,1,7,8,2147483647),(-1,0,1,8),(0,1,2,0x3c,0xff),(0,1,0x80),(.5,1.25)):
  m.mem_write(obj,bytes(0x100));put(obj+0xbc,spec);put(spec+0x3c,limit);put(0x4db67c,player);put(player+0x1834c,count);put(obj+0x10,flags);put(obj+0x9c,123);put(obj+0xa0,456);put(0x4d8f58,bits(rate))
  for off in (0x2c,0x40):
   for k,v in enumerate((18,19,bits(19.5),0x4d8f58,timer_flags)):put(obj+off+k*4,v)
  put(stack,end);m.reg_write(UC_X86_REG_ESP,stack);m.reg_write(UC_X86_REG_ECX,obj);m.emu_start(0x452f30,end,count=10000)
  rows.append(dict(args=[count,limit,flags,timer_flags,rate],result=[get(player+0x1834c),get(obj+0x10),get(obj+0x9c),get(obj+0xa0)]+[get(obj+o+i*4)for o in (0x2c,0x40)for i in (0,1,2,4)],accepted=m.reg_read(UC_X86_REG_EAX)==0))
 enemy,vm,child,node,area=0x70040000,0x70050000,0x70051000,0x70052000,0x70053000
 events=[];target_mode=0;vm_present=1
 def sink(machine,a,size,user):
  sp=m.reg_read(UC_X86_REG_ESP)
  if a==0x42c310:m.reg_write(UC_X86_REG_EAX,enemy if target_mode==1 else 0)
  elif a==0x421a60:m.reg_write(UC_X86_REG_EAX,enemy if target_mode==1 else 0)
  elif a==0x47f0a0:m.reg_write(UC_X86_REG_EAX,vm if vm_present else 0)
  elif a==0x47f140:events.append([1,get(sp+8)])
  elif a==0x47f1b0:events.append([2,get(sp+8)])
  elif a==0x450130:
   damage=get(sp+12);events.append([3,get(sp+8),damage]);m.mem_write(area,bytes(0xa4));put(area+0x10,3);put(area+0x84,damage);m.reg_write(UC_X86_REG_EAX,area)
  elif a==0x46e470:events.append([4,get(sp+4),m.reg_read(UC_X86_REG_XMM2)&0xffffffff])
  elif a==0x42c810:events.append([5,m.reg_read(UC_X86_REG_XMM1)&0xffffffff])
 for a,cleanup in ((0x42c310,4),(0x421a60,4),(0x47f0a0,4),(0x47f140,8),(0x47f1b0,8),(0x450130,12),(0x46e470,4),(0x42c810,0)):
  m.mem_write(a,b'\xc2'+struct.pack('<H',cleanup)if cleanup else b'\xc3');m.hook_add(UC_HOOK_CODE,sink,begin=a,end=a)
 def update(inputs):
  nonlocal target_mode,vm_present
  phase,age,threshold,count,attached,limit,decay,timeout,target_mode,manager,firing,state,dialogue,knives,has_child,child_scale,vm_scale,rate,timer_flags,power,flags,vm_present=inputs[:22]
  events.clear();m.mem_write(obj,bytes(0x100));m.mem_write(enemy,bytes(0x6000));m.mem_write(vm,bytes(0x1000));m.mem_write(child,bytes(0x1000));m.mem_write(area,bytes(0xa4))
  for p,v in ((0x4db67c,player),(0x4db544,enemy if manager else 0),(0x4db550,player+0x19000),(player+0x19194,dialogue),(0x4d8f58,rate),(0x4f5858,power*40),(0x4f5860,40),(player+0x1834c,count),(player+0x18350,attached),(player+0x184b0,firing),(player+0x684,state),(obj+0xbc,spec),(obj+0x10,(flags&~0x3c)|(phase<<2)),(obj+0x14,77),(obj+0x1c,age),(obj+0x98,1),(obj+0x9c,enemy if target_mode else 0),(obj+0xa0,19 if target_mode else 0),(obj+0xc0,area),(obj+0xac,19),(spec+0x38,threshold),(spec+0x3c,limit),(spec+0x44,timeout),(spec+0x4c,bits(.05)),(enemy+0x11e4,19),(enemy+0x11ec,knives),(area+0x10,1),(area+0x14,bits(9)),(area+0x18,bits(2)),(area+0x84,19),(vm+0x18,7),(vm+0x60,vm_scale),(vm+0x64,vm_scale),(vm+0x580,vm),(vm+0x584,node if has_child else 0),(node,child),(node+4,0),(child+0x60,child_scale)):
   put(p,v)
  m.mem_write(child+0x4aa,struct.pack('<H',14))
  for off,point in ((obj+0x54,(12.25,300.5,3.)),(enemy+0x1234,(32.25,180.5,2.)),(obj+0xc4,(-20.,120.,1.))):
   for i,v in enumerate(point):put(off+i*4,bits(v))
  put(obj+0x6c,bits(8));put(obj+0x70,bits(-1.5707963705062866))
  for off,time in ((0x2c,0),(0x40,decay)):
   for i,v in enumerate((time-1,time,bits(time),0x4d8f58,timer_flags)):put(obj+off+i*4,v)
  put(player+0x184b8,0);put(stack,end);m.reg_write(UC_X86_REG_ESP,stack);m.reg_write(UC_X86_REG_ECX,obj);m.reg_write(UC_X86_REG_MXCSR,0x1f80);m.reg_write(UC_X86_REG_FPCW,0x37f);m.reg_write(UC_X86_REG_FPSW,0);m.reg_write(UC_X86_REG_FPTAG,0xffff)
  if len(inputs)>22:
   kind,dx,dy,radius,width,advanced=inputs[22:28];target=0x70054000;rect=target+0x20
   as_float=lambda v:struct.unpack('<f',struct.pack('<I',v))[0]
   for p,v in ((obj+0x18,age-advanced),(area+0x28,width),(area+0x9c,enemy if target_mode else 0),(target,bits(12.25+as_float(dx))),(target+4,bits(300.5+as_float(dy))),(target+8,0),(rect,bits(24)),(rect+4,bits(40)),(stack+4,rect if kind else 0),(stack+8,0),(stack+12,radius)):put(p,v)
   m.reg_write(UC_X86_REG_EDX,target);m.emu_start(0x453540,end,count=100000);assert m.reg_read(UC_X86_REG_EIP)==end
   result=[get(obj+o)for o in (0x10,0x6c,0x54,0x58,0x5c)]+[get(player+0x18350),get(area+0x10),int(get(obj+0x9c)!=0),get(obj+0xa0)]+[get(obj+o)for o in (0xc4,0xc8,0xcc)]+[get(enemy+0x11ec),get(player+0x184b8),m.reg_read(UC_X86_REG_EAX)]
   return dict(args=inputs,result=result,events=events[:])
  m.emu_start(0x452ff0,end,count=100000);assert m.reg_read(UC_X86_REG_EIP)==end
  result=[get(obj+o)for o in (0x10,0x6c,0x70,0x54,0x58,0x5c)]+[int(get(obj+0x9c)!=0),get(obj+0xa0)]+[get(obj+o+i*4)for o in (0x2c,0x40)for i in (0,1,2,4)]+[get(p)for p in (player+0x1834c,player+0x18350,obj+0xac,area+0x10,area+0x14,area+0x18,vm+0x18,vm+0x60,enemy+0x11ec,obj+0x98,obj+0x14)]
  return dict(args=inputs,result=result,events=events[:],retired=m.reg_read(UC_X86_REG_EAX)==0xffffffff)
 updates=[]
 for phase,age,target,manager,firing,state,dialogue,rate in itertools.product((0,1,2),(9,10,11),(0,1,2),(0,1),(0,1),(1,2),(0,1),(.5,1.,1.25)):
  updates.append(update([phase,age,10,7,8,8,3,4,target,manager,firing,state,dialogue,13,1,bits(.75),bits(1.3),bits(rate),1,4,3,1]))
 for knives,attached,decay,has_child,vm_present in itertools.product((9,10,13,14,17,18,21,22),(7,8,9),(2,3,4),(0,1),(0,1)):
  phase=2 if not vm_present else 1
  updates.append(update([phase,10,10,8,attached,8,decay,4,1,1,1,1,0,knives,has_child,bits(.5),bits(1.6),bits(1.25),1,4,3,vm_present]))
 hits=[]
 for phase,shape,target,dx,dy,age,advanced,power in itertools.product((0,1,2,3),(0,1),(0,1),(-40.,0.,8.),(-120.,0.,40.),(-2,-1,0,1,2),(0,1),(0,2,4)):
  hits.append(update([phase,age,10,7,8,8,3,4,target,1,1,1,0,13,1,bits(.75),bits(1.3),bits(1.),1,power,3,1,shape,bits(dx),bits(dy),bits(10),bits(12),advanced]))
 slow=[];m.mem_write(0x42c810,img.read(0x42c810,0x83));m.ctl_remove_cache(0x42c810,0x42c893);spell=0x70055000;put(0x4db534,spell)
 for flags,initial,delta,spell_flags,spell_id in itertools.product((0,0x800000),(-.5,0.,.2,.32,.9),(-.2,-.05,0.,.05,.3,1.),(0,1),(0,0x60,0x61,0x62,0x63,0x71,0x77,0x78)):
  for p,v in ((enemy+0x5244,flags),(enemy+0x14d4,bits(initial)),(spell+0x7c,spell_flags),(spell+0x78,spell_id),(stack,end)):put(p,v)
  m.reg_write(UC_X86_REG_ESP,stack);m.reg_write(UC_X86_REG_ECX,enemy);m.reg_write(UC_X86_REG_XMM1,bits(delta));m.emu_start(0x42c810,end,count=10000);assert m.reg_read(UC_X86_REG_EIP)==end
  slow.append(dict(args=[flags,initial,delta,spell_flags,spell_id],result=get(enemy+0x14d4)))
 clocks=[];clock_delivery=[]
 def ecl_clock(machine,a,size,user):clock_delivery.append(get(0x4d8f58))
 m.mem_write(0x424810,b'\xc3');m.hook_add(UC_HOOK_CODE,ecl_clock,begin=0x424810,end=0x424810)
 for rate,reduction,applied in itertools.product((-.5,0.,.5,1.,1.25,2.),(-.5,0.,.05,.33,.9,1.,1.5),(0,1)):
  m.mem_write(enemy,bytes(0x6000));put(enemy+0x14d4,bits(reduction));put(enemy+0x5248,applied*2);put(0x4d8f58,bits(rate));put(stack,end);clock_delivery.clear()
  m.reg_write(UC_X86_REG_ESP,stack);m.reg_write(UC_X86_REG_ECX,enemy);m.emu_start(0x424710,end,count=10000);assert m.reg_read(UC_X86_REG_EIP)==end;assert get(0x4d8f58)==bits(rate);assert len(clock_delivery)==1
  clocks.append(dict(args=[rate,reduction],result=clock_delivery[0],restored=get(0x4d8f58)))
 (ROOT/'artifacts/th14/shot-sakuya-native.json').write_text(json.dumps(dict(executableSha256=hashlib.sha256(img.data).hexdigest(),spawns=rows,updates=updates,hits=hits,slowdown=slow,clocks=clocks),indent=2)+'\n',encoding='utf-8');print(f'{len(rows)} knife allocation gates / {len(updates)} updates / {len(hits)} hits / {len(slow)} slowdown changes / {len(clocks)} clocks')
if __name__=='__main__':main()
