"""Retail ECL640 name writer and ETEX1000000 descriptor/dispatch; spawn is a recorded boundary."""
import hashlib,importlib,json,struct
from pathlib import Path
from unicorn import Uc,UC_ARCH_X86,UC_MODE_32,UC_HOOK_CODE
from unicorn.x86_const import *
ROOT=Path(__file__).resolve().parents[1]
def main():
 im,_,_=importlib.import_module('th-anm-handlers').handlers(14);m=Uc(UC_ARCH_X86,UC_MODE_32)
 for _,b,size,raw,n in im.sections:
  start=b&~4095;m.mem_map(start,((b+size+4095)&~4095)-start);m.mem_write(b,im.data[raw:raw+n])
 base=0x70000000;enemy=base+0x1000;bullet=base+0x6000;code=base+0xa000;stack=base+0x1f000;m.mem_map(base,0x20000)
 def put(p,v):m.mem_write(p,struct.pack('<I',v&0xffffffff))
 def get(p):return struct.unpack('<I',m.mem_read(p,4))[0]
 records=[];reads=[];args=[]
 def boundary(machine,a,size,user):
  sp=m.reg_read(UC_X86_REG_ESP)
  if a==0x48f980:
   p=get(sp+4);m.mem_write(p,bytes([get(sp+8)&255])*get(sp+12));m.reg_write(UC_X86_REG_EAX,p)
  elif a==0x42c1d0:
   at=get(sp+4);reads.append(at);m.reg_write(UC_X86_REG_EAX,args[at])
  elif a==0x421ef0:
   p=get(sp+4);name=bytes(m.mem_read(p,64)).split(b'\0')[0].decode('ascii');records.append(dict(name=name,descriptor=list(struct.unpack('<21I',m.mem_read(get(sp+8),84)))));m.reg_write(UC_X86_REG_EAX,0)
 for a,cleanup in ((0x48f980,0),(0x42c1d0,4),(0x421ef0,8),(0x4854a0,0)):
  m.mem_write(a,b'\xc2'+struct.pack('<H',cleanup) if cleanup else b'\xc3');m.hook_add(UC_HOOK_CODE,boundary,begin=a,end=a)
 setters=[]
 for emitter in range(16):
  for at in range(18):
   for name in ('MapleEnemy','Child','Spawner_Long_Name_0123456789'):
    m.mem_write(enemy,bytes(0x5000));m.mem_write(code,bytes(128));m.mem_write(enemy+0x598,b'\xa5'*0x3800);put(enemy+0x3d98+emitter*4,13)
    packed=struct.pack('<iHHHBBIiii',0,640,28+len(name)+1,0,255,3,0,emitter,at,len(name)+1)+name.encode()+b'\0';m.mem_write(code,packed);args[:]=[emitter,at];reads.clear()
    put(stack+0x1c,enemy);put(stack+0x28,code);m.reg_write(UC_X86_REG_ESP,stack);m.reg_write(UC_X86_REG_EDI,enemy);m.reg_write(UC_X86_REG_ESI,code);m.emu_start(0x4285af,0x429c28,count=1000);assert m.reg_read(UC_X86_REG_EIP)==0x429c28
    data=bytearray(m.mem_read(enemy+0x598,0x3800));offset=emitter*0x380+0x28+at*44+40;assert struct.unpack_from('<I',data,offset)[0]==code+28;struct.pack_into('<I',data,offset,28)
    setters.append(dict(emitter=emitter,index=at,name=name,code=packed.hex(),result=data.hex(),cursor=get(enemy+0x3d98+emitter*4),reads=reads[:]))
 rows=[]
 for index in (0,1,17):
  for active in (0,4):
   for concurrent in (0,1):
    for n in range(8):
     m.mem_write(bullet,bytes(0x3000));m.mem_write(code,b'Child\0'+bytes(122));records.clear()
     pos=[-12.25+n*4,70.5-n*3,n*.125];values=[n*.25,-2.5+n*.125,999.,-.125];ints=[-2147483648+n,-999+n,2147483647-n,n*991]
     m.mem_write(bullet+0xbc0,struct.pack('<3f',*pos));put(bullet+0xc20,index);put(bullet+0xc04,active)
     t=bullet+0xc28+index*44;m.mem_write(t,struct.pack('<4f4iIiI',*values,*ints,0x1000000,concurrent,code))
     put(stack,base);m.reg_write(UC_X86_REG_ESP,stack);m.reg_write(UC_X86_REG_ECX,bullet);m.emu_start(0x418140,base,count=100000);assert m.reg_read(UC_X86_REG_EIP)==base
     rows.append(dict(index=index,active=active,concurrent=concurrent,position=pos,floats=values,integers=ints,records=records[:],state=[get(bullet+0xc20),get(bullet+0xc04)]))
 out=ROOT/'artifacts/th14/bullet-enemy-spawn-native.json';out.write_text(json.dumps(dict(executableSha256=hashlib.sha256(im.data).hexdigest(),setters=setters,cases=rows),separators=(',',':'))+'\n',encoding='utf-8');print(f'{len(setters)} ECL640 writers and {len(rows)} ETEX enemy dispatch cases.')
if __name__=='__main__':main()
