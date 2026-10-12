"""Full445a30; geometry/callback/Bomb/score are explicit controlled services."""
import hashlib,importlib,json,struct
from pathlib import Path
from unicorn import *
from unicorn.x86_const import *
ROOT=Path(__file__).resolve().parents[1]
def main():
 img,_,_=importlib.import_module('th-anm-handlers').handlers(16);m=Uc(UC_ARCH_X86,UC_MODE_32)
 for _,base,size,raw,n in img.sections:
  start=base&~4095;m.mem_map(start,((base+size+4095)&~4095)-start);m.mem_write(base,img.data[raw:raw+n])
 ret,player,sht,bomb_object,query,size,last,bomb_out,bomb_func,callback,stack=0x70000000,0x70001000,0x70040000,0x70050000,0x70060000,0x70060010,0x70060020,0x70060030,0x700e0000,0x700e0010,0x700ff000;m.mem_map(ret,0x100000)
 put=lambda p,v:m.mem_write(p,struct.pack('<I',v&0xffffffff));get=lambda p:struct.unpack('<I',m.mem_read(p,4))[0]
 signed=lambda v:struct.unpack('<i',struct.pack('<I',v))[0];bits=lambda v:struct.unpack('<I',struct.pack('<f',v))[0];rows=[];events=[];seed=0
 put(0x4a6ef8,player);put(player+0x2c788,sht);put(0x4a6da8,bomb_object);put(bomb_object,bomb_object+0x100);put(bomb_object+0x10c,bomb_func);put(0x4919e0,callback);m.mem_write(query,struct.pack('<fff',2.25,300.5,1.25));m.mem_write(size,struct.pack('<ff',12,18))
 def finish(pop,result):
  sp=m.reg_read(UC_X86_REG_ESP);m.reg_write(UC_X86_REG_EAX,result&0xffffffff);m.reg_write(UC_X86_REG_ESP,sp+4+pop);m.reg_write(UC_X86_REG_EIP,get(sp))
 def hook(uc,address,length,data):
  sp=m.reg_read(UC_X86_REG_ESP)
  if address==bomb_func:
   value=(0,5,-9)[(seed//16)%3];events.append([1,value&0xffffffff,0]);finish(8,value)
  elif address in (0x4049c0,0x403d30):
   area=m.reg_read(UC_X86_REG_EBX);flags=get(area);mode=int(bool(flags&2))*2+int(bool(seed&1));events.append([2,get(area+0x88),mode]);finish(24 if address==0x4049c0 else 16,int(bool(seed&128)))
  elif address==callback:
   area=m.reg_read(UC_X86_REG_ECX);id=(area-player-0xd080)//0x94;events.append([3,id,get(area+0x8c)]);value=signed(get(area+0x74));value=(abs(value)//2)*(-1 if value<0 else 1);put(area+0x74,value);finish(12,value+7)
  elif address==0x43e080:events.append([4,get(sp+4),0]);finish(4,0)
 m.hook_add(UC_HOOK_CODE,hook)
 for seed in range(512):
  for cap in (0,20,100):
   for advanced in (0,1):
    events=[];m.mem_write(player+0xd114,bytes(256*0x94));put(player+0x624,0);put(player+0x628,advanced);put(sht+0x28,cap);put(bomb_object+0x30,int(bool(seed&256)));put(bomb_out,1);m.mem_write(last,struct.pack('<fff',99,88,77))
    for id in (1,2,256):
     a=player+0xd080+id*0x94;w=[0]*37;w[0]=(0,1,3,5,7)[(seed+id)%5];w[1]=bits(5.5);w[3]=bits(-.75);w[5]=bits(4.25);w[6]=bits(7.5);w[7]=bits(2.25+id*.5);w[8]=bits(300.5);w[9]=bits(1.25);clock=(0,1,6,-3)[seed%4];w[25]=clock&0xffffffff;w[24]=(clock if seed&2 else -10)&0xffffffff;w[32]=(1,2,-1)[(seed//8+id)%3]&0xffffffff;w[29]=(13,-9,2147483647)[(seed//32+id)%3]&0xffffffff;w[30]=(0,8,2147483647)[(seed//64+id)%3]&0xffffffff;w[31]=(10,9999999,10000000)[(seed//128+id)%3];w[33]=7 if seed&64 else 0;w[34]=id;w[35]=123;w[36]=int(bool(seed&16));m.mem_write(a,struct.pack('<37I',*w))
    args=(query,size if seed&1 else 0,bits(3),bomb_out,last,int(bool(seed&8)),7 if seed&4 else 0);put(stack,ret)
    for n,v in enumerate(args):put(stack+4+n*4,v)
    m.reg_write(UC_X86_REG_XMM3,bits(.5));m.reg_write(UC_X86_REG_ESP,stack);m.reg_write(UC_X86_REG_MXCSR,0x1f80);m.reg_write(UC_X86_REG_FPCW,0x37f);m.reg_write(UC_X86_REG_FPSW,0);m.reg_write(UC_X86_REG_FPTAG,0xffff);m.emu_start(0x445a30,ret,count=200000);assert m.reg_read(UC_X86_REG_EIP)==ret
    rows.append(dict(seed=seed,cap=cap,advanced=advanced,output=[m.reg_read(UC_X86_REG_EAX),get(bomb_out)]+list(struct.unpack('<3I',m.mem_read(last,12))),areas={str(id):list(struct.unpack('<37I',m.mem_read(player+0xd080+id*0x94,0x94))) for id in (1,2,256)},events=events))
 (ROOT/'artifacts/th16/shot-collect-native.json').write_text(json.dumps(dict(executableSha256=hashlib.sha256(img.data).hexdigest(),rows=rows),separators=(',',':'))+'\n',encoding='utf8');print(f'{len(rows)} native TH16 complete damage collections')
if __name__=='__main__':main()
