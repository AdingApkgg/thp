"""Own TH16 500/501 stores and chapter-count side effect, controlled float args."""
import hashlib,importlib,json,struct
from pathlib import Path
from unicorn import *
from unicorn.x86_const import *
ROOT=Path(__file__).resolve().parents[1]
def main():
 img,_,_=importlib.import_module('th-anm-handlers').handlers(16);m=Uc(UC_ARCH_X86,UC_MODE_32)
 for _,base,size,raw,n in img.sections:
  first=base&~4095;m.mem_map(first,((base+size+4095)&~4095)-first);m.mem_write(base,img.data[raw:raw+n])
 m.mem_map(0x70000000,0x20000);data,stack=0x70001000,0x7001e000;args=[]
 def put(p,v):m.mem_write(p,struct.pack('<I',v&0xffffffff))
 def get(p):return struct.unpack('<I',m.mem_read(p,4))[0]
 def arg(machine,address,size,user):machine.reg_write(UC_X86_REG_XMM0,args[get(machine.reg_read(UC_X86_REG_ESP)+4)])
 m.mem_write(0x425200,b'\xc2\x04\x00');m.hook_add(UC_HOOK_CODE,arg,begin=0x425200,end=0x425200)
 rows=[]
 values=(0,0x80000000,0x3f800000,0xbf800000,0x41c00000,0x43000000,0x7f800000,0xff800000)
 for op in (500,501):
  for x in values:
   for y in values:
    for credit in (0,1,7,0xffffffff):
     for o in (0x110,0x114,0x118,0x11c):put(data+o,0x41c00000)
     put(data+0x452c,credit);put(0x4a5880,0xffffffff);args=[x,y];m.reg_write(UC_X86_REG_EDI,data);m.reg_write(UC_X86_REG_ESP,stack)
     m.emu_start(0x42034f if op==500 else 0x420393,0x422a9b,count=1000)
     rows.append(dict(op=op,args=args.copy(),credit=credit,output=[get(data+o) for o in (0x110,0x114,0x118,0x11c,0x452c)]+[get(0x4a5880)]))
 out=ROOT/'artifacts/th16/hitbox-native.json';out.write_text(json.dumps(dict(executableSha256=hashlib.sha256(img.data).hexdigest(),cases=rows),indent=2)+'\n',encoding='utf-8');print(f'{len(rows)} native TH16 hitbox/collision stores')
if __name__=='__main__':main()
