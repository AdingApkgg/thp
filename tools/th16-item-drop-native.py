"""Full420585 ECL509,41a720 drop and41d700 scatter. Only430960 factory controlled."""
import hashlib,importlib,json,struct
from pathlib import Path
from unicorn import *
from unicorn.x86_const import *
ROOT=Path(__file__).resolve().parents[1]
def main():
 img,_,_=importlib.import_module('th-anm-handlers').handlers(16);m=Uc(UC_ARCH_X86,UC_MODE_32)
 for _,base,size,raw,n in img.sections:
  first=base&~4095;m.mem_map(first,((base+size+4095)&~4095)-first);m.mem_write(base,img.data[raw:raw+n])
 ret,data,stack=0x70000000,0x70001000,0x700ff000;m.mem_map(ret,0x100000);rows=[];events=[]
 put=lambda p,v:m.mem_write(p,struct.pack('<I',v&0xffffffff));get=lambda p:struct.unpack('<I',m.mem_read(p,4))[0];bits=lambda v:struct.unpack('<I',struct.pack('<f',v))[0]
 def hook(uc,address,size,user):
  sp=m.reg_read(UC_X86_REG_ESP);p=get(sp+8);events.append([get(sp+4),*[get(p+k) for k in (0,4,8)],get(sp+16),get(sp+20),get(sp+28)]);m.reg_write(UC_X86_REG_EAX,0);m.reg_write(UC_X86_REG_ESP,sp+32);m.reg_write(UC_X86_REG_EIP,get(sp))
 m.hook_add(UC_HOOK_CODE,hook,begin=0x430960,end=0x430960)
 m.hook_add(UC_HOOK_MEM_INVALID,lambda uc,access,addr,size,value,user:print('invalid',hex(m.reg_read(UC_X86_REG_EIP)),hex(addr),seed) or False);m.mem_write(0x4c10b6,b'\0')
 for seed in range(1536):
  events=[];m.mem_write(data,bytes(0x5000));put(0x4a5bec,0x20 if seed&1 else 0);put(0x4a6d88,(seed*997+17)&65535);put(0x4a6d8c,9)
  primary=(0,1,8,15,16,0)[(seed//2)%6];put(data+0x3f90,primary)
  for n in range(17):put(data+0x3f94+n*4,((seed//12+n)%4) if n==seed%16 or n==15 else -1 if n==16 else 0)
  put(data+0x4054,(0,1,3)[(seed//48)%3]);put(data+0x4050,60);put(data+0x4040,(-1,0,1,30,60,90)[(seed//144)%6]);m.mem_write(data+0x3fd8,struct.pack('<ff',(-8.,0.,32.)[(seed//96)%3],(0.,16.,64.)[(seed//288)%3]));m.mem_write(data+0x44,struct.pack('<fff',7.25,300.5,1.25))
  m.reg_write(UC_X86_REG_ESP,stack);m.reg_write(UC_X86_REG_EDI,data);m.reg_write(UC_X86_REG_MXCSR,0x1f80);m.reg_write(UC_X86_REG_FPCW,0x37f);m.reg_write(UC_X86_REG_FPSW,0);m.reg_write(UC_X86_REG_FPTAG,0xffff);m.emu_start(0x420585,0x422a9b,count=500000);assert m.reg_read(UC_X86_REG_EIP)==0x422a9b
  rows.append(dict(seed=seed,output=[get(0x4a6d88)&65535,get(0x4a6d8c),get(data+0x3f90)]+[get(data+0x3f94+n*4) for n in range(17)],events=events))
 (ROOT/'artifacts/th16/item-drop-native.json').write_text(json.dumps(dict(executableSha256=hashlib.sha256(img.data).hexdigest(),rows=rows),separators=(',',':'))+'\n',encoding='utf8');print(f'{len(rows)} native TH16 ECL509/item scatter cases')
if __name__=='__main__':main()
