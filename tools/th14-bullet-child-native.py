"""Retail 418140 ETEX 2000 paired-record request and parent index.
4191a0 child emission and 41ac70 parent cancellation are recorded boundaries.
"""
import hashlib,importlib,itertools,json,struct
from pathlib import Path
from unicorn import Uc,UC_ARCH_X86,UC_MODE_32,UC_HOOK_CODE
from unicorn.x86_const import *
ROOT=Path(__file__).resolve().parents[1]
def main():
 img,_,_=importlib.import_module('th-anm-handlers').handlers(14);m=Uc(UC_ARCH_X86,UC_MODE_32)
 for _,b,size,raw,n in img.sections:
  start=b&~4095;m.mem_map(start,((b+size+4095)&~4095)-start);m.mem_write(b,img.data[raw:raw+n])
 end,obj,stack=0x70000000,0x70001000,0x700ff000;m.mem_map(end,0x100000)
 put=lambda p,v:m.mem_write(p,struct.pack('<I',v&0xffffffff));get=lambda p:struct.unpack('<I',m.mem_read(p,4))[0]
 bits=lambda f:struct.unpack('<I',struct.pack('<f',f))[0]
 requests=[];cancels=0
 def sink(machine,a,size,user):
  nonlocal cancels
  sp=m.reg_read(UC_X86_REG_ESP)
  if a==0x4191a0:requests.append(list(struct.unpack('<224I',m.mem_read(get(sp+4),0x380))))
  else:cancels+=1
  m.reg_write(UC_X86_REG_EAX,0)
 for a in (0x4191a0,0x41ac70):m.mem_write(a,b'\xc2\x04\x00');m.hook_add(UC_HOOK_CODE,sink,begin=a,end=a)
 rows=[]
 for index,active,concurrent,angle,speed,variant,cancel in itertools.product((0,1,16),(0,4,0x100),(0,1),(-1000.,-999.,-998.5,-998.,-997.5,.37,200.),(-1000.,-999.,-998.5,-998.,-997.5,3.25),range(4),(0,1)):
  requests.clear();cancels=0;m.mem_write(obj,bytes(0x2000));m.mem_write(obj+0xbc0,struct.pack('<3f',12.25,80.5,3.25));put(obj+0xbd8,bits(2.75));put(obj+0xbdc,bits(-.125));put(obj+0xc20,index);put(obj+0xc04,active)
  program=[(j*0x12345+0x234567)&0xffffffff if j%11<8 else 0 for j in range(198)];at=index*11;program[at:at+11]=[bits(angle),bits(.35),bits(speed),bits(.75),(0xffffffff,0,1,13)[variant],(0xffffffff,0,3,17)[variant],(1,3,7,13)[variant],(1,2,4,7)[variant],0x2000,concurrent,0x1234]
  program[at+11+4]=(0,18,31,40)[variant];program[at+11+5]=(0,3,7,15)[variant];program[at+11+6]=cancel
  m.mem_write(obj+0xc28,struct.pack('<198I',*program));m.mem_write(stack-0x3000,bytes(0x3100));put(stack,end);m.reg_write(UC_X86_REG_ESP,stack);m.reg_write(UC_X86_REG_ECX,obj);m.reg_write(UC_X86_REG_MXCSR,0x1f80);m.reg_write(UC_X86_REG_FPCW,0x37f);m.reg_write(UC_X86_REG_FPSW,0);m.reg_write(UC_X86_REG_FPTAG,0xffff)
  m.emu_start(0x418140,end,count=100000);assert m.reg_read(UC_X86_REG_EIP)==end
  rows.append(dict(index=index,active=active,program=program,result=[get(obj+0xc20),get(obj+0xc04),cancels],requests=requests[:]))
 (ROOT/'artifacts/th14/bullet-child-native.json').write_text(json.dumps(dict(executableSha256=hashlib.sha256(img.data).hexdigest(),cases=rows),separators=(',',':'))+'\n',encoding='utf8');print(f'{len(rows)} native ETEX 2000 paired-record cases.')
if __name__=='__main__':main()
