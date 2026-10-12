"""Whole40e6c0 chooser; VM-ID lookup is controlled and its ordered calls recorded."""
import hashlib,importlib,json,struct
from pathlib import Path
from unicorn import *
from unicorn.x86_const import *
ROOT=Path(__file__).resolve().parents[1]
def table(seed,mode):
 out=[];value=seed
 for i in range(1024):
  value=(value*1664525+1013904223)&0xffffffff
  out.append(0 if mode==0 else 1 if mode==1 else 2 if mode==2 else 0 if mode==3 and i==17 else 1 if mode==4 and i==17 else 2 if mode in (3,4) else value%7)
 return out
def main():
 img,_,_=importlib.import_module('th-anm-handlers').handlers(16);m=Uc(UC_ARCH_X86,UC_MODE_32)
 for _,base,size,raw,n in img.sections:
  first=base&~4095;m.mem_map(first,((base+size+4095)&~4095)-first);m.mem_write(base,img.data[raw:raw+n])
 m.mem_map(0x70000000,0x20000);manager,stack,ret=0x70001000,0x70018000,0x7001e000
 def put(p,v):m.mem_write(p,struct.pack('<I',v&0xffffffff))
 def get(p):return struct.unpack('<I',m.mem_read(p,4))[0]
 events=[]
 def lookup(machine,address,size,user):
  ident=get(machine.reg_read(UC_X86_REG_ESP)+4);events.append(ident);machine.reg_write(UC_X86_REG_EAX,0x70008000 if ident%4==1 else 0)
 m.mem_write(0x46efa0,b'\xc2\x04\x00');m.hook_add(UC_HOOK_CODE,lookup,begin=0x46efa0,end=0x46efa0)
 cases=[]
 for cursor in (0,1,1022,1023):
  for mode in range(6):
   for seed in range(1,9):
    values=table(seed,mode);put(manager+0x18,cursor);m.mem_write(manager+0x1c,struct.pack('<1024I',*values));timeline=[]
    for frame in range(16):
     put(stack,ret);m.reg_write(UC_X86_REG_ESP,stack);m.reg_write(UC_X86_REG_ECX,manager);events.clear();m.emu_start(0x40e6c0,ret,count=100000);assert m.reg_read(UC_X86_REG_EIP)==ret
     slot=m.reg_read(UC_X86_REG_EAX);ident=100+frame
     if slot!=0xffffffff:put(manager+0x1c+slot*4,ident)
     timeline.append(dict(slot=slot,cursor=get(manager+0x18),id=ident,events=list(events),ids=list(struct.unpack('<1024I',m.mem_read(manager+0x1c,4096)))))
    cases.append(dict(cursor=cursor,mode=mode,seed=seed,timeline=timeline))
 (ROOT/'artifacts/th16/effect-slots-native.json').write_text(json.dumps(dict(executableSha256=hashlib.sha256(img.data).hexdigest(),cases=cases),separators=(',',':'))+'\n',encoding='utf8');print(f'{len(cases)} native effect-slot timelines / {len(cases)*16} calls')
if __name__=='__main__':main()
