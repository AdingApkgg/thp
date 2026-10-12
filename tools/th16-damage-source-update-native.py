"""Original entire256-slot loop442a20..442b47; movement/math execute."""
import hashlib,importlib,json,struct
from pathlib import Path
from unicorn import *
from unicorn.x86_const import *
ROOT=Path(__file__).resolve().parents[1]
def main():
 img,_,_=importlib.import_module('th-anm-handlers').handlers(16);m=Uc(UC_ARCH_X86,UC_MODE_32)
 for _,base,size,raw,n in img.sections:
  start=base&~4095;m.mem_map(start,((base+size+4095)&~4095)-start);m.mem_write(base,img.data[raw:raw+n])
 player,stack=0x70001000,0x700ff000;m.mem_map(0x70000000,0x100000)
 put=lambda p,v:m.mem_write(p,struct.pack('<I',v&0xffffffff));bits=lambda v:struct.unpack('<I',struct.pack('<f',v))[0];rows=[]
 for seed in range(512):
  scale=1. if seed&128 else (0.,.5,1.,1.5)[seed%4];put(0x4a5788,bits(scale));put(0x490eb0,0 if seed&128 else 0x4a5788);m.mem_write(player+0xd114,bytes(256*0x94))
  for id in (1,2,256):
   w=[0]*37;w[0]=(0,1,3,5,7)[(seed+id)%5];w[1]=bits(3.5);w[2]=bits(-.5 if seed&1 else .25);w[3]=bits((-7.,.75,7.)[(seed//8)%3]);w[4]=bits(.25 if seed&2 else -.1);w[7]=bits(2.25+id*.5);w[8]=bits(300.5);w[9]=bits(1.25);w[13]=bits(6.25 if seed&4 else 0);w[14]=bits(-.75);w[22]=bits(2);clock=(0,1,3,9999999)[(seed//16)%4];w[24]=0;w[25]=clock;w[26]=bits(clock+.25);w[27]=(0,1,0xffffffff)[(seed//64)%3];w[28]=5;w[33]=7;m.mem_write(player+0xd080+id*0x94,struct.pack('<37I',*w))
  m.reg_write(UC_X86_REG_ESP,stack);m.reg_write(UC_X86_REG_EBP,stack+0x200);m.reg_write(UC_X86_REG_EDI,player);m.reg_write(UC_X86_REG_MXCSR,0x1f80);m.reg_write(UC_X86_REG_FPCW,0x37f);m.reg_write(UC_X86_REG_FPSW,0);m.reg_write(UC_X86_REG_FPTAG,0xffff);m.emu_start(0x442a20,0x442b48,count=200000);assert m.reg_read(UC_X86_REG_EIP)==0x442b48
  rows.append(dict(seed=seed,areas={str(id):list(struct.unpack('<37I',m.mem_read(player+0xd080+id*0x94,0x94))) for id in (1,2,256)}))
 (ROOT/'artifacts/th16/damage-source-update-native.json').write_text(json.dumps(dict(executableSha256=hashlib.sha256(img.data).hexdigest(),rows=rows),separators=(',',':'))+'\n',encoding='utf8');print(f'{len(rows)} native TH16256-slot damage source updates')
if __name__=='__main__':main()
