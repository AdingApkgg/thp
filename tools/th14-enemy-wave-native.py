"""Retail 426d48 velocity setters and complete 4230d0 mode-four movement."""
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
  else:m.reg_write(UC_X86_REG_EAX if address in (0x42c1d0,0x483f30) else UC_X86_REG_XMM0,args[get(m.reg_read(UC_X86_REG_ESP)+4)])
 for address in (0x47f0a0,0x42c230,0x42c1d0,0x483fc0,0x483f30):
  m.mem_write(address,b'\xc2\x04\x00');m.hook_add(UC_HOOK_CODE,boundary,begin=address,end=address)
 def movement():return [get(base+offset+field) for offset in (0,0x44,0x88,0xcc) for field in fields]+[get(base+0x4054)]
 def wave():return [get(base+offset+field) for offset in (0x88,0xcc) for field in (0xc,0x10,0x14,0x30)]
 def scalar():return [[get(base+off+f) if f!=0x20 else int(get(base+off+f)!=0) for f in (0,4,8,12,0x14,0x18,0x1c,0x20,0x24,0x28,0x2c)] for off in (0x3c8,0x3f8,0x428,0x458)]
 def position():return [[int(get(base+off+f)!=0) if f==0x48 else get(base+off+f) for f in (*range(0xc,0x3c,4),0x3c,0x40,0x44,0x48,0x4c,0x50,0x60)] for off in (0x2f8,0x360)]
 def state():return dict(result=movement(),wave=wave(),scalar=scalar(),position=position())
 rows=[]
 for op,mode,variant,setup_kind in [(op,mode,variant,k) for op,mode,variant in itertools.product((0,418,419),range(5),range(24)) for k in (range(5) if op==0 else (0,))]:
  m.reg_write(UC_X86_REG_FPCW,0x37f);m.reg_write(UC_X86_REG_FPSW,0);m.reg_write(UC_X86_REG_FPTAG,0xffff);m.reg_write(UC_X86_REG_MXCSR,0x1f80)
  m.mem_write(base,bytes(0x8000));put(base+0x40ec,owner);put(owner+4,owner+0x100);put(base+0x4054,(0,0x80000,0x20000,0x4020000)[variant%4])
  for k,offset in enumerate((0,0x44,0x88,0xcc)):
   values=[-32.125+k*3.25,48.5-k*7.5,3.75+k,-.5+k*.25,.625-k*.125,.03125*(k+1),(-2,0,.5,1.25,4,20)[variant%6]+k*.25,-.125+k*.0625,(-4,0,.5,8,16,32)[variant%6],(-3.5,-.25,0,.75,2.5,7)[variant%6],(-3.1415927410125732,-1.25,0,.125,2.5,1000)[variant%6],1]
   for field,value in zip(fields,values):floats(base+offset+field,value)
   put(base+offset+0x40,0)
  for k,offset in enumerate((0x88,0xcc)):
   floats(base+offset+0xc,-10.25+k*3.5,80.125-k*4.5,-2.25+k)
   floats(base+offset+0x30,(-3.1415927410125732,-1.25,0,.125,2.5,1000)[(variant+k)%6])
   selected=mode if (op==0 and k==0) or (op==418 and k==0) or (op==419 and k==1) else (4 if op==0 else variant%5)
   put(base+offset+0x40,0xa0000000|selected)
  floats(base+0x3f60,10,100,25,35);floats(base+0x3f58,16,24);floats(0x4d9294,.125,-.25,.5)
  rate=(0.,.5,1.,1.25)[variant%4];floats(0x4d8f58,rate);initial=state()
  args[:]=[f32((-999999.,-1000000.,-.25,0.,1.5,16.)[variant%6]),f32((-999999.,-1000000.,0.,3.25,-2.75,16.)[(variant//4)%6]),f32(3.25),f32(.0625),f32(-.25),f32(.5)]
  setup=None
  if setup_kind:
   setup_op=(401,403,445,447)[setup_kind-1]
   saved=args[:];args[:]=[(1,7,35)[variant%3],(7,17,18,31,-1,80)[variant%6]&0xffffffff,f32((-999999.,-2.75,0.,3.5)[variant%4]),f32(72.125)]
   setup=dict(op=setup_op,args=args[:])
   saved_flags=[get(base+off+0x40) for off in (0x88,0xcc)]
   m.reg_write(UC_X86_REG_ESP,stack);m.reg_write(UC_X86_REG_EDI,base);m.reg_write(UC_X86_REG_EDX,owner);m.reg_write(UC_X86_REG_ECX,setup_op);m.reg_write(UC_X86_REG_ESI,code);put(code+4,setup_op)
   m.emu_start(0x425eb6 if setup_op in (401,403) else 0x426960,0x429c28,count=100000);assert m.reg_read(UC_X86_REG_EIP)==0x429c28
   for off,flags in zip((0x88,0xcc),saved_flags):put(base+off+0x40,flags)
   args[:]=saved
  if op:
   m.reg_write(UC_X86_REG_ESP,stack);m.reg_write(UC_X86_REG_EDI,base);m.reg_write(UC_X86_REG_EDX,owner);m.reg_write(UC_X86_REG_ECX,op);m.reg_write(UC_X86_REG_ESI,code);put(code+4,op)
   m.emu_start(0x426d48,0x429c28,count=100000);assert m.reg_read(UC_X86_REG_EIP)==0x429c28
  configured=state();frames=[]
  for frame in range(40):
   put(base+0x4054,get(base+0x4054)|0x40000);put(stack,end);m.reg_write(UC_X86_REG_ESP,stack);m.reg_write(UC_X86_REG_ECX,base)
   m.emu_start(0x4230d0,end,count=100000);assert m.reg_read(UC_X86_REG_EIP)==end
   status=m.reg_read(UC_X86_REG_EAX);frames.append(dict(**state(),status=status));put(base+0x4054,get(base+0x4054)&~0x40000)
   if status:break
  rows.append(dict(op=op,mode=mode,variant=variant,rate=rate,initial=initial,setup=setup,args=args[:],configured=configured,frames=frames))
 output=ROOT/'artifacts/th14/enemy-wave-native.json';output.write_text(json.dumps(dict(executableSha256=hashlib.sha256(img.data).hexdigest(),rows=rows)),encoding='utf-8')
 print(f'native wave: {len(rows)} timelines / {sum(len(r["frames"]) for r in rows)} frames')
if __name__=='__main__':main()
