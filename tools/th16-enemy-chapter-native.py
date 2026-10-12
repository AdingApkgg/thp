"""Full41d900 preparation,524 and death-credit fragment from own TH16."""
import hashlib,importlib,json,struct
from pathlib import Path
from unicorn import *
from unicorn.x86_const import *
ROOT=Path(__file__).resolve().parents[1]
def main():
 img,_,_=importlib.import_module('th-anm-handlers').handlers(16);m=Uc(UC_ARCH_X86,UC_MODE_32)
 for _,base,size,raw,n in img.sections:
  first=base&~4095;m.mem_map(first,((base+size+4095)&~4095)-first);m.mem_write(base,img.data[raw:raw+n])
 m.mem_map(0x70000000,0x40000);manager,enemy,node,game,stack,bp,ret=0x70000000,0x70001000,0x70008000,0x7000a000,0x70030000,0x70038000,0x7003e000
 def put(p,v):m.mem_write(p,struct.pack('<I',v&0xffffffff))
 def get(p):return struct.unpack('<I',m.mem_read(p,4))[0]
 called=[];argument=0
 def boundary(machine,address,size,user):
  sp=machine.reg_read(UC_X86_REG_ESP)
  if address==0x477920:
   p,v,n=[get(sp+k) for k in (4,8,12)];machine.mem_write(p,bytes([v&255])*n)
  elif address==0x41d520:called.append(1);machine.reg_write(UC_X86_REG_EAX,1)
  elif address==0x4251d0:machine.reg_write(UC_X86_REG_EAX,argument&0xffffffff)
 for address,cleanup in ((0x477920,0),(0x41d520,0),(0x4251d0,4)):
  m.mem_write(address,b'\xc2'+struct.pack('<H',cleanup) if cleanup else b'\xc3');m.hook_add(UC_HOOK_CODE,boundary,begin=address,end=address)
 put(0x4a6dc0,manager);put(0x4a6dd4,game);put(manager+0x180,node);put(node,enemy);put(node+4,0);put(0x490eb0,0x4a5788);put(0x4a5788,0x3f800000)
 erase=[]
 masks=(0x20,0x80,0x100,0x400,0x400000,0x800000,0x40000,0x2000000)
 for selection in range(256):
  flags=sum(v for i,v in enumerate(masks) if selection&(1<<i))
  m.mem_write(enemy,bytes(0x6000));put(enemy+0x526c,flags)
  for n in range(20):put(enemy+0x519c+n*4,50+n)
  put(enemy+0x148c,0x3f800000);put(enemy+0x1490,0x40000000);put(enemy+0x5738,7);put(manager+0x9c,17);put(manager+0xa0,0x418c0000);put(manager+0xa4,0)
  put(stack,ret);called.clear();m.reg_write(UC_X86_REG_ESP,stack);m.emu_start(0x41d900,ret,count=2000);assert m.reg_read(UC_X86_REG_EIP)==ret
  erase.append(dict(flags=flags,selected=bool(called),output=[get(enemy+0x526c)]+[get(enemy+0x519c+n*4) for n in range(20)]+[get(enemy+0x148c),get(enemy+0x1490),get(enemy+0x5738)]))
 chapters=[]
 for argument in (-2147483648,-1,0,1,7,2147483647):
  for credit in (0,1,7,-1):
   put(enemy+0x4528,9);put(enemy+0x452c,credit);put(0x4a5798,9);put(game+0xa8,9);m.reg_write(UC_X86_REG_EDI,enemy);m.reg_write(UC_X86_REG_EBP,bp);m.reg_write(UC_X86_REG_ESP,stack)
   m.emu_start(0x4222bf,0x422a9b,count=1000)
   chapters.append(dict(tag=argument,credit=credit,output=[get(0x4a5798),get(game+0xa8),get(enemy+0x4528),get(enemy+0x452c)]))
 deaths=[];credits=[]
 for tag in (-1,0,1,7):
  for chapter in (-1,0,1,7):
   for credit in (-2147483648,-1,0,1,7,2147483647):
    put(enemy+0x5734,tag);put(enemy+0x5738,credit);put(0x4a5798,chapter);put(0x4a5884,0x7fffffff);m.reg_write(UC_X86_REG_EDI,enemy)
    m.emu_start(0x41d662,0x41d68a,count=100)
    deaths.append(dict(tag=tag,chapter=chapter,credit=credit,output=[get(enemy+0x5738),get(0x4a5884)]))
    put(enemy+0x4528,tag);put(enemy+0x452c,credit);put(0x4a5884,0x7fffffff);m.reg_write(UC_X86_REG_EDI,enemy);m.emu_start(0x420410,0x422a9b,count=100)
    credits.append(dict(tag=tag,chapter=chapter,credit=credit,output=[get(enemy+0x452c),get(0x4a5884)]))
 settings=[]
 for credit in (-2147483648,-1,0,1,2,2147483647):
  for argument in (-2147483648,-1,0,1,7,2147483647):
   for spawned in (-2147483648,-1,0,1,7,2147483647):
    put(enemy+0x452c,credit);put(0x4a5880,spawned);m.reg_write(UC_X86_REG_EDI,enemy);m.reg_write(UC_X86_REG_EBP,bp);m.reg_write(UC_X86_REG_ESP,stack)
    m.emu_start(0x4203ba,0x422a9b,count=1000);assert m.reg_read(UC_X86_REG_EIP)==0x422a9b
    settings.append(dict(credit=credit,value=argument,spawned=spawned,output=[get(enemy+0x452c),get(0x4a5880)]))
 timers=[];timer=enemy+0x2bc
 for flags in (0,1,2,0xffffffff):
  for rate in (0,.5,.99,1,1.01,2):
   for off,v in ((0,19),(4,20),(8,0x41a40000),(12,0),(16,flags)):put(timer+off,v)
   put(0x4a5788,struct.unpack('<I',struct.pack('<f',rate))[0]);m.reg_write(UC_X86_REG_EDI,enemy);m.reg_write(UC_X86_REG_ESP,stack)
   m.emu_start(0x421860,0x422a9b,count=1000);assert m.reg_read(UC_X86_REG_EIP)==0x422a9b
   def timer_words():return [get(timer+off) for off in (0,4,8)]+[int(bool(get(timer+16)&1)),get(timer+16)]
   configured=timer_words();frames=[]
   for n in range(40):
    put(stack,ret);put(stack+4,0);m.reg_write(UC_X86_REG_ESP,stack);m.reg_write(UC_X86_REG_ECX,timer);m.emu_start(0x406190,ret,count=1000);assert m.reg_read(UC_X86_REG_EIP)==ret;frames.append(timer_words())
   timers.append(dict(flags=flags,rate=rate,configured=configured,frames=frames))
 out=ROOT/'artifacts/th16/enemy-chapter-native.json';out.write_text(json.dumps(dict(executableSha256=hashlib.sha256(img.data).hexdigest(),erase=erase,chapters=chapters,deaths=deaths,credits=credits,settings=settings,timers=timers),separators=(',',':'))+'\n',encoding='utf-8');print(f'{len(erase)} erase preparations; {len(chapters)} chapters; {len(deaths)} death credits; {len(settings)} ECL569 settings; {len(timers)} phase timers')
if __name__=='__main__':main()
