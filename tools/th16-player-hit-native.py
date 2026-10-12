"""Whole443f10 player hit. Sound, effect factory and body bind/tick controlled."""
import hashlib,importlib,json,struct
from pathlib import Path
from unicorn import *
from unicorn.x86_const import *
ROOT=Path(__file__).resolve().parents[1]
def main():
 img,_,_=importlib.import_module('th-anm-handlers').handlers(16);m=Uc(UC_ARCH_X86,UC_MODE_32)
 for _,base,size,raw,n in img.sections:
  first=base&~4095;m.mem_map(first,((base+size+4095)&~4095)-first);m.mem_write(base,img.data[raw:raw+n])
 m.mem_map(0x70000000,0x100000);player,spell,bomb,effect,out,stack,ret=0x70001000,0x70040000,0x70041000,0x70042000,0x70043000,0x700ff000,0x700fe000
 def put(p,v):m.mem_write(p,struct.pack('<I',v&0xffffffff))
 def get(p):return struct.unpack('<I',m.mem_read(p,4))[0]
 events=[]
 def boundary(machine,address,size,user):
  sp=machine.reg_read(UC_X86_REG_ESP)
  if address==0x45e150:events.append([1,get(sp+4)])
  elif address==0x40e5c0:
   dest,script,pos,angle,layer=[get(sp+k) for k in (4,8,12,16,20)];assert script==29 and layer==0xffffffff and angle==0;assert struct.unpack('<fff',m.mem_read(pos,12))==(-12.25,80.5,1.25);events.append([2,script]);put(dest,7);machine.reg_write(UC_X86_REG_EAX,dest)
  elif address==0x407b20:assert get(sp+4)==player+0x14;events.append([3,get(sp+8)])
  elif address==0x45f980:events.append([4,0]);machine.reg_write(UC_X86_REG_EAX,0)
 for address,cleanup in ((0x45e150,8),(0x40e5c0,24),(0x407b20,8),(0x45f980,0)):
  m.mem_write(address,b'\xc2'+struct.pack('<H',cleanup) if cleanup else b'\xc3');m.hook_add(UC_HOOK_CODE,boundary,begin=address,end=address)
 put(0x4a6db0,spell);put(0x4a6da8,bomb);put(0x4a6db8,effect);put(effect+0xc,out)
 fields=(0x165a8,0x624,0x628,0x62c,0x634,0x16638,0x1663c,0x16640,0x16648)
 cases=[]
 for n in range(1024):
  flags=(0,8,0x10,0x18,0xffffffff)[n%5];sf=(0,1,0x21,0x23,0xffffffff)[(n//5)%5];elapsed=(-1,0,59,60,61)[(n//25)%5];active=(n//125)%2;tf=(0,1,2,0xffffffff)[(n//7)%4];invflags=(0,1,2,0xffffffff)[(n//11)%4]
  m.mem_write(player,bytes(0x30000));put(player+0x1664c,flags);put(player+0x634,tf);put(player+0x16648,invflags);put(player+0x165a8,1);m.mem_write(player+0x610,struct.pack('<fff',-12.25,80.5,1.25));put(spell+0x78,sf);put(spell+0x24,elapsed);put(spell+0x7c,12345);put(bomb+0x30,active);put(player+0x5c0,123);put(player+0x5c4,456)
  put(stack,ret);m.reg_write(UC_X86_REG_ESP,stack);m.reg_write(UC_X86_REG_ECX,player);events.clear();m.emu_start(0x443f10,ret,count=20000);assert m.reg_read(UC_X86_REG_EIP)==ret
  cases.append(dict(flags=flags,spellFlags=sf,elapsed=elapsed,bomb=active,timerFlags=tf,invFlags=invflags,output=[get(player+o) for o in fields]+[get(spell+0x78),get(spell+0x7c)],parents=[get(player+0x5c0),get(player+0x5c4)],events=list(events)))
 (ROOT/'artifacts/th16/player-hit-native.json').write_text(json.dumps(dict(executableSha256=hashlib.sha256(img.data).hexdigest(),cases=cases),separators=(',',':'))+'\n',encoding='utf8');print(f'{len(cases)} native full player hit transitions')
if __name__=='__main__':main()
