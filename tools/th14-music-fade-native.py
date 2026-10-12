"""Whole retail481540 fade tick and481200 volume, controlled DirectSound."""
import hashlib,importlib,itertools,json,struct
from pathlib import Path
from unicorn import Uc,UC_ARCH_X86,UC_MODE_32,UC_HOOK_CODE
from unicorn.x86_const import *
ROOT=Path(__file__).resolve().parents[1]
def main():
 img,*_=importlib.import_module('th-anm-handlers').handlers(14);m=Uc(UC_ARCH_X86,UC_MODE_32)
 for _,b,size,raw,n in img.sections:
  p=b&~4095;m.mem_map(p,((b+size+4095)&~4095)-p);m.mem_write(b,img.data[raw:raw+n])
 base=0x70000000;m.mem_map(base,0x10000);owner=base+0x1000;holder=base+0x2000;voice=base+0x3000;vtable=base+0x4000;stack=base+0xf000;events=[]
 def put(p,v):m.mem_write(p,struct.pack('<I',v&0xffffffff))
 def get(p):return struct.unpack('<I',m.mem_read(p,4))[0]
 def sink(uc,a,n,u):
  sp=uc.reg_read(UC_X86_REG_ESP);stop=a==base+0x5000
  events.append(['stop',0] if stop else ['volume',get(sp+8)])
  uc.reg_write(UC_X86_REG_EAX,0);uc.reg_write(UC_X86_REG_EIP,get(sp));uc.reg_write(UC_X86_REG_ESP,sp+(8 if stop else 12))
 put(owner+4,holder);put(holder,voice);put(voice,vtable)
 for off,a in ((0x48,base+0x5000),(0x3c,base+0x6000)):
  put(vtable+off,a);m.hook_add(UC_HOOK_CODE,sink,begin=a,end=a)
 def call(a):
  put(stack,base);m.reg_write(UC_X86_REG_ESP,stack);m.reg_write(UC_X86_REG_ECX,owner);m.reg_write(UC_X86_REG_MXCSR,0x1f80);m.emu_start(a,base,count=10000);assert m.reg_read(UC_X86_REG_EIP)==base
 rows=[]
 for master,frames in itertools.product((0,1,14,50,99,100),(0,1,2,3,17,60,120,240)):
  put(0x4fd1ac,master);put(owner+0x14,frames);put(owner+0x18,frames);put(owner+0x1c,1);steps=[]
  for n in range(max(frames,1)+2):
   events.clear();call(0x481540)
   steps.append(dict(state=[get(owner+o) for o in (0x14,0x18,0x1c)],result=m.reg_read(UC_X86_REG_EAX),events=events[:]))
  rows.append(dict(master=master,frames=frames,steps=steps))
 proof=dict(passed=True,rows=rows,executableSha256=hashlib.sha256(img.data).hexdigest(),scope='Whole481540 countdown/stop and481200 SSE master-volume setter with controlled DirectSound Stop/SetVolume. Eight nonnegative durations including zero, six master levels, terminal plus two inactive ticks. No asynchronous thread cadence, pause scheduling, PCM or device latency equivalence.')
 (ROOT/'artifacts/th14/music-fade-native.json').write_text(json.dumps(proof)+'\n',encoding='utf8');print('PASS',len(rows),'native fade timelines')
if __name__=='__main__':main()
