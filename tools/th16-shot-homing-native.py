"""Full445ee0 with original atan2, angle folding and angle setters."""
import hashlib,importlib,itertools,json,struct
from pathlib import Path
from unicorn import *
from unicorn.x86_const import *
ROOT=Path(__file__).resolve().parents[1]
def main():
 img,_,_=importlib.import_module('th-anm-handlers').handlers(16);m=Uc(UC_ARCH_X86,UC_MODE_32)
 for _,base,size,raw,n in img.sections:
  start=base&~4095;m.mem_map(start,((base+size+4095)&~4095)-start);m.mem_write(base,img.data[raw:raw+n])
 ret,shot,enemy,stack=0x70000000,0x70001000,0x70010000,0x700ff000;m.mem_map(ret,0x100000)
 put=lambda p,v:m.mem_write(p,struct.pack('<I',v&0xffffffff));get=lambda p:struct.unpack('<I',m.mem_read(p,4))[0]
 bits=lambda v:struct.unpack('<I',struct.pack('<f',v))[0];rows=[];events=[];mode=0
 def finish(pop,result):
  sp=m.reg_read(UC_X86_REG_ESP);m.reg_write(UC_X86_REG_EAX,result);m.reg_write(UC_X86_REG_ESP,sp+4+pop);m.reg_write(UC_X86_REG_EIP,get(sp))
 def hook(uc,address,size,data):
  sp=m.reg_read(UC_X86_REG_ESP)
  if address==0x425240:
   out,pos=get(sp+4),get(sp+8);assert list(struct.unpack('<fff',m.mem_read(pos,12)))==[7.25,300.5,1.25];radius=m.reg_read(UC_X86_REG_XMM3)&0xffffffff;events.append([1,radius]);put(out,0 if mode==1 else 7);finish(8,out)
  elif address==0x41a980:events.append([2,get(sp+4)]);finish(4,int(mode!=3))
  elif address==0x41b540:events.append([3,get(m.reg_read(UC_X86_REG_ECX))]);finish(0,enemy)
 m.hook_add(UC_HOOK_CODE,hook)
 for state,target,age,speed,angle,point,mode,flags in itertools.product((1,2),(0,7),(0,59,60),(3.9,6.,15.9),(-7.,-3.,-.75,0.,3.),((7.25,300.5),(100.,100.),(-100.,400.)),range(5),(0,1,0x2000000)):
  events=[];m.mem_write(shot,bytes(0xc0));put(shot+0x8c,state);put(shot+0x90,target);put(shot+0x10,age);m.mem_write(shot+0x48,struct.pack('<fff',7.25,300.5,1.25));put(shot+0x60,bits(speed));put(shot+0x64,bits(angle));m.mem_write(enemy+0x1250,struct.pack('<ff',*point));put(enemy+0x526c,flags);put(0x4a6dc0,0 if mode==0 else enemy)
  put(stack,ret);m.reg_write(UC_X86_REG_ESP,stack);m.reg_write(UC_X86_REG_ECX,shot);m.reg_write(UC_X86_REG_MXCSR,0x1f80);m.reg_write(UC_X86_REG_FPCW,0x37f);m.reg_write(UC_X86_REG_FPSW,0);m.reg_write(UC_X86_REG_FPTAG,0xffff);m.emu_start(0x445ee0,ret,count=100000);assert m.reg_read(UC_X86_REG_EIP)==ret
  rows.append(dict(state=state,target=target,age=age,speed=speed,angle=angle,point=point,mode=mode,flags=flags,output=[get(shot+k) for k in (0x90,0x60,0x64)],events=events))
 (ROOT/'artifacts/th16/shot-homing-native.json').write_text(json.dumps(dict(executableSha256=hashlib.sha256(img.data).hexdigest(),rows=rows),separators=(',',':'))+'\n',encoding='utf8');print(f'{len(rows)} native TH16 homing callbacks')
if __name__=='__main__':main()
