"""Complete4455d0, own clocks execute;445470 emits a controlled frame request."""
import hashlib,importlib,itertools,json,struct
from pathlib import Path
from unicorn import *
from unicorn.x86_const import *
ROOT=Path(__file__).resolve().parents[1]
def main():
 img,_,_=importlib.import_module('th-anm-handlers').handlers(16);m=Uc(UC_ARCH_X86,UC_MODE_32)
 for _,base,size,raw,n in img.sections:
  start=base&~4095;m.mem_map(start,((base+size+4095)&~4095)-start);m.mem_write(base,img.data[raw:raw+n])
 ret,player,stack=0x70000000,0x70001000,0x700ff000;m.mem_map(ret,0x100000)
 put=lambda p,v:m.mem_write(p,struct.pack('<I',v&0xffffffff));get=lambda p:struct.unpack('<I',m.mem_read(p,4))[0]
 bits=lambda v:struct.unpack('<I',struct.pack('<f',v))[0];events=[]
 def hook(machine,a,size,user):
  sp=m.reg_read(UC_X86_REG_ESP);events.append([get(sp+4),get(sp+8)]);m.reg_write(UC_X86_REG_EAX,0)
 m.mem_write(0x445470,b'\xc2\x08\x00');m.hook_add(UC_HOOK_CODE,hook,begin=0x445470,end=0x445470);put(0x490eb0,0x4a5788)
 rows=[]
 for state,held,regular,long,rate,same in itertools.product((0,1,2,4),(0,1),(-1,0,1,13,14,15),(-1,0,1,118,119,120),(0.,.5,1.,1.5),(0,1)):
  m.mem_write(player,bytes(0x30000));put(player+0x165a8,state);put(player+0x2c790,123);put(player+0x2c794,1)
  for off,clock in ((0x165cc,regular),(0x165e0,long)):
   put(player+off,clock if same else clock-1);put(player+off+4,clock);put(player+off+8,bits(clock+.25));put(player+off+0xc,0);put(player+off+0x10,1)
  put(0x4a52c8,held);put(0x4a5788,bits(rate));put(stack,ret);m.reg_write(UC_X86_REG_ESP,stack);m.reg_write(UC_X86_REG_ECX,player);m.reg_write(UC_X86_REG_MXCSR,0x1f80);events.clear();m.emu_start(0x4455d0,ret,count=100000);assert m.reg_read(UC_X86_REG_EIP)==ret
  rows.append(dict(state=state,held=held,regular=regular,long=long,rate=rate,same=same,output=[get(player+o+k) for o in (0x165cc,0x165e0) for k in (0,4,8)]+[get(player+0x2c790),get(player+0x2c794)&255],events=events[:]))
 (ROOT/'artifacts/th16/shot-schedule-native.json').write_text(json.dumps(dict(executableSha256=hashlib.sha256(img.data).hexdigest(),rows=rows),separators=(',',':'))+'\n',encoding='utf8');print(f'{len(rows)} original TH16 two-clock firing cases')
if __name__=='__main__':main()
