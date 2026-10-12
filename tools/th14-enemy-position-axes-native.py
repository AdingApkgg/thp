"""Retail 434..439 per-axis and relative-offset position interpolation."""
import hashlib,importlib,itertools,json,struct
from pathlib import Path
from unicorn import Uc,UC_ARCH_X86,UC_MODE_32,UC_HOOK_CODE
from unicorn.x86_const import *
ROOT=Path(__file__).resolve().parents[1]
def main():
 img,_,_=importlib.import_module('th-anm-handlers').handlers(14);m=Uc(UC_ARCH_X86,UC_MODE_32)
 for _,base,size,raw,n in img.sections:
  start=base&~4095;m.mem_map(start,((base+size+4095)&~4095)-start);m.mem_write(base,img.data[raw:raw+n])
 base,owner,code,stack,end=0x70001000,0x70007000,0x70008000,0x7000f000,0x70000000;m.mem_map(end,0x10000)
 def put(p,v):m.mem_write(p,struct.pack('<I',v&0xffffffff))
 def get(p):return struct.unpack('<I',m.mem_read(p,4))[0]
 def floats(p,*v):m.mem_write(p,struct.pack('<'+'f'*len(v),*v))
 f32=lambda f:struct.unpack('<I',struct.pack('<f',f))[0]
 fields=(0,4,8,0x34,0x38,0x3c,0x18,0x1c,0x20,0x24,0x28,0x2c,0x40);args=[]
 def boundary(machine,address,size,user):
  if address==0x47f0a0:m.reg_write(UC_X86_REG_EAX,0)
  else:m.reg_write(UC_X86_REG_EAX if address in (0x483f30,0x42c1d0) else UC_X86_REG_XMM0,args[get(m.reg_read(UC_X86_REG_ESP)+4)])
 for address in (0x47f0a0,0x483fc0,0x483f30,0x42c1d0,0x42c230):
  m.mem_write(address,b'\xc2\x04\x00');m.hook_add(UC_HOOK_CODE,boundary,begin=address,end=address)
 def movement():return [get(base+offset+field) for offset in (0,0x44,0x88,0xcc) for field in fields]+[get(base+0x4054)]
 def position():return [[int(get(base+off+f)!=0) if f==0x48 else get(base+off+f) for f in (*range(0xc,0x3c,4),0x3c,0x40,0x44,0x48,0x4c,0x50,0x60)] for off in (0x2f8,0x360)]
 def axis():return [[get(base+off+f) for f in (0x54,0x58,0x5c,0x64)] for off in (0x2f8,0x360)]
 def state():return dict(result=movement(),position=position(),axis=axis())
 rows=[]
 for op,mode,variant in itertools.product((401,403,425,426,427,*range(434,440)),(*range(32),-1,80),range(12)):
  m.reg_write(UC_X86_REG_FPCW,0x37f);m.reg_write(UC_X86_REG_FPSW,0);m.reg_write(UC_X86_REG_FPTAG,0xffff);m.reg_write(UC_X86_REG_MXCSR,0x1f80)
  m.mem_write(base,bytes(0x8000));put(base+0x40ec,owner);put(owner+4,owner+0x100);put(base+0x4054,(0,0x80000,0x20000,0x4020000)[variant%4])
  for k,offset in enumerate((0,0x44,0x88,0xcc)):
   values=[-32.125+k*3.25,48.5-k*7.5,3.75+k,-.5+k*.25,.625-k*.125,.03125*(k+1),.5+k*.25,-.125+k*.0625,1,2,3,4]
   for field,value in zip(fields,values):floats(base+offset+field,value)
   put(base+offset+0x40,0 if k<2 else (0,2,3,4)[variant%4])
  floats(base+0x3f60,10,100,25,35);floats(base+0x3f58,16,24);floats(0x4d9294,.125,-.25,.5)
  rate=(.5,1.,1.25)[variant%3];floats(0x4d8f58,rate)
  for k,offset in enumerate((0x2f8,0x360)):
   floats(base+offset+0xc,1.25,-2.5,3.75);floats(base+offset+0x18,-4.5,5.25,-6.75)
   put(base+offset+0x3c,0xffffffff);put(base+offset+0x48,0x4d8f58);put(base+offset+0x4c,1);put(base+offset+0x50,3)
   put(base+offset+0x60,(0,7,17,8)[variant%4]);put(base+offset+0x54,mode);put(base+offset+0x58,(mode*7+5)%32);put(base+offset+0x5c,(0,7,17,31)[variant%4]);put(base+offset+0x64,0xabc00001)
  initial=state();separate=op in (434,435,438,439)
  args[:]=[(0,-1,7,35)[variant//3]&0xffffffff,mode&0xffffffff]
  if separate:args.append(((mode*7+5)%32 if mode>=0 and mode<32 else mode)&0xffffffff)
  args.extend([f32((-999999.,-1000000.,-80.,24.5)[variant%4]),f32((100.,-999999.,0.,72.125)[variant%4])])
  if op in (425,426,427):args[:]=[args[0],f32(1.25),f32(-2.5),args[2],args[3],f32(-3.75),f32(.625)]
  m.reg_write(UC_X86_REG_ESP,stack);m.reg_write(UC_X86_REG_EDI,base);m.reg_write(UC_X86_REG_EDX,owner);m.reg_write(UC_X86_REG_ECX,op);m.reg_write(UC_X86_REG_ESI,code);put(code+4,op)
  m.emu_start(0x4261c6 if op in (425,426,427) else 0x425eb6 if op in (401,403,436,437) else 0x426076,0x429c28,count=100000);assert m.reg_read(UC_X86_REG_EIP)==0x429c28
  configured=state();frames=[]
  for frame in range(76):
   put(base+0x4054,get(base+0x4054)|0x40000);put(stack,end);m.reg_write(UC_X86_REG_ESP,stack);m.reg_write(UC_X86_REG_ECX,base)
   m.emu_start(0x4230d0,end,count=100000);assert m.reg_read(UC_X86_REG_EIP)==end
   status=m.reg_read(UC_X86_REG_EAX);frames.append(dict(**state(),status=status));put(base+0x4054,get(base+0x4054)&~0x40000)
   if status:break
  rows.append(dict(op=op,mode=mode,variant=variant,rate=rate,initial=initial,args=args[:],configured=configured,frames=frames))
 output=ROOT/'artifacts/th14/enemy-position-axes-native.json';output.write_text(json.dumps(dict(executableSha256=hashlib.sha256(img.data).hexdigest(),rows=rows)),encoding='utf-8');print(f'native position axes: {len(rows)} timelines / {sum(len(r["frames"]) for r in rows)} frames')
if __name__=='__main__':main()
