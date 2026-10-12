"""Full444e10 and444b20, only ANM delivery/audio and rejected callback controlled."""
import hashlib,importlib,itertools,json,struct
from pathlib import Path
from unicorn import *
from unicorn.x86_const import *
ROOT=Path(__file__).resolve().parents[1]
def main():
 img,_,_=importlib.import_module('th-anm-handlers').handlers(16);m=Uc(UC_ARCH_X86,UC_MODE_32)
 for _,base,size,raw,n in img.sections:
  start=base&~4095;m.mem_map(start,((base+size+4095)&~4095)-start);m.mem_write(base,img.data[raw:raw+n])
 ret,player,sht,shot,vm,reject,stack=0x70000000,0x70001000,0x70040000,0x70050000,0x70060000,0x700e0000,0x700ff000;m.mem_map(ret,0x100000)
 put=lambda p,v:m.mem_write(p,struct.pack('<I',v&0xffffffff));get=lambda p:struct.unpack('<I',m.mem_read(p,4))[0]
 bits=lambda v:struct.unpack('<I',struct.pack('<f',v))[0];rows=[];events=[]
 put(0x4a6ef8,player);put(player+0x2c788,sht);put(player+0x2c78c,sht);put(sht+0x190,sht+0x200);put(player+0xc,1);put(player+0x10,2);put(0x490eb0,0x4a5788)
 for i in range(12):
  o=player+0x660+i*0xe4;put(o+0x5c,-321+i*777);put(o+0x60,50319-i*333);put(o+0xa8,bits((i-5)*.75))
 m.mem_write(player+0x610,struct.pack('<fff',7.25,400.5,1.25));spec=sht+0x200
 def finish(pop,result):
  sp=m.reg_read(UC_X86_REG_ESP);m.reg_write(UC_X86_REG_EAX,result);m.reg_write(UC_X86_REG_ESP,sp+4+pop);m.reg_write(UC_X86_REG_EIP,get(sp))
 def hook(uc,address,size,data):
  sp=m.reg_read(UC_X86_REG_ESP)
  if address==0x406380:
   out,script,layer,prepend=[get(sp+i) for i in (4,8,12,16)];events.append([1,int(m.reg_read(UC_X86_REG_ECX)==2),script,layer]);assert prepend==0;put(out,77);finish(16,out)
  elif address==0x46efa0:assert get(sp+4)==77;finish(4,vm)
  elif address==0x445ed0:events.append([2,1,m.reg_read(UC_X86_REG_EDX),0])
  elif address==reject:events.append([2,7,m.reg_read(UC_X86_REG_EDX),0]);finish(0,1)
  elif address==0x45e1f0:events.append([3,get(sp+4),m.reg_read(UC_X86_REG_XMM2)&0xffffffff,0]);finish(4,0)
  elif address==0x46f1c0:events.append([4,get(sp+4),0,0]);finish(4,0)
 m.hook_add(UC_HOOK_CODE,hook)
 seed=struct.pack('<37I',0xabcdef06,*[0xa5000000+i for i in range(1,37)])*257
 for number,kind,angle,focus,family,callback,flags2,cursor,sound in itertools.product((0,1,4,101,106),(0,2),(-7.,995.,1000.),(0,1),(0,1),(0,1,2,4,7),(0,0x80),(3,255),(-1,12)):
  if number==0 and kind==2:continue
  events=[];m.mem_write(player+0xd080,seed);put(player+0xd110,cursor);m.mem_write(spec,bytes(0x58));m.mem_write(shot,bytes(0xc0));put(shot,0x80000000);put(shot+4,19);put(shot+0x1c,1);put(shot+0x90,123)
  m.mem_write(vm,bytes(0x600));put(vm+0x530,0x100);put(vm+0x534,flags2);put(vm+0x40,bits(3.25));m.mem_write(vm+0x5e0,struct.pack('<fff',11,22,33))
  m.mem_write(spec+2,struct.pack('<h',13));m.mem_write(spec+4,struct.pack('<ffffff',2.25,-3.5,4.25,7.5,angle,6.25));m.mem_write(spec+0x20,struct.pack('<bbhh',number,kind,7,sound));put(spec+0x28,{0:0,1:0x445ed0,2:0x446200,4:0x447450,7:reject}[callback])
  put(player+0x165c8,focus);put(0x4a57e4,399);put(0x4a57ec,100);put(0x4a5788,bits(.5));put(0x4a6d88,12345);put(0x4a6d8c,17)
  for i in range(16):put(player+0x165f8+i*4,123)
  put(stack,ret);put(stack+4,0x10000 if family else 0);put(stack+8,7);put(stack+12,player+0x610);m.reg_write(UC_X86_REG_ESP,stack);m.reg_write(UC_X86_REG_ECX,shot);m.reg_write(UC_X86_REG_MXCSR,0x1f80);m.reg_write(UC_X86_REG_FPCW,0x37f);m.reg_write(UC_X86_REG_FPSW,0);m.reg_write(UC_X86_REG_FPTAG,0xffff);m.emu_start(0x444e10,ret,count=100000);assert m.reg_read(UC_X86_REG_EIP)==ret
  area=player+0xd080+get(shot+0xb0)*0x94
  rows.append(dict(number=number,kind=kind,angle=angle,focus=focus,family=family,callback=callback,flags2=flags2,cursor=cursor,sound=sound,result=m.reg_read(UC_X86_REG_EAX),output=[get(shot+k) for k in (0,0x8c,0xac,0xc,0x10,0x14,0x9c,0xa0,0xa4)]+[get(0x4a6d88)&65535,get(0x4a6d8c)]+[get(shot+k) for k in (8,0xb0,0x90)]+[get(player+0xd110)]+[get(vm+k) for k in (0x530,0x534,0x40,0x5e0,0x5e4,0x5e8)]+[get(player+0x165f8+i*4) for i in range(16)],movement=[get(shot+k) for k in (0x48,0x4c,0x50,0x60,0x64,0x7c,0x80,0x84)],area=[get(area+i*4) for i in range(37)],events=events))
 (ROOT/'artifacts/th16/shot-factory-native.json').write_text(json.dumps(dict(executableSha256=hashlib.sha256(img.data).hexdigest(),rows=rows),separators=(',',':'))+'\n',encoding='utf8');print(f'{len(rows)} native TH16 complete shot factories')
if __name__=='__main__':main()
