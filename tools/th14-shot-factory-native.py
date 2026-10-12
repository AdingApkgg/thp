"""Full retail 4508f0 factory, actual movement and damage-area allocation.
ANM binding/update/registry, heap memset and audio are controlled boundaries.
"""
import hashlib,importlib,itertools,json,struct
from pathlib import Path
from unicorn import Uc,UC_ARCH_X86,UC_MODE_32,UC_HOOK_CODE
from unicorn.x86_const import *
ROOT=Path(__file__).resolve().parents[1]
def main():
 im,*_=importlib.import_module('th-anm-handlers').handlers(14);m=Uc(UC_ARCH_X86,UC_MODE_32)
 for _,b,size,raw,n in im.sections:
  s=b&~4095;m.mem_map(s,((b+size+4095)&~4095)-s);m.mem_write(b,im.data[raw:raw+n])
 end,obj,spec,player,vm,file,origin,stack=0x70000000,0x70001000,0x70002000,0x70010000,0x70040000,0x70042000,0x70043000,0x700ff000;m.mem_map(end,0x100000)
 put=lambda p,v:m.mem_write(p,struct.pack('<I',v&0xffffffff));get=lambda p:struct.unpack('<I',m.mem_read(p,4))[0]
 floats=lambda p,*v:m.mem_write(p,struct.pack('<'+'f'*len(v),*v));created=[];angle_hint=False
 def boundary(machine,a,size,user):
  sp=m.reg_read(UC_X86_REG_ESP)
  if a==0x48f980:m.mem_write(get(sp+4),bytes(get(sp+12)));m.reg_write(UC_X86_REG_EAX,get(sp+4))
  elif a==0x47fcb0:m.reg_write(UC_X86_REG_EAX,vm)
  elif a==0x40af00:created.append(get(sp+8));put(vm+0x18,6);put(vm+0x1c,0x40 if angle_hint else 0)
  elif a==0x47e890:put(get(sp+4),73);m.reg_write(UC_X86_REG_EAX,get(sp+4))
  elif a==0x47f0a0:m.reg_write(UC_X86_REG_EAX,vm)
 for a,n in ((0x48f980,0),(0x47fcb0,0),(0x40af00,8),(0x46fe50,0),(0x47e890,8),(0x47f0a0,4),(0x4854a0,0)):
  m.mem_write(a,b'\xc2'+struct.pack('<H',n)if n else b'\xc3');m.hook_add(UC_HOOK_CODE,boundary,begin=a,end=a)
 rows=[]
 for option,angle,kind,flags,focus,rate,seed in itertools.product((0,1,8),(-3.,.37,995.,1000.),(0,2,3),(0,0x3c,0xff),(0,1),(.5,1.,1.25),(0,65535)):
  m.mem_write(end,bytes(0xf0000));created.clear();angle_hint=bool(flags&1);timer_flags=0x80|(flags&1)
  for p,v in ((0x4db67c,player),(player+0x10,file),(player+0x184b0,focus),(obj+0x10,flags),(obj+0x28,timer_flags),(obj+0x24,0x4d8f58),(0x4f5858,120),(0x4f5860,40),(0x4db508,54321),(0x4db50c,77),(0x4db510,seed),(0x4db514,123)):put(p,v)
  floats(0x4d8f58,rate);floats(origin,-12.25,400.125,3);m.mem_write(0x4f5815,b'\0')
  # Poison old motion; the retail 0x44-byte memset must clear it before use.
  m.mem_write(obj+0x54,bytes([0xa5])*0x44)
  m.mem_write(spec+2,struct.pack('<h',19));floats(spec+4,.37,-.51,24,40,angle,8.125)
  m.mem_write(spec+0x20,struct.pack('<bbhhh',option,kind,1,0,-1))
  ox,oy=(2147483647,-2147483648)if option==8 else(1397,40291);oa=-3.2 if option==8 else .37
  put(player+option*0xe4+0xd664,ox);put(player+option*0xe4+0xd668,oy);floats(player+option*0xe4+0xd6b0,oa)
  put(stack,end);put(stack+4,spec);put(stack+8,7);put(stack+12,origin);m.reg_write(UC_X86_REG_ESP,stack);m.reg_write(UC_X86_REG_ECX,obj);m.reg_write(UC_X86_REG_MXCSR,0x1f80);m.reg_write(UC_X86_REG_FPCW,0x37f);m.reg_write(UC_X86_REG_FPSW,0);m.reg_write(UC_X86_REG_FPTAG,0xffff)
  m.emu_start(0x4508f0,end,count=100000);assert m.reg_read(UC_X86_REG_EIP)==end and m.reg_read(UC_X86_REG_EAX)==0
  a=get(obj+0xc0);result=[get(obj+n)for n in (0x98,0x10,0x18,0x1c,0x20,0x28,0x54,0x58,0x5c,0x6c,0x70,0x88,0x8c,0x90,0xac,0xb0,0xb4)]+[get(vm+n)for n in (0x18,0x1c,0x50,0x59c,0x5a0,0x5a4,0x24)]+[get(a+n)for n in (0x10,0x1c,0x24,0x28,0x2c,0x30,0x34,0x70,0x74,0x78,0x90,0x8c,0x84)]+[int(get(a+0xa0)==0x451760),get(player+0x1834c)if kind==2 else 0,get(player+0x18348+option*4)if kind==3 else 0,get(0x4db508)&65535,get(0x4db50c),get(0x4db510)&65535,get(0x4db514)]
  rows.append(dict(args=[option,angle,kind,flags,focus,rate,seed,ox,oy,oa],result=result,created=created[:]))
 gates=[];sht=0x70050000;head=player+0xd6c8
 for kind,option,cached,focus,power,frame,available in itertools.product((0,2,3),(0,1,8),(0,1,-1,4),(0,1),(0,40,120,160),range(6),(0,1)):
  m.mem_write(end,bytes(0xf0000));created.clear();angle_hint=False
  for p,v in ((0x4db67c,player),(player+0x10,file),(player+0x184b0,focus),(player+0x688,sht),(sht+0x20,4),(head+4,obj if available else 0),(obj+8,head),(0x4f5858,power),(0x4f5860,40),(0x4db508,54321),(0x4db50c,77),(0x4db510,0),(0x4db514,123),(player+0x1834c,cached)):put(p,v)
  if kind==3:put(player+0x18348+option*4,cached)
  for n in range(10):put(sht+0xe0+n*4,spec)
  floats(0x4d8f58,1);floats(player+0x5e0,-12.25,400.125,3);m.mem_write(0x4f5815,b'\0')
  m.mem_write(spec,struct.pack('<bbh',3,1,19));floats(spec+4,.37,-.51,24,40,-3,8.125);m.mem_write(spec+0x20,struct.pack('<bbhhh',option,kind,1,0,-1));m.mem_write(spec+0x58,b'\xff')
  put(player+option*0xe4+0xd664,1397);put(player+option*0xe4+0xd668,40291);floats(player+option*0xe4+0xd6b0,.37)
  put(stack,end);put(stack+4,frame);m.reg_write(UC_X86_REG_ESP,stack);m.reg_write(UC_X86_REG_ECX,player);m.reg_write(UC_X86_REG_MXCSR,0x1f80);m.reg_write(UC_X86_REG_FPCW,0x37f);m.reg_write(UC_X86_REG_FPSW,0);m.reg_write(UC_X86_REG_FPTAG,0xffff)
  m.emu_start(0x450ed0,end,count=100000);assert m.reg_read(UC_X86_REG_EIP)==end
  gates.append(dict(args=[kind,option,cached,focus,power,frame,available],result=[len(created),get(player+0x1834c)if kind==2 else 0,get(player+0x18348+option*4)if kind==3 else 0]))
 (ROOT/'artifacts/th14/shot-factory-native.json').write_text(json.dumps(dict(executableSha256=hashlib.sha256(im.data).hexdigest(),rows=rows,gates=gates),indent=2)+'\n',encoding='utf8');print(f'{len(rows)} retail common shot allocations, {len(gates)} firing gates.')
if __name__=='__main__':main()
