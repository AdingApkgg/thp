"""Retail442724..442895 death drops. Original angle helper executes; item/rebuild controlled."""
import hashlib,importlib,json,struct,itertools
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
  sp=machine.reg_read(UC_X86_REG_ESP)
  if address==0x430960:
   kind,pos,unused,angle,speed,unused2,force=[get(sp+k) for k in (4,8,12,16,20,24,28)];events.append([kind]+list(struct.unpack('<3I',m.mem_read(pos,12)))+[angle,speed,force]);machine.reg_write(UC_X86_REG_EAX,0)
  elif address==0x4440e0:events.append([100,machine.reg_read(UC_X86_REG_ECX)-player])
 for address,cleanup in ((0x430960,28),(0x4440e0,0)):
  m.mem_write(address,b'\xc2'+struct.pack('<H',cleanup) if cleanup else b'\xc3');m.hook_add(UC_HOOK_CODE,boundary,begin=address,end=address)
 cases=[]
 for power,step,position in itertools.product((-2147483648,-1,0,49,50,99,100,200,400,2147483647),(-101,-1,0,1,99,100,101,200),((0,400,1.25),(-12.25,80.5,0),(192,16,-1.5),(0,1e10,5))):
  put(0x4a57e4,power);put(0x4a57ec,step);m.mem_write(player+0x610,struct.pack('<fff',*position));put(bp-0x28,player);m.reg_write(UC_X86_REG_ESP,stack);m.reg_write(UC_X86_REG_EBP,bp);m.reg_write(UC_X86_REG_EDI,player);m.reg_write(UC_X86_REG_XMM3,0);events.clear();m.emu_start(0x442724,0x442895,count=20000);assert m.reg_read(UC_X86_REG_EIP)==0x442895
  cases.append(dict(power=power,step=step,position=position,output=get(0x4a57e4),events=list(events)))
 (ROOT/'artifacts/th16/player-death-drops-native.json').write_text(json.dumps(dict(executableSha256=hashlib.sha256(img.data).hexdigest(),cases=cases),separators=(',',':'))+'\n',encoding='utf8');print(f'{len(cases)} native death drop cases / {len(cases)*7} item requests')
if __name__=='__main__':main()
