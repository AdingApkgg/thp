"""Complete446260, actual angle/trig math; audio and ANM boundaries controlled."""
import hashlib,importlib,json,struct
from pathlib import Path
from unicorn import *
from unicorn.x86_const import *
ROOT=Path(__file__).resolve().parents[1]
def main():
 img,_,_=importlib.import_module('th-anm-handlers').handlers(16);m=Uc(UC_ARCH_X86,UC_MODE_32)
 for _,base,size,raw,n in img.sections:
  start=base&~4095;m.mem_map(start,((base+size+4095)&~4095)-start);m.mem_write(base,img.data[raw:raw+n])
 ret,player,sht,shot,vm,message,audio,pan,stack=0x70000000,0x70001000,0x70040000,0x70050000,0x70060000,0x70070000,0x70080000,0x700e0000,0x700ff000;m.mem_map(ret,0x100000)
 put=lambda p,v:m.mem_write(p,struct.pack('<I',v&0xffffffff));get=lambda p:struct.unpack('<I',m.mem_read(p,4))[0];bits=lambda v:struct.unpack('<I',struct.pack('<f',v))[0];f32=lambda v:struct.unpack('<f',struct.pack('<f',v))[0];rows=[];events=[];seed=0
 put(0x4a6ef8,player);put(player+0x2c788,sht);put(player+0x2c78c,sht);put(sht+0x190,sht+0x200);put(0x4dba74,audio);put(audio,audio+0x100);put(audio+0x140,pan);put(0x4a6dcc,message)
 for i in range(12):o=player+0x660+i*0xe4;put(o+0x5c,-321+i*777);put(o+0x60,50319-i*333)
 def finish(pop,result):
  sp=m.reg_read(UC_X86_REG_ESP);m.reg_write(UC_X86_REG_EAX,result&0xffffffff);m.reg_write(UC_X86_REG_ESP,sp+4+pop);m.reg_write(UC_X86_REG_EIP,get(sp))
 def hook(uc,address,length,data):
  sp=m.reg_read(UC_X86_REG_ESP)
  if address==pan:events.append([1,get(sp+8)]);finish(8,0)
  elif address==0x46efa0:finish(4,0 if seed&128 else vm)
  elif address==0x46f0b0:events.append([2,get(sp+8)]);finish(8,0)
  elif address==0x45e2a0:events.append([3,get(sp+4)]);finish(4,0)
 m.hook_add(UC_HOOK_CODE,hook)
 for seed in range(8192):
  season=seed&1;index=(seed//2)%(6 if season else 4);angle=(-.75,-1.5707963705062866,7.)[(seed//1024)%3];current=(-7.,-1.5707963705062866,f32(angle-.0005),f32(angle+.002))[(seed//64)%4];length=(0.,512.,510.,530.)[(seed//256)%4];events=[]
  m.mem_write(sht+0x200,bytes(0x58));m.mem_write(sht+0x220,struct.pack('<b',(101 if season else 1)+index));put(sht+0x214,bits(angle));m.mem_write(shot,bytes(0xc0));put(shot,2);put(shot+8,77);put(shot+0xac,0x10000 if season else 0);put(shot+0x8c,(1,2,3)[(seed//16)%3]);put(shot+0xb0,2);m.mem_write(shot+0x48,struct.pack('<fff',7,8,9));put(shot+0x64,bits(current));put(shot+0xa0,bits(length));put(shot+0xa4,bits(7.5));put(shot+0x94,int(bool(seed&4)));put(shot+0x98,int(bool(seed&8)))
  area=player+0xd080+2*0x94;m.mem_write(area,struct.pack('<37I',0xabcdef07,*[0xa5000000+i for i in range(1,37)]));m.mem_write(vm,bytes(0x600));put(vm+0x530,0x100);put(vm+0x70,bits(7));put(vm+0x68,bits(3))
  put(player+0x610,bits((-200.,-33.,0.,201.)[(seed//1024)%4]));put(player+0x165c8,int(bool(seed&32)));put(player+0x165f4,0 if seed&2048 else 4);put(player+0x1669c,0 if seed&2048 else 6);put(player+0x165a8,(1,2,3,4)[(seed//512)%4]);put(player+0x165d0,-1 if seed&1024 else 0);put(0x4a57e4,399);put(0x4a57ec,100);cache=player+0x165f8+(index+(8 if season else 0))*4;put(cache,2 if seed&4096 else 3);put(message+0x1c8,int(bool(seed&256)));put(0x4a6dc0,0 if seed&512 else player)
  put(stack,ret);m.reg_write(UC_X86_REG_ESP,stack);m.reg_write(UC_X86_REG_ECX,shot);m.reg_write(UC_X86_REG_MXCSR,0x1f80);m.reg_write(UC_X86_REG_FPCW,0x37f);m.reg_write(UC_X86_REG_FPSW,0);m.reg_write(UC_X86_REG_FPTAG,0xffff);m.emu_start(0x446260,ret,count=200000);assert m.reg_read(UC_X86_REG_EIP)==ret
  rows.append(dict(seed=seed,output=[get(shot+k) for k in (0x8c,8,0x48,0x4c,0x50,0x64,0xa0,0x94,0x98)]+[get(cache)]+[get(vm+k) for k in (0x530,0x70,0x68)],area=list(struct.unpack('<37I',m.mem_read(area,0x94))),events=events))
 (ROOT/'artifacts/th16/shot-beam-update-native.json').write_text(json.dumps(dict(executableSha256=hashlib.sha256(img.data).hexdigest(),rows=rows),separators=(',',':'))+'\n',encoding='utf8');print(f'{len(rows)} native TH16 beam updates')
if __name__=='__main__':main()
