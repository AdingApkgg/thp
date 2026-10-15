"""Original 453a90: all three counters, with declared full item pools."""
import hashlib,importlib,json,struct
from pathlib import Path
from unicorn import Uc,UC_ARCH_X86,UC_MODE_32,UC_HOOK_CODE
from unicorn.x86_const import *
ROOT=Path(__file__).resolve().parents[1]

def main():
 img,_,_=importlib.import_module('th-anm-handlers').handlers(14);m=Uc(UC_ARCH_X86,UC_MODE_32)
 for _,b,size,raw,n in img.sections:
  first=b&~4095;m.mem_map(first,((b+size+4095)&~4095)-first);m.mem_write(b,img.data[raw:raw+n])
 end,player,p,stack,items=0x70000000,0x70001000,0x70020000,0x700ff000,0x72000000
 m.mem_map(end,0x100000);m.mem_map(items,0xe00000)
 def put(p,v):m.mem_write(p,struct.pack('<I',v&0xffffffff))
 def get(p):return struct.unpack('<I',m.mem_read(p,4))[0]
 def bits(v):return struct.unpack('<I',struct.pack('<f',v))[0]
 requests=[]
 def observe(machine,a,length,user):
  if a in (0x453ad5,0x4540a0):row=[1,get(p),get(p+4),get(p+8),bits(-1.5707963705062866),bits(2.2)]
  elif a==0x453cfa:row=[9,get(p),get(p+4),get(p+8),m.reg_read(UC_X86_REG_XMM1)&0xffffffff,bits(2.2)]
  else:row=[9,get(p),get(p+4),get(p+8),m.reg_read(UC_X86_REG_XMM2)&0xffffffff,m.reg_read(UC_X86_REG_XMM1)&0xffffffff]
  requests.append(row)
 for a in (0x453ad5,0x453cfa,0x453f00,0x4540a0):m.hook_add(UC_HOOK_CODE,observe,begin=a,end=a)
 rows=[]
 for n in range(1920):
  power=n%5;plain=(0,499,500,549,550,700,999,1200)[n//5%8]
  focused=(0,99,100,199,200,501)[n//40%6]
  third=(0,99,100,199,200,501,0x80000000,0xffffffff)[n//240%8]
  seed=(0,1,12345,0xffff,0x9630,54321)[n%6];requests.clear()
  m.mem_write(player,bytes(0x19000));m.mem_write(stack-0x2000,bytes(0x2100))
  put(0x4db67c,player);put(0x4db660,items);put(player+0x184b4,plain);put(player+0x184b8,focused);put(player+0x184bc,third)
  put(0x4f5858,power*100);put(0x4f5860,100);put(0x4db510,seed);put(0x4db514,123);put(items+0xddd878,27)
  m.mem_write(p,struct.pack('<3f',240,123,.1));put(stack,end)
  m.reg_write(UC_X86_REG_ESP,stack);m.reg_write(UC_X86_REG_ECX,p);m.reg_write(UC_X86_REG_FPCW,0x37f)
  m.reg_write(UC_X86_REG_FPSW,0);m.reg_write(UC_X86_REG_FPTAG,0xffff);m.reg_write(UC_X86_REG_MXCSR,0x1f80)
  m.emu_start(0x453a90,end,count=100000);assert m.reg_read(UC_X86_REG_EIP)==end
  rows.append(dict(power=power,plain=plain,focused=focused,third=third,seed=seed,
      result=[get(player+0x184b4),get(player+0x184b8),get(player+0x184bc),get(0x4db510),get(0x4db514),get(items+0xddd878)],requests=requests[:]))
 out=ROOT/'artifacts/th14/shot-third-reward-native-oct16.json';assert not out.exists()
 out.write_text(json.dumps(dict(executableSha256=hashlib.sha256(img.data).hexdigest(),rows=rows,
  originalFunction='0x453a90',thirdConsumer='0x454091..0x454274',itemPoolsDeclaredFull=True,
  originalCodeUnmodified=True,retailProcessesStarted=0,audioPlayed=False,productionChanged=False,
  toolSha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
  scope='Actual original machine-code reward consumer with all three counters, signed threshold edge controls, original RNG, and empty free-list heads. Captures attempted item creation in native order and native spawn-count changes. No item allocation/ANM/device or complete-game equivalence claim.'),indent=2)+'\n')
 print(json.dumps(dict(cases=len(rows),allocationAttempts=sum(len(r['requests']) for r in rows),thirdAtLeast100Cases=sum(100<=r['third']<0x80000000 for r in rows))))
if __name__=='__main__':main()
