"""Execute the retail ending selection/status block; no callee is replaced."""
import hashlib,importlib,json,struct
from pathlib import Path
from unicorn import Uc,UC_ARCH_X86,UC_MODE_32
from unicorn.x86_const import *
ROOT=Path(__file__).resolve().parents[1]
def main():
 img,_,_=importlib.import_module('th-anm-handlers').handlers(14)
 m=Uc(UC_ARCH_X86,UC_MODE_32)
 for _,b,size,raw,n in img.sections:
  start=b&~4095;m.mem_map(start,((b+size+4095)&~4095)-start);m.mem_write(b,img.data[raw:raw+n])
 arena,manager,ending=0x70000000,0x70001000,0x70030000
 m.mem_map(arena,0x40000)
 def put(p,v):m.mem_write(p,struct.pack('<I',v&0xffffffff))
 def get(p):return struct.unpack('<I',m.mem_read(p,4))[0]
 put(0x4db68c,manager);rows=[]
 for selection in range(6):
  for difficulty in range(4):
   for continues in (0,1,9,-1):
    for initial in (0,1,2,0x10,0x80,0xff):
     data=bytes([initial])*0x42c;m.mem_write(manager+0x24230,data)
     m.mem_write(ending,bytes(0x100));put(0x4f5828,selection//2);put(0x4f582c,selection%2)
     put(0x4f5834,difficulty);put(0x4f5838,continues)
     m.reg_write(UC_X86_REG_EBX,ending)
     m.emu_start(0x41fbca,0x41fc37,count=200)
     assert m.reg_read(UC_X86_REG_EIP)==0x41fc37
     rows.append(dict(selection=selection,difficulty=difficulty,continues=continues,initial=initial,index=get(ending+0x1c),seen=get(ending+0x20),settings=bytes(m.mem_read(manager+0x24230,0x42c)).hex()))
 files=[]
 for n in range(13):
  p=img.u32(0x4d1d6c+n*4);files.append(img.read(p,40).split(b'\0')[0].decode('ascii'))
 out=ROOT/'artifacts/th14/ending-record-native.json'
 out.write_text(json.dumps(dict(executableSha256=hashlib.sha256(img.data).hexdigest(),files=files,rows=rows),indent=2)+'\n',encoding='utf-8')
 print(f'{len(rows)} retail ending index/seen/status cases')
if __name__=='__main__':main()
