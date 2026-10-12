"""Retail kind-2 cancellation / 43aaf0 reset through recorded ANM delivery."""
import hashlib,importlib,json,struct
from pathlib import Path
from unicorn import Uc,UC_ARCH_X86,UC_MODE_32,UC_HOOK_CODE
from unicorn.x86_const import *
ROOT=Path(__file__).resolve().parents[1]
def main():
 img,_,_=importlib.import_module('th-anm-handlers').handlers(14);m=Uc(UC_ARCH_X86,UC_MODE_32)
 for _,b,size,raw,n in img.sections:
  start=b&~4095;m.mem_map(start,((b+size+4095)&~4095)-start);m.mem_write(b,img.data[raw:raw+n])
 end,obj,samples,manager,effect,stack=0x70000000,0x70001000,0x70004000,0x70007000,0x70008000,0x7000f000;m.mem_map(end,0x1000000)
 def put(p,v):m.mem_write(p,struct.pack('<I',v&0xffffffff))
 def get(p):return struct.unpack('<I',m.mem_read(p,4))[0]
 def words(p,n):return list(struct.unpack('<'+'I'*n,m.mem_read(p,n*4)))
 def bits(f):return struct.unpack('<I',struct.pack('<f',f))[0]
 effects=[];script=0
 def boundary(machine,a,size,user):
  nonlocal script
  sp=m.reg_read(UC_X86_REG_ESP)
  if a==0x47fcb0:m.mem_write(effect,bytes(0x600));m.reg_write(UC_X86_REG_EAX,effect)
  elif a==0x40af00:assert get(sp+4)==effect;script=get(sp+8)
  elif a==0x46fe50:effects.append([script,*words(effect+0x59c,3),get(effect+0x1c),get(effect+0x50)])
  else:assert get(sp+8)==effect
 for a,cleanup in ((0x47fcb0,0),(0x40af00,8),(0x46fe50,0),(0x47e890,8)):
  m.mem_write(a,b'\xc2'+struct.pack('<H',cleanup) if cleanup else b'\xc3');m.hook_add(UC_HOOK_CODE,boundary,begin=a,end=a)
 put(0x4db530,end+0x20000);put(end+0x20000+0x9bf6cc,end+0x30000);put(0x4db664,manager);put(0x4f5815,0);rows=[]
 for count in (1,2,7,120):
  for color in (0,7,14):
   for state in (1,2,3):
    for protection in (0,3):
     for mode in (0,1,2):
      effects.clear();m.mem_write(obj,bytes(0x2000));m.mem_write(manager,bytes(0x600));m.mem_write(stack-0x2000,bytes(0x2100));put(manager+0x18,obj);put(obj,0x4be2fc);put(obj+0x10,state);put(obj+0x14,2);put(obj+0x14ac,samples);put(obj+0x5e0,count);put(obj+0x5dc,color);put(obj+0x5b4,protection);put(obj+0x5a0,6);put(obj+0x5a4,7);put(obj+0x5a8,bits(7.25));put(obj+0x5ac,0x4d8f58);put(obj+0x5b0,1)
      initial=[]
      for j in range(count):
       row=list(map(bits,(12.25+j*.75,80.5-j*.125,j*.25,0,0,0,.125,4)));initial.append(row);m.mem_write(samples+j*32,struct.pack('<8I',*row))
      put(stack,end);put(stack+4,1);put(stack+8,mode==1);m.reg_write(UC_X86_REG_ESP,stack);m.reg_write(UC_X86_REG_ECX,obj);m.reg_write(UC_X86_REG_FPCW,0x37f);m.reg_write(UC_X86_REG_FPSW,0);m.reg_write(UC_X86_REG_FPTAG,0xffff);m.reg_write(UC_X86_REG_MXCSR,0x1f80)
      m.emu_start(0x43aaf0 if mode==2 else 0x4436d0,end,count=1000000);assert m.reg_read(UC_X86_REG_EIP)==end
      rows.append(dict(initial=initial,color=color,state=state,protection=protection,mode=mode,result=[get(obj+0x10),get(obj+0x5b4),*words(obj+0x5a0,3)],effects=effects[:]))
 out=ROOT/'artifacts/th14/laser-curve-manager-native.json';out.write_text(json.dumps(dict(executableSha256=hashlib.sha256(img.data).hexdigest(),cases=rows),indent=2)+'\n',encoding='utf-8');print(f'{len(rows)} retail global curve cancellations / resets, recorded ANM requests.')
if __name__=='__main__':main()
