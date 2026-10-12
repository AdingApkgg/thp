"""Actual retail VM writes and reads of shared, Boss and position references."""
import hashlib,importlib,json,struct
from pathlib import Path
from unicorn import Uc,UC_ARCH_X86,UC_MODE_32
from unicorn.x86_const import *
ROOT=Path(__file__).resolve().parents[1]
def main():
 img,_,_=importlib.import_module('th-anm-handlers').handlers(16);m=Uc(UC_ARCH_X86,UC_MODE_32)
 for _,b,size,raw,n in img.sections:
  first=b&~4095;m.mem_map(first,((b+size+4095)&~4095)-first);m.mem_write(b,img.data[raw:raw+n])
 base,boss,manager,code,stack,end=0x70000000,0x70008000,0x70010000,0x70020000,0x7003f000,0x7003e000;m.mem_map(base,0x40000)
 put=lambda p,v:m.mem_write(p,struct.pack('<I',v&0xffffffff))
 get=lambda p:struct.unpack('<I',m.mem_read(p,4))[0]
 bits=lambda f:struct.unpack('<I',struct.pack('<f',f))[0]
 def ins(op,args,refs=0,time=0):return struct.pack('<iHHHBBI',time,op,16+4*len(args),refs,255,len(args),0)+struct.pack('<'+'I'*len(args),*[v&0xffffffff for v in args])
 own=[base+0x1498+j*4 for j in range(12)]+[base+o for o in (0x1294,0x1298,0x12d8,0x12dc)]
 other=[boss+0x1498+j*4 for j in range(8)]
 shared=[manager+0x3c+j*4 for j in range(3)]+[manager+0xc+j*4 for j in range(12)]
 addresses=own+other+shared;initial=[j+11 for j in range(len(addresses))];rows=[]
 ids=[(i,0) for i in (*range(-9926,-9922),*range(-9943,-9939))]+[(i,1) for i in (*range(-9922,-9914),*range(-9939,-9935),*range(-9995,-9991))]
 for id,floating in ids:
  values=[bits(v) for v in (-123.25,-0.,0.,123.25,16777216.)]+[0x7fc01234,0x7f800000,0xff800000] if floating else [0,1,0xffffffff,16777217,0x80000000,0x7fffffff]
  for present in (0,1):
   for value in values:
    m.mem_write(base,bytes(0x3d000));put(base,0x4921a8);put(0x4a6dc0,manager);put(manager+0x48,17 if present else 0);put(manager+0x180,manager+0x200);put(manager+0x200,boss);put(boss+0x5740,17)
    for p,v in zip(addresses,initial):put(p,v)
    payload=ins(44 if floating else 42,[value])+ins(45 if floating else 43,[bits(id) if floating else id],1)+ins(42,[id],1)+ins(44,[bits(id)],1)+ins(0,[],time=2147483647)
    m.mem_write(code,bytes(16)+payload);context=base+8;put(context+4,0);put(context+8,0);put(context+0x1018,base);put(context+0x1020,255);put(base+0x11f8,base+0x30000);put(base+0x3008c,base+0x31000);put(base+0x31004,code);put(stack,end)
    m.reg_write(UC_X86_REG_ECX,context);m.reg_write(UC_X86_REG_ESP,stack);m.reg_write(UC_X86_REG_XMM1,0);m.reg_write(UC_X86_REG_MXCSR,0x1f80);m.reg_write(UC_X86_REG_FPCW,0x37f);m.reg_write(UC_X86_REG_FPSW,0);m.reg_write(UC_X86_REG_FPTAG,0xffff)
    m.emu_start(0x472030,end,count=20000);assert m.reg_read(UC_X86_REG_EIP)==end and get(context+0x100c)==16
    rows.append(dict(id=id,floating=floating,present=present,value=value,code=payload.hex(),storage=[get(p) for p in addresses],reads=[get(context+16),get(context+24)]))
 out=ROOT/'artifacts/th16/ecl-globals-native.json';out.write_text(json.dumps(dict(executableSha256=hashlib.sha256(img.data).hexdigest(),initial=initial,cases=rows))+'\n',encoding='utf8');print(f'{len(rows)} retail global reference write/read cases.')
if __name__=='__main__':main()
