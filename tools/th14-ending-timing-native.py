"""Execute retail420260/4202d0 with real timer callees and controlled sound delivery."""
import hashlib,importlib,itertools,json,struct
from pathlib import Path
from unicorn import Uc,UC_ARCH_X86,UC_MODE_32,UC_HOOK_CODE
from unicorn.x86_const import *
ROOT=Path(__file__).resolve().parents[1]
def main():
 img,_,_=importlib.import_module('th-anm-handlers').handlers(14);m=Uc(UC_ARCH_X86,UC_MODE_32)
 for _,b,size,raw,n in img.sections:
  start=b&~4095;m.mem_map(start,((b+size+4095)&~4095)-start);m.mem_write(b,img.data[raw:raw+n])
 arena,vm,owner,instruction,stack=0x70000000,0x70001000,0x70002000,0x70003000,0x7000f000;m.mem_map(arena,0x10000)
 def put(p,v):m.mem_write(p,struct.pack('<I',v&0xffffffff))
 def get(p):return struct.unpack('<I',m.mem_read(p,4))[0]
 def bits(v):return struct.unpack('<I',struct.pack('<f',v))[0]
 sounds=[];music_fades=[];fades=[]
 def hook(uc,a,size,data):
  if a not in (0x46e3d0,0x46ef90,0x46d1c0):return
  sp=uc.reg_read(UC_X86_REG_ESP)
  if a==0x46e3d0:sounds.append(get(sp+4));pop=8
  elif a==0x46ef90:assert get(sp+4)==5;music_fades.append(get(sp+8));pop=12
  else:fades.append([uc.reg_read(UC_X86_REG_ECX),uc.reg_read(UC_X86_REG_EDX),*[get(sp+i*4) for i in range(1,5)]]);pop=16
  uc.reg_write(UC_X86_REG_EIP,get(sp));uc.reg_write(UC_X86_REG_ESP,sp+4+pop)
 m.hook_add(UC_HOOK_CODE,hook);put(0x4db540,owner)
 inputs=[]
 for op,duration,wait,seen,profile,pressed,rate in itertools.product((5,6),(-1,0,1,6,7,60),(0,1,6,7),range(4),((0,0),(512,0),(1,19),(1,20)),(0,1,0x80000),(.5,1,1.25)):
  inputs.append(dict(op=op,duration=duration,wait=wait,seen=seen,held=profile[0],shootFrames=profile[1],pressed=pressed,rate=rate,time=0))
 for seen,held,rate,time in itertools.product(range(4),(0,512),(.5,1,1.25),(0,39,40)):
  inputs.append(dict(op=9,duration=0x123456,wait=0,seen=seen,held=held,shootFrames=0,pressed=0,rate=rate,time=time))
 for seen,held,rate in itertools.product(range(4),(0,512),(0,.3,.5,.75,.99,1,1.01,1.25,4)):
  inputs.append(dict(op=11,duration=0,wait=0,seen=seen,held=held,shootFrames=0,pressed=0,rate=rate,time=0))
 for op,duration,rate,seen,held in itertools.product((13,14),(-1,0,1,7,200),(.5,1,1.25),range(4),(0,512)):
  inputs.append(dict(op=op,duration=duration,wait=0,seen=seen,held=held,shootFrames=0,pressed=0,rate=rate,time=0))
 rows=[]
 callbacks=[]
 for op,seen,profile,rate,flags,frames in itertools.product((0,5,6,9),range(4),((0,0),(512,0),(1,19),(1,20)),(.5,1,1.25),(1,2),(0,1,10,11,12,0x7fffffff,0xffffffff)):
  callbacks.append(dict(op=op,duration=60 if op in (5,6) else 0x123456,wait=0,seen=seen,held=profile[0],shootFrames=profile[1],pressed=0,rate=rate,time=0,flags=flags,frames=frames,callback=True))
 callback_rows=[]
 for args in inputs+callbacks:
  m.mem_write(vm,bytes(0xf0));put(owner+0x20,args['seen']);put(0x4d6878,args['held']);put(0x4d6884,args['pressed']);put(0x4d698c,args['shootFrames']);put(0x4d8f58,bits(args['rate']))
  for offset,initial in ((4,0),(0x18,args['time']),(0x2c,args['wait'])):
   put(vm+offset,initial-1);put(vm+offset+4,initial);put(vm+offset+8,bits(initial));put(vm+offset+12,0x4d8f58);put(vm+offset+16,1)
  put(vm+0x54,instruction);put(vm+0x74,args.get('flags',1));put(vm+0x78,3);put(vm+0x7c,0xffffff)
  put(owner+0x18,vm);put(owner+0x24,args.get('frames',0));put(0x4d964c,0);put(0x4d9684,0)
  scheduled=40 if args['op']==9 else 0
  m.mem_write(instruction,struct.pack('<HBBI',scheduled,args['op'],4,args['duration']&0xffffffff)+struct.pack('<HBB',65535,0,0))
  sounds.clear();music_fades.clear();fades.clear();calls=0
  while True:
   put(stack,arena);m.reg_write(UC_X86_REG_ESP,stack);m.reg_write(UC_X86_REG_ECX,owner if args.get('callback') else vm)
   m.emu_start(0x41ff70 if args.get('callback') else 0x420260,arena,count=2000);assert m.reg_read(UC_X86_REG_EIP)==arena
   calls+=1;assert calls<=12
   if not args.get('callback') or m.reg_read(UC_X86_REG_EAX)!=6:break
  row=dict(args,active=not get(0x4d964c) if args.get('callback') else not m.reg_read(UC_X86_REG_EAX),offset=get(vm+0x54)-instruction,flags=get(vm+0x74),line=get(vm+0x78),color=get(vm+0x7c),sounds=sounds[:],fades=fades[:],musicFadeFrames=music_fades[-1]*60 if music_fades else -1,timers=[[get(vm+off+n*4) for n in range(3)] for off in (4,0x18,0x2c)])
  if args.get('callback'):row.update(finalFrames=get(owner+0x24),calls=calls);callback_rows.append(row)
  else:rows.append(row)
 input_rows=[]
 for initial,profile in itertools.product((0,18,25,0xffffffff),range(4)):
  m.mem_write(vm,bytes(0x240))
  for bit in range(32):put(vm+0x14+bit*4,initial);put(vm+0x114+bit*4,initial)
  samples=[]
  for frame in range(100):
   held=(1,512,1 if frame%3 else 0,513)[profile]
   put(vm+4,get(vm));put(vm,held);put(stack,arena);m.reg_write(UC_X86_REG_ESP,stack);m.reg_write(UC_X86_REG_ECX,vm)
   m.emu_start(0x407540,arena,count=1000);assert m.reg_read(UC_X86_REG_EIP)==arena
   samples.append(dict(held=held,state=[get(vm+o) for o in (0,4,0xc,0x10,8,0x22c)],counts=[get(vm+0x14+b*4) for b in range(32)],heldFrames=[get(vm+0x114+b*4) for b in range(32)]))
  input_rows.append(dict(initial=initial,samples=samples))
 out=ROOT/'artifacts/th14/ending-timing-native.json';out.write_text(json.dumps(dict(executableSha256=hashlib.sha256(img.data).hexdigest(),rows=rows,callbacks=callback_rows,inputRows=input_rows),indent=2)+'\n',encoding='utf-8')
 print(f'{len(rows)} retail ending wait/timer cases, {len(callbacks)} scheduler cases')
if __name__=='__main__':main()
