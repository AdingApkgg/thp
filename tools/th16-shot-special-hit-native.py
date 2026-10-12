"""Complete446870 and447320. Original geometry, trig, RNG, interpolation and default hit execute."""
import hashlib,importlib,json,struct
from pathlib import Path
from unicorn import *
from unicorn.x86_const import *
ROOT=Path(__file__).resolve().parents[1]
def main():
 img,_,_=importlib.import_module('th-anm-handlers').handlers(16);m=Uc(UC_ARCH_X86,UC_MODE_32)
 for _,base,size,raw,n in img.sections:
  start=base&~4095;m.mem_map(start,((base+size+4095)&~4095)-start);m.mem_write(base,img.data[raw:raw+n])
 ret,player,shot,vm,effect,target,size,bmanager,stack=0x70000000,0x70001000,0x70050000,0x70060000,0x70061000,0x70062000,0x70062100,0x70070000,0x700ff000;m.mem_map(ret,0x100000)
 put=lambda p,v:m.mem_write(p,struct.pack('<I',v&0xffffffff));get=lambda p:struct.unpack('<I',m.mem_read(p,4))[0];bits=lambda v:struct.unpack('<I',struct.pack('<f',v))[0];rows=[];events=[]
 put(0x4a6ef8,player);put(0x4a6db8,bmanager);put(player+0xc,1);put(player+0x10,2);put(bmanager+0xc,3);m.mem_write(0x4d9dc4,bytes(12));m.mem_write(0x4c10b6,b'\0')
 def finish(pop,value):
  sp=m.reg_read(UC_X86_REG_ESP);m.reg_write(UC_X86_REG_EAX,value&0xffffffff);m.reg_write(UC_X86_REG_ESP,sp+4+pop);m.reg_write(UC_X86_REG_EIP,get(sp))
 def hook(uc,address,length,data):
  sp=m.reg_read(UC_X86_REG_ESP)
  if address==0x46f0b0:events.append([0,get(sp+4),get(sp+8)]);finish(8,0)
  elif address==0x40e5c0:
   out,script,pos,rotation,layer,last=[get(sp+i) for i in (4,8,12,16,20,24)];events.append([1,m.reg_read(UC_X86_REG_ECX),script,*[get(pos+k) for k in (0,4,8)],rotation,layer]);put(out,88);finish(24,out)
  elif address==0x40e6c0:finish(0,-1)
  elif address==0x46efa0:finish(4,effect if get(sp+4)==88 else vm)
  elif address==0x47499b:finish(0,m.reg_read(UC_X86_REG_EAX))
 m.hook_add(UC_HOOK_CODE,hook)
 for kind,count in ((0,4096),(1,1024)):
  for seed in range(count):
   events=[];m.mem_write(shot,bytes(0xc0));m.mem_write(vm,bytes(0x600));m.mem_write(effect,bytes(0x600));area=player+0xd080+2*0x94;m.mem_write(area,bytes(0x94))
   angle=(0.,-.75,-1.5707963705062866,3.1415927410125732)[(seed//8)%4];age=(-4,-1,0,1,2,4,8,9)[seed%8];height=(4.,8.,16.,32.)[(seed//32)%4]
   x=(-100.,-20.,0.,20.,100.,250.,-2.,2.)[(seed//128)%8];y=(-40.,-8.,0.,8.)[(seed//1024)%4]
   put(shot+8,77);put(shot+0xb0,2);put(shot+0x8c,1);put(shot+0x9c,13);put(shot+0xac,0x10000 if seed&1 else 0);put(shot+0xc,age if seed&2 else age-1);put(shot+0x10,age);put(shot+0x98,int(bool(seed&4)));put(shot+0x60,bits(16));put(shot+0x64,bits(angle));m.mem_write(shot+0x48,struct.pack('<fff',7.25,300.5,1.25));put(area,7);put(area+0x18,bits(height));put(area+0x74,13);put(vm+0x490,7);put(effect+0x520,0xaabbccdd);put(effect+0x530,0x100)
   m.mem_write(target,struct.pack('<fff',7.25+x,300.5+y,0));m.mem_write(size,struct.pack('<ff',24,40));put(0x4a6d80,(seed*997+17)&65535);put(0x4a6d84,9)
   put(stack,ret);put(stack+4,size if seed&64 else 0);put(stack+8,bits((0.,.5,-1.25)[(seed//256)%3]));put(stack+12,bits((0.,4.,16.)[(seed//64)%3]));m.reg_write(UC_X86_REG_ESP,stack);m.reg_write(UC_X86_REG_ECX,shot);m.reg_write(UC_X86_REG_EDX,target);m.reg_write(UC_X86_REG_MXCSR,0x1f80);m.reg_write(UC_X86_REG_FPCW,0x37f);m.reg_write(UC_X86_REG_FPSW,0);m.reg_write(UC_X86_REG_FPTAG,0xffff)
   m.emu_start(0x447320 if kind else 0x446870,ret,count=500000);assert m.reg_read(UC_X86_REG_EIP)==ret
   output=[m.reg_read(UC_X86_REG_EAX)]+[get(shot+k) for k in (0x94,0x98,0xa0)]+[get(area+0x14)] if not kind else [m.reg_read(UC_X86_REG_EAX),get(0x4a6d80),get(0x4a6d84)]+[get(effect+k) for k in (0x520,0x230,0x234,0x1f4,0x1f8,0x1fc,0x200,0x21c,0x220,0x224)]+[get(shot+k) for k in (0x8c,0xb0,0x50,0x60)]+[get(area),get(vm+0x490)]
   interp=[get(effect+k) for k in (0x530,0x40,0xdc,0xe0,0x8c,0x90,0x94,0x98,0x9c,0xa0,0xa4,0xa8,0xac,0xb0,0xb4,0xb8,0xc8,0xcc,0xd0)] if not kind and len(events)>int(not bool(seed&4)) else []
   rows.append(dict(kind=kind,seed=seed,output=output,events=events,interp=interp))
 (ROOT/'artifacts/th16/shot-special-hit-native.json').write_text(json.dumps(dict(executableSha256=hashlib.sha256(img.data).hexdigest(),rows=rows),separators=(',',':'))+'\n',encoding='utf8');print(f'{len(rows)} native TH16 special shot hits')
if __name__=='__main__':main()


