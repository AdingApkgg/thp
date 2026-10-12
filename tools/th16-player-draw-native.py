"""Full443730; only468490 rendering is controlled."""
import hashlib,importlib,itertools,json,struct
from pathlib import Path
from unicorn import *
from unicorn.x86_const import *
ROOT=Path(__file__).resolve().parents[1]
def main():
 img,_,_=importlib.import_module('th-anm-handlers').handlers(16);m=Uc(UC_ARCH_X86,UC_MODE_32)
 for _,base,size,raw,n in img.sections:
  start=base&~4095;m.mem_map(start,((base+size+4095)&~4095)-start);m.mem_write(base,img.data[raw:raw+n])
 ret,player,stack=0x70000000,0x70001000,0x700ff000;m.mem_map(ret,0x100000)
 put=lambda p,v:m.mem_write(p,struct.pack('<I',v&0xffffffff));get=lambda p:struct.unpack('<I',m.mem_read(p,4))[0]
 m.mem_write(0x468490,b'\xc2\x04\x00');put(0x4a6ef8,player);rows=[]
 for flags,life,position in itertools.product((0,0x40000,0x80000,0xc0000,0x200500,0xffffffff),range(5),((0.,400.,0.),(-183.5,16.25,1.75),(183.5,431.75,-.125))):
  m.mem_write(player+0x5f4,struct.pack('<fff',91.,-72.,33.));m.mem_write(player+0x610,struct.pack('<fff',*position));put(player+0x548,flags);put(player+0x165a8,life);put(stack,ret);m.reg_write(UC_X86_REG_ESP,stack);m.reg_write(UC_X86_REG_ECX,player);m.emu_start(0x443730,ret,count=1000);assert m.reg_read(UC_X86_REG_EIP)==ret
  rows.append(dict(flags=flags,life=life,position=position,output=[get(player+o) for o in (0x5f4,0x5f8,0x5fc,0x548)]))
 (ROOT/'artifacts/th16/player-draw-native.json').write_text(json.dumps(dict(executableSha256=hashlib.sha256(img.data).hexdigest(),rows=rows))+'\n',encoding='utf8');print(f'{len(rows)} native TH16 player draw preparations')
if __name__=='__main__':main()
