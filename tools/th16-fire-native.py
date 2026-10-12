"""TH16 601 position/exclusion request and complete414da0 batch loop boundaries."""
import hashlib,importlib,json,struct
from pathlib import Path
from unicorn import *
from unicorn.x86_const import *
ROOT=Path(__file__).resolve().parents[1]
def main():
 img,_,_=importlib.import_module('th-anm-handlers').handlers(16);m=Uc(UC_ARCH_X86,UC_MODE_32)
 for _,base,size,raw,n in img.sections:
  first=base&~4095;m.mem_map(first,((base+size+4095)&~4095)-first);m.mem_write(base,img.data[raw:raw+n])
 m.mem_map(0x70000000,0x30000);data,manager,player,stack,ret=0x70001000,0x70008000,0x70009000,0x7002d000,0x7002e000
 def put(p,v):m.mem_write(p,struct.pack('<I',v&0xffffffff))
 def get(p):return struct.unpack('<I',m.mem_read(p,4))[0]
 def fs(p,values):m.mem_write(p,struct.pack('<'+'f'*len(values),*values))
 put(0x4a6dac,manager);put(0x4a6ef8,player);events=[];selected=0;status=0;limit=0
 def boundary(machine,address,size,user):
  sp=machine.reg_read(UC_X86_REG_ESP)
  if address==0x4251d0:machine.reg_write(UC_X86_REG_EAX,selected)
  elif address==0x414da0:events.append([get(sp+4)-data,get(manager+0x44)])
  elif address==0x412cb0:
   events.append([get(sp+8),get(sp+12),get(sp+16)]);machine.reg_write(UC_X86_REG_EAX,1 if limit and len(events)>=limit else status&0xffffffff)
  elif address==0x45e1f0:events.append(['sound',get(sp+4),machine.reg_read(UC_X86_REG_XMM2)&0xffffffff])
 for address,cleanup in ((0x4251d0,4),(0x414da0,4)):
  m.mem_write(address,b'\xc2'+struct.pack('<H',cleanup));hook=m.hook_add(UC_HOOK_CODE,boundary,begin=address,end=address)
  if address==0x414da0:entry_hook=hook
 rows=[]
 for selected in range(16):
  for origin_z in (0,.9,1,2):
   base=[selected*.25-3,4.125,-2];origin=[7.75,-9.5,origin_z];position=[11.25,37.5,2.25]
   fs(data+0x44,position);fs(data+0x3dd8+selected*12,base);fs(data+0x3e98+selected*12,origin);put(data+0x4074,0x42c80000)
   events.clear();m.reg_write(UC_X86_REG_EDI,data);m.reg_write(UC_X86_REG_EBP,stack+0x500);m.reg_write(UC_X86_REG_ESP,stack);m.emu_start(0x4209cf,0x422a9b,count=5000)
   rows.append(dict(index=selected,base=base,origin=origin,position=position,output=[get(data+0x5a0+selected*0x380+j*4) for j in range(3)],requests=list(events),exclusionAfter=get(manager+0x44)))
 # Restore actual batch body, only low-level spawn and sound are boundaries.
 m.mem_write(0x414da0,img.read(0x414da0,3));m.hook_del(entry_hook)
 batches=[]
 for address,cleanup in ((0x412cb0,16),(0x45e1f0,4)):
  m.mem_write(address,b'\xc2'+struct.pack('<H',cleanup));m.hook_add(UC_HOOK_CODE,boundary,begin=address,end=address)
 emitter=data+0x598
 for count,layers in ((-1,3),(0,3),(1,1),(3,2),(7,4)):
  for flags in (0,0x20):
   for status,limit in ((0,0),(-1,0),(0,1),(0,4)):
    for target in ((1.,2.,0.),(-1.5,8.125,0.)):
     fs(emitter+8,[1,2,3]);fs(player+0x610,target);m.mem_write(emitter+0x364,struct.pack('<2h',count,layers));put(emitter+0x36c,flags);put(emitter+0x370,21)
     put(stack,ret);put(stack+4,emitter);m.reg_write(UC_X86_REG_ECX,manager);m.reg_write(UC_X86_REG_ESP,stack);events.clear();m.emu_start(0x414da0,ret,count=5000)
     batches.append(dict(count=count,layers=layers,flags=flags,status=status,limit=limit,target=target,events=list(events)))
 out=ROOT/'artifacts/th16/fire-native.json';out.write_text(json.dumps(dict(executableSha256=hashlib.sha256(img.data).hexdigest(),positions=rows,batches=batches),indent=2)+'\n',encoding='utf-8');print(f'{len(rows)} native fire positions; {len(batches)} batch loops')
if __name__=='__main__':main()
