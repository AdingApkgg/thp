"""Whole443cd0 death, controlled effect-slot/HUD/ANM boundaries."""
import hashlib,importlib,json,struct
from pathlib import Path
from unicorn import *
from unicorn.x86_const import *
ROOT=Path(__file__).resolve().parents[1]
def main():
 img,_,_=importlib.import_module('th-anm-handlers').handlers(16);m=Uc(UC_ARCH_X86,UC_MODE_32)
 for _,base,size,raw,n in img.sections:
  first=base&~4095;m.mem_map(first,((base+size+4095)&~4095)-first);m.mem_write(base,img.data[raw:raw+n])
 m.mem_map(0x70000000,0x100000);player,spell,bomb,effect,enemy,hud,out,stack,ret=0x70001000,0x70040000,0x70041000,0x70042000,0x70044000,0x70045000,0x70043000,0x700ff000,0x700fe000
 def put(p,v):m.mem_write(p,struct.pack('<I',v&0xffffffff))
 def get(p):return struct.unpack('<I',m.mem_read(p,4))[0]
 events=[];available=0
 def boundary(machine,address,size,user):
  sp=machine.reg_read(UC_X86_REG_ESP)
  if address==0x40e6c0:machine.reg_write(UC_X86_REG_EAX,0 if available else 0xffffffff)
  elif address==0x40e5c0:
   dest,script,pos,angle,layer=[get(sp+k) for k in (4,8,12,16,20)];assert script==28 and layer==0xffffffff and angle==0;assert struct.unpack('<fff',m.mem_read(pos,12))==(-12.25,80.5,1.25);events.append([0,script,0]);put(dest,7);machine.reg_write(UC_X86_REG_EAX,dest)
  elif address==0x42c280:events.append([1,get(sp+4),get(sp+8)])
  elif address==0x42c390:events.append([2,get(sp+4),get(sp+8)])
  elif address==0x407b20:assert get(sp+4)==player+0x14;events.append([3,get(sp+8),0])
  elif address==0x45f980:events.append([4,0,0]);machine.reg_write(UC_X86_REG_EAX,0)
  elif address==0x46f0b0:events.append([5,get(sp+4),get(sp+8)])
 for address,cleanup in ((0x40e6c0,0),(0x40e5c0,24),(0x42c280,8),(0x42c390,8),(0x407b20,8),(0x45f980,0),(0x46f0b0,8)):
  m.mem_write(address,b'\xc2'+struct.pack('<H',cleanup) if cleanup else b'\xc3');m.hook_add(UC_HOOK_CODE,boundary,begin=address,end=address)
 for address,pointer in ((0x4a6db0,spell),(0x4a6da8,bomb),(0x4a6db8,effect),(0x4a6dc0,enemy),(0x4a6dcc,hud)):put(address,pointer)
 put(effect+0xc,out);fields=(0x165a8,0x624,0x628,0x62c,0x634,0x16638,0x1663c,0x16640,0x16648,0x165f4)
 cases=[]
 for n in range(1024):
  lives=(-2147483648,-1,0,1,3,2147483647)[n%6];death_count=(-2147483648,-1,0,999998,999999,2147483647)[(n//6)%6];sf=(0,1,0x21,0x23,0xffffffff)[(n//36)%5];elapsed=(-1,0,59,60,61)[(n//7)%5];active=(n//11)%2;tf=(0,1,2,0xffffffff)[(n//13)%4];invflags=(0,1,2,0xffffffff)[(n//17)%4];available=n%2
  m.mem_write(player,bytes(0x30000));put(player+0x634,tf);put(player+0x16648,invflags);put(player+0x165a8,4);m.mem_write(player+0x610,struct.pack('<fff',-12.25,80.5,1.25));put(spell+0x78,sf);put(spell+0x24,elapsed);put(spell+0x7c,12345);put(bomb+0x30,active);put(0x4a57f4,lives);put(0x4a57f8,0x12345);put(0x4a5800,8);put(0x4a5804,0x12345678);put(0x4a57cc,death_count);put(enemy+0x3c,0x7fffffff);put(enemy+0x44,123);put(player+0x165f4,77)
  for i in range(4):
   row=player+0x660+i*0xe4;put(row,20+i);put(row+0xb0,10+i*2);put(row+0xb4,11+i*2)
  put(stack,ret);m.reg_write(UC_X86_REG_ESP,stack);m.reg_write(UC_X86_REG_ECX,player);events.clear();m.emu_start(0x443cd0,ret,count=20000);assert m.reg_read(UC_X86_REG_EIP)==ret
  cases.append(dict(lives=lives,deathCount=death_count,spellFlags=sf,elapsed=elapsed,bomb=active,timerFlags=tf,invFlags=invflags,available=available,output=[get(player+o) for o in fields]+[get(spell+0x78),get(spell+0x7c),get(0x4a57f4),get(0x4a5800),get(0x4a57cc),get(enemy+0x3c),get(enemy+0x44)]+[get(player+0x660+i*0xe4) for i in range(4)],events=list(events)))
 (ROOT/'artifacts/th16/player-death-native.json').write_text(json.dumps(dict(executableSha256=hashlib.sha256(img.data).hexdigest(),cases=cases),separators=(',',':'))+'\n',encoding='utf8');print(f'{len(cases)} native full player death transitions')
if __name__=='__main__':main()
