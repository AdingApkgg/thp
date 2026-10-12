"""Retail4425a3..442685 respawn arm; cancel consumers controlled."""
import hashlib,importlib,json,struct
from pathlib import Path
from unicorn import *
from unicorn.x86_const import *
ROOT=Path(__file__).resolve().parents[1]
def main():
 img,_,_=importlib.import_module('th-anm-handlers').handlers(16);m=Uc(UC_ARCH_X86,UC_MODE_32)
 for _,base,size,raw,n in img.sections:
  first=base&~4095;m.mem_map(first,((base+size+4095)&~4095)-first);m.mem_write(base,img.data[raw:raw+n])
 m.mem_map(0x70000000,0x100000);player,stack,bp=0x70001000,0x700f0000,0x700f8000
 def put(p,v):m.mem_write(p,struct.pack('<I',v&0xffffffff))
 def get(p):return struct.unpack('<I',m.mem_read(p,4))[0]
 events=[]
 def boundary(machine,address,size,user):
  sp=machine.reg_read(UC_X86_REG_ESP);pos=get(sp+4)
  events.append([0 if address==0x416d20 else 1]+list(struct.unpack('<3I',m.mem_read(pos,12)))+[machine.reg_read(UC_X86_REG_XMM2)&0xffffffff,0 if address==0x416d20 else get(sp+8),get(sp+8 if address==0x416d20 else sp+12)])
 for address,cleanup in ((0x416d20,8),(0x431a70,12)):
  m.mem_write(address,b'\xc2'+struct.pack('<H',cleanup));m.hook_add(UC_HOOK_CODE,boundary,begin=address,end=address)
 ages=(-2147483648,-100,-1,0,1,7,15,29,30,31,59,60,61,120,1234567,2147483647)
 cases=[]
 for n in range(512):
  age=ages[n%len(ages)];x=(-192,-12.25,0,192)[(n//16)%4];z=(-2,0,1.25,5)[(n//64)%4]
  m.mem_write(player,bytes(0x30000));put(player+0x628,age);m.mem_write(player+0x610,struct.pack('<fff',x,80.5,z));m.mem_write(player+0x2c76c,struct.pack('<fff',11.5,127.25,-2))
  for i in range(12):put(player+0x660+i*0xe4+0xd4,20+i)
  m.reg_write(UC_X86_REG_ESP,stack);m.reg_write(UC_X86_REG_EBP,bp);m.reg_write(UC_X86_REG_EDI,player);events.clear();m.emu_start(0x4425a3,0x442685,count=20000);assert m.reg_read(UC_X86_REG_EIP)==0x442685
  cases.append(dict(age=age,x=x,z=z,output=[get(player+0x620)]+list(struct.unpack('<3I',m.mem_read(player+0x610,12)))+[get(player+0x660+i*0xe4+0xd4) for i in range(12)],events=list(events)))
 (ROOT/'artifacts/th16/player-respawn-native.json').write_text(json.dumps(dict(executableSha256=hashlib.sha256(img.data).hexdigest(),cases=cases),separators=(',',':'))+'\n',encoding='utf8');print(f'{len(cases)} native respawn arm cases')
if __name__=='__main__':main()
