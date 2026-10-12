"""Retail player scale requests and interpolation; option ANM/rebuild are boundaries."""
import hashlib,importlib,json,struct
from pathlib import Path
from unicorn import Uc,UC_ARCH_X86,UC_MODE_32,UC_HOOK_CODE
from unicorn.x86_const import *
ROOT=Path(__file__).resolve().parents[1]
def main():
 img,_,_=importlib.import_module('th-anm-handlers').handlers(14);m=Uc(UC_ARCH_X86,UC_MODE_32)
 for _,b,size,raw,n in img.sections:
  start=b&~4095;m.mem_map(start,((b+size+4095)&~4095)-start);m.mem_write(b,img.data[raw:raw+n])
 base,stack,end=0x70000000,0x700ff000,0x700fe000;m.mem_map(base,0x100000)
 player=base;put=lambda p,v:m.mem_write(p,struct.pack('<I',v&0xffffffff));get=lambda p:struct.unpack('<I',m.mem_read(p,4))[0];bits=lambda v:struct.unpack('<I',struct.pack('<f',v))[0]
 put(0x4db67c,player);events=[]
 def boundary(machine,address,size,user):
  sp=m.reg_read(UC_X86_REG_ESP)
  if address==0x47f140:events.append([get(sp+4),get(sp+8)])
  else:events.append(['rebuild'])
 for address,cleanup in ((0x47f140,8),(0x44f970,0)):
  m.mem_write(address,b'\xc2'+struct.pack('<H',cleanup) if cleanup else b'\xc3');m.hook_add(UC_HOOK_CODE,boundary,begin=address,end=address)
 offsets=[0x182d4,0x182d8,0x182dc,0x182e0,0x182e4,0x182ec,0x182f0,0x182f4,0x182f8,0x182fc,0x18300,0x18304,0x18308,0x1830c]
 def state():
  values=[get(player+o) for o in offsets];p=values[8];values[8]=0 if not p else 1 if p==base+0x80000 else 2;return values
 def call(entry,until=end):
  put(stack,end);m.reg_write(UC_X86_REG_ESP,stack);m.reg_write(UC_X86_REG_ECX,player);m.reg_write(UC_X86_REG_EDI,player)
  m.reg_write(UC_X86_REG_MXCSR,0x1f80);m.reg_write(UC_X86_REG_FPCW,0x37f);m.reg_write(UC_X86_REG_FPSW,0);m.reg_write(UC_X86_REG_FPTAG,0xffff)
  try:m.emu_start(entry,until,count=100000)
  except Exception:
   print(hex(m.reg_read(UC_X86_REG_EIP)),hex(m.reg_read(UC_X86_REG_ESP)));raise
  assert m.reg_read(UC_X86_REG_EIP)==until
 requests=[]
 for flags in (0,2,16,18,0xffffffff):
  for timer_flags in (0,1,0x80000000,0xffffffff):
   for pointer in (0,1,2):
    for value in (-float('inf'),-1.,-0.,1.,1.0000001192092896,2.,8.,float('inf'),float('nan')):
     m.mem_write(player,bytes(0x19000));events.clear();initial=[flags,bits(2),bits(4),bits(7),bits(9),7,13,bits(13.25),pointer,timer_flags,77,9,bits(5),33]
     for o,v in zip(offsets,initial):put(player+o,(0,base+0x80000,0x4d8f58)[pointer] if o==0x182f8 else v)
     for j in range(8):put(player+0xd79c+j*0xe4,2*j+1);put(player+0xd7a0+j*0xe4,2*j+2)
     m.reg_write(UC_X86_REG_XMM1,bits(value));call(0x4504c0)
     requests.append(dict(initial=initial,value=bits(value),result=state(),events=events[:]))
 updates=[]
 for target in (1.0000001192092896,2.,3.5,8.,float('inf')):
  for speed in (0.,.5,.99,1.,1.01,1.25):
   for frame in (0,1,2,3,119,120):
    for elapsed in (0,1,117,118,119,120):
     m.mem_write(player,bytes(0x19000));initial=[18,bits(1),bits(target),0,0,elapsed-1,elapsed,bits(elapsed+.25),2,1,120,0,bits(5),0]
     for o,v in zip(offsets,initial):put(player+o,0x4d8f58 if o==0x182f8 else v)
     put(0x4d8f58,bits(speed));put(player+0x690,frame);put(player+0x74,bits(17));put(player+0x78,bits(19));put(player+0x2c,0)
     for o,v in ((0x5e0,12.25),(0x5e4,-80.5),(0x5e8,3.25),(0x648,1.),(0x64c,2.),(0x650,5.),(0x654,30.),(0x658,35.),(0x65c,5.),(0x660,50.),(0x664,59.),(0x668,5.)):put(player+o,bits(v))
     call(0x44e1b4,0x44e8db)
     bounds=[get(player+o+n*4) for o in (0x630,0x63c,0x1835c,0x18368,0x18374,0x18380,0x1838c,0x18398) for n in range(3)]
     updates.append(dict(initial=initial,speed=bits(speed),frame=frame,result=state(),visual=[get(player+0x74),get(player+0x78),get(player+0x2c)],bounds=bounds))
 out=ROOT/'artifacts/th14/player-scale-native.json';out.write_text(json.dumps(dict(executableSha256=hashlib.sha256(img.data).hexdigest(),requests=requests,updates=updates))+'\n',encoding='utf8');print(f'{len(requests)} scale requests, {len(updates)} updates')
if __name__=='__main__':main()
