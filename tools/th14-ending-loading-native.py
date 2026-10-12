"""Actual ending op7 / pending callbacks /420c00 worker completion; services controlled."""
import hashlib,importlib,itertools,json,struct
from pathlib import Path
from unicorn import Uc,UC_ARCH_X86,UC_MODE_32,UC_HOOK_CODE
from unicorn.x86_const import *
ROOT=Path(__file__).resolve().parents[1]
def main():
 img,*_=importlib.import_module('th-anm-handlers').handlers(14);m=Uc(UC_ARCH_X86,UC_MODE_32)
 for _,b,size,raw,n in img.sections:
  p=b&~4095;m.mem_map(p,((b+size+4095)&~4095)-p);m.mem_write(b,img.data[raw:raw+n])
 base=0x70000000;m.mem_map(base,0x80000)
 vm,owner,supervisor,resource,msg,stack=(base+n for n in (0x1000,0x2000,0x10000,0x30000,0x40000,0x7f000));events=[]
 def put(p,v):m.mem_write(p,struct.pack('<I',v&0xffffffff))
 def get(p):return struct.unpack('<I',m.mem_read(p,4))[0]
 def bits(v):return struct.unpack('<I',struct.pack('<f',v))[0]
 def hook(uc,a,n,u):
  sp=uc.reg_read(UC_X86_REG_ESP)
  if a==0x47ed10:
   p=get(sp+12);events.append(dict(service='loading',script=get(sp+8),position=list(struct.unpack('<3I',uc.mem_read(p,12))),layer=get(sp+20)));put(get(sp+4),79);uc.reg_write(UC_X86_REG_EAX,get(sp+4));pop=28
  elif a==0x47d7f0:events.append(dict(service='release',file=get(sp+4)));pop=4
  elif a==0x403c30:
   assert get(sp+4)==0x420c00 and get(sp+8)==vm;events.append(dict(service='worker',slot=get(vm+0xec)));pop=8
  elif a==0x47d090:
   events.append(dict(service='load',file=get(sp+4),name=bytes(uc.mem_read(get(sp+8),16)).split(b'\0')[0].decode('ascii')));uc.reg_write(UC_X86_REG_EAX,resource);pop=8
  elif a==0x47f140:events.append(dict(service='interrupt',handle=get(sp+4),label=get(sp+8)));pop=8
  else:return
  uc.reg_write(UC_X86_REG_EIP,get(sp));uc.reg_write(UC_X86_REG_ESP,sp+4+pop)
 m.hook_add(UC_HOOK_CODE,hook)
 def call(a,this):
  put(stack,base);m.reg_write(UC_X86_REG_ESP,stack);m.reg_write(UC_X86_REG_ECX,this);m.emu_start(a,base,count=20000);assert m.reg_read(UC_X86_REG_EIP)==base
 def state():return [get(vm+0x54)-msg,get(vm+0x74),get(vm+0x78),get(vm+0x7c),get(owner+0x24),*[get(vm+off+i*4) for off in (4,0x18,0x2c) for i in range(3)]]
 rows=[]
 for slot,rate,delay,seen in itertools.product(range(4),(.5,1,1.25),(0,1,9,44),range(4)):
  m.mem_write(base,bytes(0x7e000));put(0x4db540,owner);put(owner+0x18,vm);put(owner+0x20,seen);put(0x4db520,supervisor);put(supervisor+0x191e4,resource);put(0x4d8f58,bits(rate));put(0x4d6878,0);put(0x4d6884,0);m.mem_write(0x4f5815,b'\0')
  for off in (4,0x18,0x2c):put(vm+off,-1);put(vm+off+12,0x4d8f58);put(vm+off+16,1)
  put(vm+0x54,msg);put(vm+0x74,1);put(vm+0x7c,0xffffff)
  path=b'e01.anm\0';code=struct.pack('<HBBi',0,7,4+len(path),slot)+path+struct.pack('<HBBI',0,9,4,0x123456)+struct.pack('<HBB',65535,0,0);m.mem_write(msg,code)
  events.clear();call(0x41ff70,owner);requested=state();assert requested[1]==5 and requested[0]==16
  assert get(supervisor+0x191ec)==79
  pending=[]
  for tick in range(delay):call(0x41ff70,owner);pending.append(state());assert pending[-1][0:4]==requested[0:4]
  call(0x420c00,0);completed=state();assert completed[1]==1;assert get(vm+0x80+slot*4)==resource;assert get(supervisor+0x191ec)==0
  call(0x41ff70,owner);resumed=state();assert resumed[0]==24 and resumed[3]==0x123456
  assert events==[dict(service='loading',script=17,position=[bits(960),bits(784),0],layer=0xffffffff),dict(service='release',file=20+slot),dict(service='worker',slot=slot),dict(service='load',file=20+slot,name='e01.anm'),dict(service='interrupt',handle=79,label=1)],events
  rows.append(dict(slot=slot,rate=rate,delay=delay,seen=seen,requested=requested,pending=pending,completed=completed,resumed=resumed,events=events[:]))
 result=dict(passed=True,executableSha256=hashlib.sha256(img.data).hexdigest(),rows=rows,scope='Whole retail41ff70 ending callback/4202d0 opcode7, real420d20 loading wrapper and actual420c00 completion worker entry. Observes instructions, flags, line/color, frame count and all previous/current/fractional timer words during waits and resume; resource slot20..23 release/load, async worker request, loading root coordinates and interrupt1/handle clear. Thread dispatch, resource decoding/templates, ANM factory and interrupt delivery controlled. Actual worker scheduling, child ANM state, GPU and complete ending excluded.')
 (ROOT/'artifacts/th14/ending-loading-native.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print(f'PASS {len(rows)} retail ending resource wait/worker timelines')
if __name__=='__main__':main()
