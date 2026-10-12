"""444e10 through4451ef, actual402ff0 and visual RNG execute, no allocations."""
import hashlib,importlib,itertools,json,struct
from pathlib import Path
from unicorn import *
from unicorn.x86_const import *
ROOT=Path(__file__).resolve().parents[1]
def main():
 img,_,_=importlib.import_module('th-anm-handlers').handlers(16);m=Uc(UC_ARCH_X86,UC_MODE_32)
 for _,base,size,raw,n in img.sections:
  start=base&~4095;m.mem_map(start,((base+size+4095)&~4095)-start);m.mem_write(base,img.data[raw:raw+n])
 ret,player,sht,shot,stack=0x70000000,0x70001000,0x70040000,0x70050000,0x700ff000;m.mem_map(ret,0x100000)
 put=lambda p,v:m.mem_write(p,struct.pack('<I',v&0xffffffff));get=lambda p:struct.unpack('<I',m.mem_read(p,4))[0]
 bits=lambda v:struct.unpack('<I',struct.pack('<f',v))[0];rows=[]
 put(0x4a6ef8,player);put(player+0x2c788,sht);put(player+0x2c78c,sht);put(sht+0x190,sht+0x200);put(0x490eb0,0x4a5788)
 for i in range(12):
  o=player+0x660+i*0xe4;put(o+0x5c,-321+i*777);put(o+0x60,50319-i*333);put(o+0xa8,bits((i-5)*.75))
 m.mem_write(player+0x610,struct.pack('<fff',7.25,400.5,1.25));spec=sht+0x200
 for number,kind,angle,speed,focus,family,seed,rate in itertools.product((0,1,4,101,106),(0,2),(-7.,-.75,995.,1000.),(0.,6.25),(0,1),(0,1),(0,12345),(0.,.5,1.,1.5)):
  if number==0 and kind==2:continue
  m.mem_write(spec,bytes(0x58));m.mem_write(shot,bytes(0xc0));put(shot,0x80000000);put(shot+0x1c,1)
  m.mem_write(spec+2,struct.pack('<h',13));m.mem_write(spec+0xc,struct.pack('<ffff',4.25,7.5,angle,speed));m.mem_write(spec+0x20,struct.pack('<bb',number,kind))
  put(player+0x165c8,focus);put(0x4a57e4,399);put(0x4a57ec,100);put(0x4a5788,bits(rate));put(0x4a6d88,seed);put(0x4a6d8c,17)
  for i in range(16):put(player+0x165f8+i*4,123)
  put(stack,ret);put(stack+4,0x10000 if family else 0);put(stack+8,7);put(stack+12,player+0x610);m.reg_write(UC_X86_REG_ESP,stack);m.reg_write(UC_X86_REG_ECX,shot);m.reg_write(UC_X86_REG_MXCSR,0x1f80);m.reg_write(UC_X86_REG_FPCW,0x37f);m.reg_write(UC_X86_REG_FPSW,0);m.reg_write(UC_X86_REG_FPTAG,0xffff);m.emu_start(0x444e10,0x4451f0,count=100000);assert m.reg_read(UC_X86_REG_EIP)==0x4451f0
  rows.append(dict(number=number,kind=kind,angle=angle,speed=speed,focus=focus,family=family,seed=seed,rate=rate,output=[get(shot+k) for k in (0,0x8c,0xac,0xc,0x10,0x14,0x9c,0xa0,0xa4)]+[get(0x4a6d88)&65535,get(0x4a6d8c)]+[get(player+0x165f8+i*4) for i in range(16)],movement=[get(shot+k) for k in (0x48,0x4c,0x50,0x60,0x64,0x7c,0x80,0x84)]))
 (ROOT/'artifacts/th16/shot-spawn-native.json').write_text(json.dumps(dict(executableSha256=hashlib.sha256(img.data).hexdigest(),rows=rows),separators=(',',':'))+'\n',encoding='utf8');print(f'{len(rows)} native TH16 shot spawn prefixes')
if __name__=='__main__':main()
