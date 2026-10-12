"""Actual retail VM writes and reads of shared, Boss and position references."""
import hashlib,importlib,json,struct
from pathlib import Path
from unicorn import Uc,UC_ARCH_X86,UC_MODE_32
from unicorn.x86_const import *
ROOT=Path(__file__).resolve().parents[1]
def main():
 img,_,_=importlib.import_module('th-anm-handlers').handlers(14);m=Uc(UC_ARCH_X86,UC_MODE_32)
 for _,b,size,raw,n in img.sections:
  first=b&~4095;m.mem_map(first,((b+size+4095)&~4095)-first);m.mem_write(b,img.data[raw:raw+n])
 base,boss,manager,code,stack,end=0x70000000,0x70008000,0x70010000,0x70020000,0x7003f000,0x7003e000;m.mem_map(base,0x40000)
 put=lambda p,v:m.mem_write(p,struct.pack('<I',v&0xffffffff))
 get=lambda p:struct.unpack('<I',m.mem_read(p,4))[0]
 bits=lambda f:struct.unpack('<I',struct.pack('<f',f))[0]
 def ins(op,args,refs=0,time=0):return struct.pack('<iHHHBBI',time,op,16+4*len(args),refs,255,len(args),0)+struct.pack('<'+'I'*len(args),*[v&0xffffffff for v in args])
 own=[base+0x147c+j*4 for j in range(12)]+[base+o for o in (0x1278,0x127c,0x12bc,0x12c0)]
 other=[boss+0x147c+j*4 for j in range(8)]
 shared=[manager+0x10+j*4 for j in range(3)]+[manager+0x2c+j*4 for j in range(12)]
 addresses=own+other+shared;initial=[j+11 for j in range(len(addresses))];rows=[]
 ids=[(i,0) for i in (*range(-9926,-9922),*range(-9943,-9939))]+[(i,1) for i in (*range(-9922,-9914),*range(-9939,-9935),*range(-9995,-9991))]
 for id,floating in ids:
  values=[bits(v) for v in (-123.25,-0.,0.,123.25,16777216.)]+[0x7fc01234,0x7f800000,0xff800000] if floating else [0,1,0xffffffff,16777217,0x80000000,0x7fffffff]
  for present in (0,1):
   for value in values:
    m.mem_write(base,bytes(0x3d000));put(base,0x4bde7c);put(0x4db544,manager);put(manager+0x5c,boss if present else 0)
    for p,v in zip(addresses,initial):put(p,v)
    payload=ins(44 if floating else 42,[value])+ins(45 if floating else 43,[bits(id) if floating else id],1)+ins(42,[id],1)+ins(44,[bits(id)],1)+ins(0,[],time=2147483647)
    m.mem_write(code,payload);context=base+8;put(context+4,code);put(context+0x1014,base);put(context+0x101c,255);put(stack,end)
    m.reg_write(UC_X86_REG_ECX,context);m.reg_write(UC_X86_REG_ESP,stack);m.reg_write(UC_X86_REG_XMM1,0);m.reg_write(UC_X86_REG_MXCSR,0x1f80);m.reg_write(UC_X86_REG_FPCW,0x37f);m.reg_write(UC_X86_REG_FPSW,0);m.reg_write(UC_X86_REG_FPTAG,0xffff)
    m.emu_start(0x482380,end,count=20000);assert m.reg_read(UC_X86_REG_EIP)==end and get(context+0x1008)==16
    rows.append(dict(id=id,floating=floating,present=present,value=value,code=payload.hex(),storage=[get(p) for p in addresses],reads=[get(context+12),get(context+20)]))
 flag_reads=[]
 for id,flags in ((id,flags) for id in (-9906,-9986) for flags in (0,0xffffffff,0x180000,*(1<<j for j in range(32)))):
  m.mem_write(base,bytes(0x3d000));put(base,0x4bde7c);put(base+0x5244,flags)
  payload=ins(42,[id],1)+ins(44,[bits(id)],1)+ins(0,[],time=2147483647)
  m.mem_write(code,payload);context=base+8;put(context+4,code);put(context+0x1014,base);put(context+0x101c,255);put(stack,end)
  m.reg_write(UC_X86_REG_ECX,context);m.reg_write(UC_X86_REG_ESP,stack);m.reg_write(UC_X86_REG_XMM1,0);m.reg_write(UC_X86_REG_FPCW,0x37f);m.reg_write(UC_X86_REG_FPSW,0);m.reg_write(UC_X86_REG_FPTAG,0xffff)
  m.emu_start(0x482380,end,count=20000);assert m.reg_read(UC_X86_REG_EIP)==end
  flag_reads.append(dict(id=id,flags=flags,code=payload.hex(),reads=[get(context+12),get(context+20)]))
 random_reads=[]
 for id in (-10000,-9999,-9998,-9987):
  for floating in (0,1):
   for seed in (*[(n*251)&65535 for n in range(512)],48997,65535):
    m.mem_write(base,bytes(0x3d000));put(base,0x4bde7c);put(0x4db510,seed);put(0x4db514,0)
    payload=ins(44 if floating else 42,[bits(id) if floating else id],1)+ins(0,[],time=2147483647)
    m.mem_write(code,payload);context=base+8;put(context+4,code);put(context+0x1014,base);put(context+0x101c,255);put(stack,end)
    m.reg_write(UC_X86_REG_ECX,context);m.reg_write(UC_X86_REG_ESP,stack);m.reg_write(UC_X86_REG_XMM1,0);m.reg_write(UC_X86_REG_MXCSR,0x1f80);m.reg_write(UC_X86_REG_FPCW,0x37f);m.reg_write(UC_X86_REG_FPSW,0);m.reg_write(UC_X86_REG_FPTAG,0xffff)
    m.emu_start(0x482380,end,count=20000);assert m.reg_read(UC_X86_REG_EIP)==end
    random_reads.append(dict(id=id,floating=floating,seed=seed,code=payload.hex(),result=[get(context+12),get(0x4db510)&65535,get(0x4db514)]))
 out=ROOT/'artifacts/th14/ecl-globals-native.json';out.write_text(json.dumps(dict(executableSha256=hashlib.sha256(img.data).hexdigest(),initial=initial,cases=rows,flagReads=flag_reads,randomReads=random_reads))+'\n',encoding='utf8');print(f'{len(rows)} retail global reference write/read cases / {len(flag_reads)} flags / {len(random_reads)} RNG reads.')
if __name__=='__main__':main()
