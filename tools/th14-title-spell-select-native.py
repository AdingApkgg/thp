"""Retail spell selection463180, choices463600 and draw464210."""
import hashlib,importlib,itertools,json,re,struct
from pathlib import Path
from unicorn import Uc,UC_ARCH_X86,UC_MODE_32,UC_HOOK_CODE
from unicorn.x86_const import *
ROOT=Path(__file__).resolve().parents[1]
def main():
 img,_,_=importlib.import_module('th-anm-handlers').handlers(14);m=Uc(UC_ARCH_X86,UC_MODE_32)
 for _,b,size,raw,n in img.sections:
  start=b&~4095;m.mem_map(start,((b+size+4095)&~4095)-start);m.mem_write(b,img.data[raw:raw+n])
 base,menu,score,sup,resource,stack=0x70000000,0x70001000,0x70010000,0x70050000,0x70070000,0x700ff000;m.mem_map(base,0x100000)
 def put(p,v):m.mem_write(p,struct.pack('<I',v&0xffffffff))
 def get(p):return struct.unpack('<I',m.mem_read(p,4))[0]
 def flt(p):return struct.unpack('<f',m.mem_read(p,4))[0]
 def string(p):return bytes(m.mem_read(p,255)).split(b'\0')[0].decode('latin1')
 events=[];texts=[];ascii=[];objects={};scripts={};counter=0
 def alloc(script=-1):
  nonlocal counter
  counter+=1;pointer=0x70072000+counter*0x600;handle=2000+counter;objects[handle]=pointer;scripts[pointer]=script;return pointer,handle
 def fmt(p,args):
  values=[];pattern=string(p)
  for match in re.finditer(r'%(?:[-+ #0]*\d*(?:\.\d+)?)([ds%])',pattern):
   if match[1]=='%':continue
   values.append(string(get(args)) if match[1]=='s' else struct.unpack('<i',m.mem_read(args,4))[0]);args+=4
  return (pattern%tuple(values)).encode('latin1').hex()
 def hook(uc,a,size,user):
  sp=uc.reg_read(UC_X86_REG_ESP);this=uc.reg_read(UC_X86_REG_ECX);pop=None
  if a==0x458d70:
   script=get(sp+4);p,h=alloc(script);put(this+0x2c8+script*4,h);events.append(['create',script]);pop=4
  elif a==0x47fcb0:uc.reg_write(UC_X86_REG_EAX,alloc()[0]);pop=0
  elif a==0x40af00:scripts[get(sp+4)]=get(sp+8);events.append(['text-create',get(sp+8)]);pop=8
  elif a==0x46fe50:pop=0
  elif a==0x47e890:
   p=get(sp+8);h=next(h for h,v in objects.items() if v==p);put(get(sp+4),h);uc.reg_write(UC_X86_REG_EAX,get(sp+4));pop=8
  elif a==0x47f0a0:uc.reg_write(UC_X86_REG_EAX,objects.get(get(sp+4),0));pop=4
  elif a in (0x47f140,0x47f1b0):events.append(['interrupt',get(sp+4),get(sp+8)]);pop=8
  elif a==0x46e3d0:events.append(['sound',get(sp+4)]);pop=8
  elif a==0x46ef90:events.append(['audio',get(sp+4),get(sp+8)]);pop=12
  elif a==0x420d20:events.append(['loading']);pop=0
  elif a==0x41eea0:put(get(sp+4),79);uc.reg_write(UC_X86_REG_EAX,get(sp+4));events.append(['fade']);pop=16
  elif a==0x4854a0:pop=0
  elif a==0x47db50:
   texts.append(dict(text=fmt(get(sp+32),sp+36),color=get(sp+12),offset=get(sp+16),font=get(sp+20),style=get(sp+24),row=scripts[get(sp+8)]-193));pop=0
  elif a==0x40bb10:
   p=get(sp+8);ascii.append(dict(text=fmt(get(sp+12),sp+16),position=[flt(p+i*4) for i in range(3)],color=get(sup+0x191b0),shadow=get(sup+0x191c4),font=get(sup+0x191c8),scale=[flt(sup+0x191b4),flt(sup+0x191b8)]));pop=0
  if pop is not None:uc.reg_write(UC_X86_REG_EIP,get(sp));uc.reg_write(UC_X86_REG_ESP,sp+4+pop)
 m.hook_add(UC_HOOK_CODE,hook);counts=[3,4,4,6,5,6,12]
 def call(address,args=()):
  put(stack,base)
  for n,v in enumerate(args):put(stack+4+n*4,v)
  m.reg_write(UC_X86_REG_ESP,stack);m.reg_write(UC_X86_REG_ECX,menu);m.emu_start(address,base,count=1000000);assert m.reg_read(UC_X86_REG_EIP)==base,hex(m.reg_read(UC_X86_REG_EIP))
 def setup(state,timer,stage,row,loadout,mode,resume=-1):
  nonlocal counter
  m.mem_write(base,bytes(0xfe000));objects.clear();scripts.clear();counter=0;put(0x4db520,sup);put(0x4db68c,score);put(sup+0x191e4,resource);put(0x4f56cc,sup+0x1a000);put(0x4d8f58,0x3f800000);m.mem_write(0x4f5815,b'\0');put(0x4d5fec,resume);put(0x4d5fe8,-1)
  for off,v in ((0x14,resource),(0x1c,18),(0x24,state),(0x28,row),(0x30,counts[stage]),(0x34,3),(0x38,stage),(0x74,10),(0x78,7),(0xb4,2),(0xf8,1),(0x5c90,loadout),(0x5c98,6),(0x5d60,1),(0x5d68,stage),(0x5d6c,row),(0x2b4,timer-1),(0x2b8,timer),(0x2bc,0x3f800000),(0x2c0,0x4d8f58),(0x2c4,1)):put(menu+off,v)
  for script in (198,259):p,h=alloc(script);put(menu+0x2c8+script*4,h)
  for c in range(7):
   for id in range(120):
    p=score+8+c*0x5298+0x978+id*0x9c;m.mem_write(p,f'Spell {id:03d}'.encode()+b'\x81\x48\0');words=[id%3,(id+c)%3,7 if mode==1 or mode==2 and id%2 else 0,5 if mode==3 else 9,0,0,(0,2345678,0x7fffffff,0x80000000)[id%4]];m.mem_write(p+0x80,struct.pack('<7I',*words))
  put(sup+0x191b0,0xffffffff);m.mem_write(sup+0x191b4,struct.pack('<2f',1,1));put(0x4d6884,0);put(0x4d6880,0)
  if state:
   call(0x463600,(stage,row,menu+0x5d70,0))
   for script in (96,199):p,h=alloc(script);put(menu+0x2c8+script*4,h)
  events.clear();texts.clear();ascii.clear()
 def snap():return dict(screen=get(menu+0x1c),substate=get(menu+0x24),selected=get(menu+0x28),count=get(menu+0x30),depth=get(menu+0xb4),loadout=get(menu+0x5c90),stage=get(menu+0x5d68),row=get(menu+0x5d6c),resume=get(0x4d5fec),choices=[get(menu+0x5d70+n*4) for n in range(5)],events=events[:],texts=texts[:])
 entries=[];controls=[];boundaries=[];layouts=[]
 for stage,loadout,resume in itertools.product(range(7),(0,5),(-1,0)):
  setup(0,0,stage,0,loadout,1,resume);call(0x463180);entries.append(dict(stage=stage,loadout=loadout,resume=resume,result=snap()))
 for stage in range(7):
  for row,loadout,mode,pressed in itertools.product(range(counts[stage]),(0,5),range(4),(0,16,32,64,128,1,2)):
   setup(2,17,stage,row,loadout,mode);put(0x4d6884,pressed);call(0x463180);controls.append(dict(stage=stage,row=row,loadout=loadout,mode=mode,pressed=pressed,result=snap()))
  for state,timer,row in itertools.product((1,3,4),(5,6,10,11,13,14),(0,counts[stage]-1)):
   setup(state,timer,stage,row,0,1);call(0x463180);boundaries.append(dict(stage=stage,state=state,timer=timer,row=row,result=snap()))
  for row,loadout,mode in itertools.product(range(counts[stage]),range(6),range(4)):
   setup(1,5,stage,row,loadout,mode);call(0x463600,(stage,row,menu+0x5d70,0));call(0x464210);layouts.append(dict(stage=stage,row=row,loadout=loadout,mode=mode,choices=[get(menu+0x5d70+n*4) for n in range(5)],texts=texts[:],ascii=ascii[:]))
 result=dict(passed=True,executableSha256=hashlib.sha256(img.data).hexdigest(),entries=entries,controls=controls,boundaries=boundaries,layouts=layouts,scope='Actual full retail463180/463600/463020/4635b0 and464210; seven groups/40 rows/120 spell metadata, loadout changes, seen/unseen/partially seen/practice-only records, resume paths, cursor stacks, timer gates, text requests and score ASCII. ANM/texture/font/CRT/audio services controlled; no browser/GPU or spell battle proof.')
 (ROOT/'artifacts/th14/title-spell-select-native.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print(f'PASS {len(entries)} entries, {len(controls)} controls, {len(boundaries)} boundaries, {len(layouts)} layouts')
if __name__=='__main__':main()
