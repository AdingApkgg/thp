"""453a90 with full item pools: captures allocation attempts and actual RNG.
Individual item allocation/ANM initialization is verified by item fixtures.
"""
import hashlib,importlib,json,struct
from pathlib import Path
from unicorn import Uc,UC_ARCH_X86,UC_MODE_32,UC_HOOK_CODE
from unicorn.x86_const import *
ROOT=Path(__file__).resolve().parents[1]
def main():
 img,_,_=importlib.import_module('th-anm-handlers').handlers(14);m=Uc(UC_ARCH_X86,UC_MODE_32)
 for _,b,size,raw,n in img.sections:
  start=b&~4095;m.mem_map(start,((b+size+4095)&~4095)-start);m.mem_write(b,img.data[raw:raw+n])
 end,player,p,stack,items=0x70000000,0x70001000,0x70020000,0x700ff000,0x72000000;m.mem_map(end,0x100000);m.mem_map(items,0xe00000)
 def put(p,v):m.mem_write(p,struct.pack('<I',v&0xffffffff))
 def get(p):return struct.unpack('<I',m.mem_read(p,4))[0]
 def bits(v):return struct.unpack('<I',struct.pack('<f',v))[0]
 requests=[]
 def observe(machine,a,length,user):
  if a==0x453ad5:requests.append([1,get(p),get(p+4),get(p+8),bits(-1.5707963705062866),bits(2.2)])
  elif a==0x453cfa:requests.append([9,get(p),get(p+4),get(p+8),m.reg_read(UC_X86_REG_XMM1)&0xffffffff,bits(2.2)])
  else:requests.append([9,get(p),get(p+4),get(p+8),m.reg_read(UC_X86_REG_XMM2)&0xffffffff,m.reg_read(UC_X86_REG_XMM1)&0xffffffff])
 for a in (0x453ad5,0x453cfa,0x453f00):m.hook_add(UC_HOOK_CODE,observe,begin=a,end=a)
 rows=[]
 for n in range(1440):
  requests.clear();power=n%5;plain=(0,499,500,549,550,700,999,1200)[n//5%8];focused=(0,99,100,199,200,501)[n//40%6];seed=(0,1,12345,0xffff,0x9630,54321)[n//240%6]
  m.mem_write(player,bytes(0x19000));m.mem_write(stack-0x2000,bytes(0x2100));put(0x4db67c,player);put(0x4db660,items);put(player+0x184b4,plain);put(player+0x184b8,focused);put(0x4f5858,power*40);put(0x4f5860,40);put(0x4db510,seed);put(0x4db514,123);put(items+0xddd878,27)
  m.mem_write(p,struct.pack('<3f',240,123,.1));put(stack,end);m.reg_write(UC_X86_REG_ESP,stack);m.reg_write(UC_X86_REG_ECX,p);m.reg_write(UC_X86_REG_FPCW,0x37f);m.reg_write(UC_X86_REG_FPSW,0);m.reg_write(UC_X86_REG_FPTAG,0xffff);m.reg_write(UC_X86_REG_MXCSR,0x1f80)
  m.emu_start(0x453a90,end,count=100000);assert m.reg_read(UC_X86_REG_EIP)==end
  rows.append(dict(power=power,plain=plain,focused=focused,seed=seed,result=[get(player+0x184b4),get(player+0x184b8),get(0x4db510),get(0x4db514),get(items+0xddd878)],requests=requests[:]))
 # Execute the actual 451760 wrapper; intercept its reward consumer only.
 # An unrelated owner origin deliberately differs from the damage-area center.
 area,owner,spec,callback=p+0x1000,p+0x2000,p+0x3000,p+0x5000
 m.mem_write(0x453a90,b'\xc3');m.mem_write(callback,b'\x31\xc0\xc2\x0c\x00')
 captured=[]
 def midpoint_observe(machine,a,length,user):
  at=m.reg_read(UC_X86_REG_ECX);captured.append([get(at+i*4) for i in range(3)])
 m.hook_add(UC_HOOK_CODE,midpoint_observe,begin=0x453a90,end=0x453a90)
 midpoints=[]
 points=[(-192.0045,140.70,3),(-191.9955,-121.68,-7),(0,0,1),(192,448,8),(1e10,-1e10,4),(.000001,-.000001,9),(-49.87,298.28,12),(29.87,117.93,-4)]
 for a in points:
  for t in points:
   captured.clear();m.mem_write(stack-0x2000,bytes(0x2100));m.mem_write(area,bytes(0x400));m.mem_write(owner,bytes(0x200));m.mem_write(spec,bytes(0x80))
   m.mem_write(area+0x2c,struct.pack('<3f',*a));m.mem_write(owner+0x54,struct.pack('<3f',91,23,4));m.mem_write(p,struct.pack('<3f',*t))
   put(area+0x98,owner);put(owner+0xbc,spec);put(spec+0x34,callback);put(stack,end)
   m.reg_write(UC_X86_REG_ESP,stack);m.reg_write(UC_X86_REG_ECX,area);m.reg_write(UC_X86_REG_EDX,p)
   m.emu_start(0x451760,end,count=10000);assert m.reg_read(UC_X86_REG_EIP)==end and len(captured)==1
   midpoints.append(dict(args=[*a,*t],result=captured[0]))
 out=ROOT/'artifacts/th14/shot-rewards-native.json';out.write_text(json.dumps(dict(executableSha256=hashlib.sha256(img.data).hexdigest(),rows=rows,midpoints=midpoints),indent=2)+'\n',encoding='utf-8');print(f'{len(rows)} shot reward timelines, {len(midpoints)} native wrapper midpoints.')
if __name__=='__main__':main()
