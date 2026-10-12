"""Execute retail ECL 802 and root resets, with argument/lookup/free boundaries."""
import hashlib,importlib,json,struct
from pathlib import Path
from unicorn import Uc,UC_ARCH_X86,UC_MODE_32,UC_HOOK_CODE
from unicorn.x86_const import *
ROOT=Path(__file__).resolve().parents[1]
def main():
 img,_,_=importlib.import_module('th-anm-handlers').handlers(14);m=Uc(UC_ARCH_X86,UC_MODE_32)
 for _,b,size,raw,n in img.sections:
  start=b&~4095;m.mem_map(start,((b+size+4095)&~4095)-start);m.mem_write(b,img.data[raw:raw+n])
 base=0x70000000;m.mem_map(base,0x80000);stack=base+0x7f000;manager=base+0x50000;code=base+0x60000;name=base+0x60100
 put=lambda p,v:m.mem_write(p,struct.pack('<I',v&0xffffffff))
 get=lambda p:struct.unpack('<I',m.mem_read(p,4))[0]
 selected=0;freed=[];lookups=[]
 def hook(uc,a,size,data):
  sp=uc.reg_read(UC_X86_REG_ESP)
  if a==0x42c1d0:assert get(sp+4)==0;uc.reg_write(UC_X86_REG_EAX,selected)
  elif a==0x4848b0:assert get(sp+4)==name;lookups.append(uc.reg_read(UC_X86_REG_ECX));uc.reg_write(UC_X86_REG_EAX,code)
  else:freed.append(get(sp+4))
 for a,cleanup in ((0x42c1d0,4),(0x4848b0,4),(0x4854fe,0)):
  m.mem_write(a,b'\xc2'+struct.pack('<H',cleanup) if cleanup else b'\xc3');m.hook_add(UC_HOOK_CODE,hook,begin=a,end=a)
 assert img.u32(0x429c50+img.read(0x429ef4+802-300,1)[0]*4)==0x429a9e
 rows=[]
 for selected in (0,3,7):
  for caller_slot in (-1,0,1,2,3):
   for pattern in range(8):
    for mode in range(4):
     for threads in (0,2):
      m.mem_write(base,bytes(0x7e000));put(0x4db544,manager);put(base+0x11f0+0x4064,caller_slot);m.mem_write(name,b'Next\0');freed.clear();lookups.clear()
      for slot in range(3):
       owner=base+0x10000*(slot+1);put(manager+0x5c+slot*4,owner if pattern&(1<<slot) else 0)
       put(owner+0x11cc,0x12340000+slot);put(owner+8,0x42f70000+slot);put(owner+12,code+16);put(owner+0x1010,128);put(owner+0x1014,64);put(owner+0x11c8,3);put(owner+0x1020,77);put(owner+0x11d4,owner+0x8000 if threads else 0)
       for n in range(threads):
        node=owner+0x8000+n*16;put(node,owner+0x8100+n*0x100);put(node+4,node+16 if n+1<threads else 0)
       phase=owner+0x525c+selected*16;put(phase,0xffffffff if mode&1 else 177);put(phase+8,0 if mode&2 else name)
      m.reg_write(UC_X86_REG_ESP,stack);m.reg_write(UC_X86_REG_EDI,base+0x11f0);m.emu_start(0x429a9e,0x429c28,count=10000);assert m.reg_read(UC_X86_REG_EIP)==0x429c28
      states=[]
      for slot in range(3):
       owner=base+0x10000*(slot+1);states.append([get(owner+8),int(get(owner+12)==code),get(owner+0x1010),get(owner+0x1014),get(owner+0x11c8),get(owner+0x1020),int(bool(get(owner+0x11d4))),get(owner+0x525c+selected*16)])
      rows.append(dict(selected=selected,callerSlot=caller_slot,pattern=pattern,mode=mode,threads=threads,states=states,freeCount=len(freed),lookupCount=len(lookups)))
 out=ROOT/'artifacts/th14/boss-interrupt-native.json';out.write_text(json.dumps(dict(executableSha256=hashlib.sha256(img.data).hexdigest(),cases=rows))+'\n',encoding='utf8');print(f'{len(rows)} retail boss interrupt cases.')
if __name__=='__main__':main()
