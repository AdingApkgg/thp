"""Full4456d0, own movement helpers and447480 execute; ANM boundaries controlled."""
import hashlib,importlib,itertools,json,struct
from pathlib import Path
from unicorn import *
from unicorn.x86_const import *
ROOT=Path(__file__).resolve().parents[1]
def main():
 img,_,_=importlib.import_module('th-anm-handlers').handlers(16);m=Uc(UC_ARCH_X86,UC_MODE_32)
 for _,base,size,raw,n in img.sections:
  start=base&~4095;m.mem_map(start,((base+size+4095)&~4095)-start);m.mem_write(base,img.data[raw:raw+n])
 ret,player,sht,vm,reject,stack=0x70000000,0x70001000,0x70040000,0x70060000,0x700e0000,0x700ff000;m.mem_map(ret,0x100000)
 put=lambda p,v:m.mem_write(p,struct.pack('<I',v&0xffffffff));get=lambda p:struct.unpack('<I',m.mem_read(p,4))[0]
 bits=lambda v:struct.unpack('<I',struct.pack('<f',v))[0];rows=[];events=[];missing=geometry=0
 put(0x4a6ef8,player);put(player+0x2c788,sht);put(sht+0x190,sht+0x200);put(0x490eb0,0x4a5788);put(0x4d9d38,32);put(0x4d9d3c,16);spec=sht+0x200
 def finish(pop,result):
  sp=m.reg_read(UC_X86_REG_ESP);m.reg_write(UC_X86_REG_EAX,result);m.reg_write(UC_X86_REG_ESP,sp+4+pop);m.reg_write(UC_X86_REG_EIP,get(sp))
 def hook(uc,address,size,data):
  sp=m.reg_read(UC_X86_REG_ESP)
  if address==reject:events.append([1,7,0,0]);finish(0,1)
  elif address==0x447480:events.append([1,5,0,0])
  elif address==0x46efa0:events.append([2,get(sp+4),0,0]);finish(4,0 if missing else vm)
  elif address==0x468c00:
   events.append([3,77,0,0]);out=get(sp+4);corners=[(100.,100.,0.) if geometry==0 else (0.,0.,0.)]*4
   if geometry==2:corners[2]=(100.,100.,0.)
   if geometry==3:corners[0]=(32.,16.,0.);corners[1]=(416.,464.,0.)
   m.mem_write(out,struct.pack('<12f',*[v for p in corners for v in p]));finish(4,out)
  elif address==0x46f1c0:events.append([4,get(sp+4),0,0]);finish(4,0)
  elif address==0x47499b:finish(0,0)
 m.hook_add(UC_HOOK_CODE,hook)
 for state,age,kind,callback,flags,flags2,missing,geometry,rate in itertools.product((1,2),(14,15),(0,2),(0,5,7),(0,1),(0,0x80),(0,1),(0,1,2,3),(0.,.5,1.,1.5)):
  events=[];m.mem_write(player+0x1110,bytes(256*0xc0));shot=player+0x1110+(255 if age==15 else 0)*0xc0
  for offset,value in ((0,flags),(8,77),(0xc,-5),(0x10,age),(0x14,bits(age+.25)),(0x18,0),(0x1c,1),(0x8c,state),(0x9c,13),(0xa0,bits(4.25)),(0xa4,bits(7.5)),(0xac,0),(0xb0,2)):put(shot+offset,value)
  m.mem_write(shot+0x48,struct.pack('<fff',7.25,300.5,1.25));put(shot+0x60,bits(6.25));put(shot+0x64,bits(-.75));m.mem_write(shot+0x7c,struct.pack('<fff',11,22,2))
  area=player+0xd080+2*0x94;m.mem_write(area,struct.pack('<37I',0xabcdef07,*[0xa5000000+i for i in range(1,37)]))
  m.mem_write(spec,bytes(0x58));m.mem_write(spec+0x21,bytes([kind]));put(spec+0x2c,{0:0,5:0x447480,7:reject}[callback]);m.mem_write(vm,bytes(0x600));put(vm+0x530,0x100);put(vm+0x534,flags2);put(vm+0x40,bits(3.25));m.mem_write(vm+0x5e0,struct.pack('<fff',11,22,33));put(0x4a5788,bits(rate))
  put(stack,ret);m.reg_write(UC_X86_REG_ESP,stack);m.reg_write(UC_X86_REG_ECX,player);m.reg_write(UC_X86_REG_MXCSR,0x1f80);m.reg_write(UC_X86_REG_FPCW,0x37f);m.reg_write(UC_X86_REG_FPSW,0);m.reg_write(UC_X86_REG_FPTAG,0xffff);m.emu_start(0x4456d0,ret,count=200000);assert m.reg_read(UC_X86_REG_EIP)==ret
  rows.append(dict(state=state,age=age,kind=kind,callback=callback,flags=flags,flags2=flags2,missing=missing,geometry=geometry,rate=rate,output=[get(shot+k) for k in (0,0x8c,0xc,0x10,0x14,8,0xb0)]+[get(vm+k) for k in (0x530,0x534,0x40,0x5e0,0x5e4,0x5e8)],movement=[get(shot+k) for k in (0x48,0x4c,0x50,0x60,0x64,0x7c,0x80,0x84)],area=[get(area+i*4) for i in range(37)],events=events))
 (ROOT/'artifacts/th16/shot-update-native.json').write_text(json.dumps(dict(executableSha256=hashlib.sha256(img.data).hexdigest(),rows=rows),separators=(',',':'))+'\n',encoding='utf8');print(f'{len(rows)} native TH16 complete shot updates')
if __name__=='__main__':main()
