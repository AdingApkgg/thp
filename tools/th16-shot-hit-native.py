"""Full445d40 default branch and445e20, only ANM lookup controlled."""
import hashlib,importlib,itertools,json,struct
from pathlib import Path
from unicorn import *
from unicorn.x86_const import *
ROOT=Path(__file__).resolve().parents[1]
def main():
 img,_,_=importlib.import_module('th-anm-handlers').handlers(16);m=Uc(UC_ARCH_X86,UC_MODE_32)
 for _,base,size,raw,n in img.sections:
  start=base&~4095;m.mem_map(start,((base+size+4095)&~4095)-start);m.mem_write(base,img.data[raw:raw+n])
 ret,player,sht,vm,stack=0x70000000,0x70001000,0x70040000,0x70060000,0x700ff000;m.mem_map(ret,0x100000)
 put=lambda p,v:m.mem_write(p,struct.pack('<I',v&0xffffffff));get=lambda p:struct.unpack('<I',m.mem_read(p,4))[0];bits=lambda v:struct.unpack('<I',struct.pack('<f',v))[0];rows=[]
 put(0x4a6ef8,player);put(player+0x2c788,sht);put(player+0x2c78c,sht);put(sht+0x190,sht+0x200);m.mem_write(sht+0x200,bytes(0x58))
 def hook(uc,address,length,data):
  sp=m.reg_read(UC_X86_REG_ESP);assert get(sp+4)==77;m.reg_write(UC_X86_REG_EAX,vm);m.reg_write(UC_X86_REG_ESP,sp+8);m.reg_write(UC_X86_REG_EIP,get(sp))
 m.hook_add(UC_HOOK_CODE,hook,begin=0x46efa0,end=0x46efa0)
 for family,index,id,speed,hit,flags,pending in itertools.product((0,1),(0,255),(1,256),(0.,4.,16.),(-9,13),(0,1,0xabcdef07),(-1,7)):
  m.mem_write(player+0x1110,bytes(256*0xc0));m.mem_write(player+0xd114,bytes(256*0x94));shot=player+0x1110+index*0xc0;area=player+0xd080+id*0x94
  for offset,value in ((0,3),(8,77),(0x8c,1),(0x9c,hit),(0xac,0x10000 if family else 0),(0xb0,id)):put(shot+offset,value)
  m.mem_write(shot+0x48,struct.pack('<fff',7.25,300.5,1.25));put(shot+0x60,bits(speed));put(shot+0x64,bits(-.75));put(area,flags);put(area+0x88,index)
  m.mem_write(vm,bytes(0x600));put(vm+0x530,0x100);put(vm+0x534,0x2800);put(vm+0x490,pending);m.mem_write(vm+0x5e0,struct.pack('<fff',11,22,33))
  put(stack,ret);put(stack+4,0);put(stack+8,bits(3));put(stack+12,bits(.5));m.reg_write(UC_X86_REG_ESP,stack);m.reg_write(UC_X86_REG_ECX,area);m.reg_write(UC_X86_REG_EDX,player+0x610);m.reg_write(UC_X86_REG_MXCSR,0x1f80);m.emu_start(0x445d40,ret,count=100000);assert m.reg_read(UC_X86_REG_EIP)==ret
  rows.append(dict(input=[family,index,id,speed,hit,flags,pending],output=[m.reg_read(UC_X86_REG_EAX)]+[get(shot+k) for k in (0,0x8c,8,0xb0,0x48,0x4c,0x50,0x60,0x64)]+[get(player+0xd080+j*0x94) for j in (1,256)]+[get(vm+k) for k in (0x490,0x5e0,0x5e4,0x5e8,0x530,0x534)]))
 (ROOT/'artifacts/th16/shot-hit-native.json').write_text(json.dumps(dict(executableSha256=hashlib.sha256(img.data).hexdigest(),rows=rows),separators=(',',':'))+'\n',encoding='utf8');print(f'{len(rows)} native TH16 default shot hits')
if __name__=='__main__':main()
