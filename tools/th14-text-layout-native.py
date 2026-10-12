"""Whole retail text wrappers; formatting and downstream raster delivery controlled."""
import hashlib,importlib,itertools,json,struct
from pathlib import Path
from unicorn import Uc,UC_ARCH_X86,UC_MODE_32,UC_HOOK_CODE
from unicorn.x86_const import *
ROOT=Path(__file__).resolve().parents[1]
def main():
 img,*_=importlib.import_module('th-anm-handlers').handlers(14);m=Uc(UC_ARCH_X86,UC_MODE_32)
 for _,b,size,raw,n in img.sections:
  start=b&~4095;m.mem_map(start,((b+size+4095)&~4095)-start);m.mem_write(b,img.data[raw:raw+n])
 arena=0x70000000;m.mem_map(arena,0x20000);vm=arena+0x1000;sprite=arena+0x2000;surface=arena+0x3000;stack=arena+0x1f000;payload=b'';deliveries=[]
 def put(p,v):m.mem_write(p,struct.pack('<I',v&0xffffffff))
 def get(p):return struct.unpack('<I',m.mem_read(p,4))[0]
 def hook(uc,a,n,u):
  sp=uc.reg_read(UC_X86_REG_ESP);pop=0
  if a==0x4859cd:m.mem_write(get(sp+4),payload+b'\0');uc.reg_write(UC_X86_REG_EAX,len(payload))
  elif a==0x467ba0:
   args=[get(sp+i*4) for i in range(1,9)];deliveries.append(dict(height=args[0],color=args[1],outline=args[2],font=args[5],spacing=args[6],shadow=args[7],offset=uc.reg_read(UC_X86_REG_EDX)));pop=32
  uc.reg_write(UC_X86_REG_EIP,get(sp));uc.reg_write(UC_X86_REG_ESP,sp+4+pop)
 for a in (0x4859cd,0x467ba0,0x4854a0):m.hook_add(UC_HOOK_CODE,hook,begin=a,end=a)
 put(vm+0x2c,sprite);put(sprite+8,surface);put(surface,arena+0x4000)
 for i,v in enumerate((4.,3.,516.,35.)):m.mem_write(sprite+0xc+i*4,struct.pack('<f',v))
 rows=[]
 for mode,height,width,length,flags,spacing,offset in itertools.product(range(3),(0,8,9,17,40),(384.,384.5,-3.75,16777216.),(0,1,4,11,127),(0,2,0x800),(0,11,0xffffffff),(-3,7)):
  payload=b'A'*length;deliveries.clear();font=7 if length%2 else 0;m.mem_write(vm+0x528,bytes([height]));put(vm+0x1c,flags);put(vm+0x18,0xa4);m.mem_write(sprite+0x38,struct.pack('<f',width));put(stack,arena)
  args=(0,vm,0x123456,0x654321,font,offset,spacing,arena+0x5000) if mode==0 else (0,vm,0x123456,0x654321,font,spacing,arena+0x5000)
  for i,v in enumerate(args,1):put(stack+i*4,v)
  m.reg_write(UC_X86_REG_ESP,stack);m.emu_start((0x47db50,0x47dc40,0x47dd70)[mode],arena,count=10000);assert m.reg_read(UC_X86_REG_EIP)==arena;assert len(deliveries)==(0 if height==8 else 1)
  rows.append(dict(mode=mode,height=height,width=width,length=length,flags=flags,spacing=spacing,offset=offset,font=font,delivery=deliveries[0] if deliveries else None,finalFlags=get(vm+0x18)))
 (ROOT/'artifacts/th14/text-layout-native.json').write_text(json.dumps(dict(executableSha256=hashlib.sha256(img.data).hexdigest(),rows=rows,scope='Actual retail47db50/47dc40/47dd70 wrapper execution. Vararg formatting is controlled literal bytes; downstream467ba0 intercepted. Compares physical pixel coordinates, font/color/outline/spacing/shadow, height<=8 delivery skip and VM dirty flag. Excludes actual formatter/GDI/GPU.'),indent=2)+'\n',encoding='utf-8');print(f'{len(rows)} retail text wrapper cases')
if __name__=='__main__':main()
