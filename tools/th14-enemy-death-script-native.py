"""Retail ECL556 setter and 424c21..424c8b death-subroutine delivery."""
import hashlib,importlib,json,struct
from pathlib import Path
from unicorn import Uc,UC_ARCH_X86,UC_MODE_32,UC_HOOK_CODE
from unicorn.x86_const import *
ROOT=Path(__file__).resolve().parents[1]
def main():
 img,_,_=importlib.import_module('th-anm-handlers').handlers(14);m=Uc(UC_ARCH_X86,UC_MODE_32)
 for _,b,size,raw,n in img.sections:
  start=b&~4095;m.mem_map(start,((b+size+4095)&~4095)-start);m.mem_write(b,img.data[raw:raw+n])
 base,code,stack,end=0x70000000,0x70020000,0x7003f000,0x7003e000;m.mem_map(base,0x40000)
 put=lambda p,v:m.mem_write(p,struct.pack('<I',v&0xffffffff))
 get=lambda p:struct.unpack('<I',m.mem_read(p,4))[0]
 bits=lambda f:struct.unpack('<I',struct.pack('<f',f))[0]
 def ins(op,args,refs=0,time=0):return struct.pack('<iHHHBBI',time,op,16+4*len(args),refs,255,len(args),0)+struct.pack('<'+'I'*len(args),*args)
 freed=[];lookups=[]
 def hook(machine,address,size,user):
  sp=m.reg_read(UC_X86_REG_ESP)
  if address==0x4854fe:freed.append(get(sp+4))
  else:
   assert bytes(m.mem_read(get(sp+4),6))==b'Death\0';lookups.append(get(sp+4));m.reg_write(UC_X86_REG_EAX,code)
 for p,cleanup in ((0x4854fe,0),(0x4848b0,4)):
  m.mem_write(p,b'\xc2'+struct.pack('<H',cleanup) if cleanup else b'\xc3');m.hook_add(UC_HOOK_CODE,hook,begin=p,end=p)
 rows=[]
 for n in range(4):
  for value in (-123.25,0.,123.25):
   for dirty in (0,128):
    freed.clear();lookups.clear();m.mem_write(base,bytes(0x3d000));payload=ins(40,[4])+ins(44,[bits(value)])+ins(45,[bits(0)],1)+ins(0,[],time=2147483647);m.mem_write(code,payload)
    name=base+0x18000;m.mem_write(name,b'Death\0');instruction=name-20
    m.reg_write(UC_X86_REG_EDI,base+0x11f0);m.reg_write(UC_X86_REG_ESI,instruction);m.reg_write(UC_X86_REG_ESP,stack);m.emu_start(0x4287ac,0x429c28,count=1000);assert get(base+0x52f8)==name
    put(base+0x1010,dirty);put(base+0x1014,dirty);put(base+0x1024,255);put(base+0x11d4,base+0x10000 if n else 0)
    for j in range(n):
     node=base+0x10000+j*16;put(node,base+0x11000+j*0x1100);put(node+4,node+16 if j+1<n else 0)
    m.reg_write(UC_X86_REG_EBX,base);m.reg_write(UC_X86_REG_ESP,stack);m.reg_write(UC_X86_REG_MXCSR,0x1f80);m.reg_write(UC_X86_REG_FPCW,0x37f);m.reg_write(UC_X86_REG_FPSW,0);m.reg_write(UC_X86_REG_FPTAG,0xffff)
    m.emu_start(0x424c21,0x424c8b,count=20000);assert m.reg_read(UC_X86_REG_EIP)==0x424c8b
    assert len(freed)==2*n and len(lookups)==1
    output=[get(base+8),get(base+12)-code,get(base+0x1010),get(base+0x1014),get(base+16),get(base+0x52f8),get(base+0x11d4)]
    rows.append(dict(threads=n,value=bits(value),dirty=dirty,code=payload.hex(),output=output,freeCount=len(freed)))
 out=ROOT/'artifacts/th14/enemy-death-script-native.json';out.write_text(json.dumps(dict(executableSha256=hashlib.sha256(img.data).hexdigest(),cases=rows))+'\n',encoding='utf8');print(f'{len(rows)} retail death subroutine cases.')
if __name__=='__main__':main()
