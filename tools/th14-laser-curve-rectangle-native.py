"""Actual 442a00 rectangle selection, timer/length changes and inherited fragments."""
import hashlib,importlib,itertools,json,struct
from pathlib import Path
from unicorn import Uc,UC_ARCH_X86,UC_MODE_32,UC_HOOK_CODE
from unicorn.x86_const import *
ROOT=Path(__file__).resolve().parents[1]
def main():
 img,_,_=importlib.import_module('th-anm-handlers').handlers(14);m=Uc(UC_ARCH_X86,UC_MODE_32)
 for _,b,size,raw,n in img.sections:
  begin=b&~4095;m.mem_map(begin,((b+size+4095)&~4095)-begin);m.mem_write(b,img.data[raw:raw+n])
 end,obj,samples,center,sizep,manager,child,heap,stack=0x70000000,0x70001000,0x70004000,0x70007000,0x70008000,0x70009000,0x7000a000,0x7000c000,0x7001f000;m.mem_map(end,0x1000000)
 put=lambda p,v:m.mem_write(p,struct.pack('<I',v&0xffffffff));get=lambda p:struct.unpack('<I',m.mem_read(p,4))[0]
 words=lambda p,n:list(struct.unpack('<'+'I'*n,m.mem_read(p,n*4)))
 bits=lambda f:struct.unpack('<I',struct.pack('<f',f))[0]
 rewards=[];effects=[];fragments=[]
 def boundary(machine,a,size,user):
  sp=m.reg_read(UC_X86_REG_ESP)
  if a==0x41ae00:rewards.append([m.reg_read(UC_X86_REG_EDX),*words(m.reg_read(UC_X86_REG_ECX),3)])
  elif a==0x47ed10:effects.append([get(sp+8),*words(get(sp+12),3)]);put(get(sp+4),1)
  elif a==0x47f0a0:m.reg_write(UC_X86_REG_EAX,0)
  elif a==0x485540:m.reg_write(UC_X86_REG_EAX,heap)
  elif a==0x4854af:m.reg_write(UC_X86_REG_EAX,child)
  elif a==0x43a980:put(child,0x4be2fc);m.reg_write(UC_X86_REG_EAX,child)
  elif a==0x4401d0:
   row=words(get(sp+4),213);assert row[0x34c//4]==obj+0x14b4;row[0x34c//4]=1;fragments.append(row)
  elif a==0x48f980:m.mem_write(get(sp+4),bytes(get(sp+12)))
 for a,cleanup in ((0x41ae00,0),(0x47ed10,28),(0x47f0a0,4),(0x485540,0),(0x4854af,0),(0x43a980,0),(0x4401d0,4),(0x48f980,0),(0x4855d2,0),(0x4854a0,0)):
  m.mem_write(a,b'\xc2'+struct.pack('<H',cleanup) if cleanup else b'\xc3');m.hook_add(UC_HOOK_CODE,boundary,begin=a,end=a)
 put(0x4db530,end+0x20000);put(0x4db664,manager);rows=[]
 patterns=('000000000000','111111111111','111000000000','000000001111','000011110000','010101010101','101010101010','011100100010','000001000000','100011100000')
 for pattern,angle,dimension,rate,(skip,protection) in itertools.product(patterns,(0.,.125,1.5707963705062866,-3.1415927410125732),((8.,16.),(0.,0.),(-8.,16.)),(.5,1.,1.25),((0,0),(1,0),(0,1),(1,1))):
  rewards.clear();effects.clear();fragments.clear();m.mem_write(obj,bytes(0x2000));m.mem_write(manager,bytes(0x1000));put(manager+0x5d0,manager+0x800);put(obj+0x14ac,samples);put(obj+0x5b4,protection)
  request=[0]*213;request[0:6]=list(map(bits,(12.25,80.5,3.5,.125,16.,4.)));request[8]=len(pattern);request[7]=14;request[0x344//4]=17;request[0x350//4]=bits(30.5);m.mem_write(obj+0x5c0,struct.pack('<213I',*request))
  put(obj+0x40,29);put(obj+0x44,30);put(obj+0x48,bits(30.5));put(obj+0x4c,0x4d8f58);put(0x4d8f58,bits(rate));initial=[]
  for j,c in enumerate(pattern):
   row=list(map(bits,(12.25+(0 if c=='1' else 50),80.5,j*.125,j*.25,-j*.125,3.5,j*.0625,4+j*.25)));initial.append(row);m.mem_write(samples+j*32,struct.pack('<8I',*row))
  position=list(map(bits,(12.25,80.5,0)));dimensions=list(map(bits,dimension));m.mem_write(center,struct.pack('<3I',*position));m.mem_write(sizep,struct.pack('<2I',*dimensions));put(stack,end)
  for j,v in enumerate((center,sizep,bits(angle),1,skip)):put(stack+4+j*4,v)
  m.reg_write(UC_X86_REG_ESP,stack);m.reg_write(UC_X86_REG_ECX,obj);m.reg_write(UC_X86_REG_FPCW,0x37f);m.reg_write(UC_X86_REG_FPSW,0);m.reg_write(UC_X86_REG_FPTAG,0xffff);m.reg_write(UC_X86_REG_MXCSR,0x1f80)
  m.emu_start(0x442a00,end,count=100000);assert m.reg_read(UC_X86_REG_EIP)==end
  rows.append(dict(initial=initial,request=request,center=position,size=dimensions,angle=bits(angle),rate=rate,skip=skip,protection=protection,count=m.reg_read(UC_X86_REG_EAX),flags=get(obj+0xc),timer=words(obj+0x40,3),samples=[words(samples+j*32,8) for j in range(get(obj+0x5e0))],rewards=rewards[:],effects=effects[:],fragments=fragments[:]))
 (ROOT/'artifacts/th14/laser-curve-rectangle-native.json').write_text(json.dumps(dict(executableSha256=hashlib.sha256(img.data).hexdigest(),cases=rows),indent=2)+'\n',encoding='utf8');print(f'{len(rows)} native curve rectangle cuts.')
if __name__=='__main__':main()
