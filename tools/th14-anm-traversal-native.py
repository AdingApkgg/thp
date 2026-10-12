"""Whole retail ordinary/overlay registry update and live layer construction."""
import hashlib,importlib,itertools,json,struct
from pathlib import Path
from unicorn import Uc,UC_ARCH_X86,UC_MODE_32,UC_HOOK_CODE
from unicorn.x86_const import *
ROOT=Path(__file__).resolve().parents[1]

def main():
 img=importlib.import_module('th-anm-handlers').handlers(14)[0];m=Uc(UC_ARCH_X86,UC_MODE_32)
 for _,b,size,raw,n in img.sections:
  start=b&~4095;m.mem_map(start,((b+size+4095)&~4095)-start);m.mem_write(b,img.data[raw:raw+n])
 base=0x70000000;manager=0x71000000;m.mem_map(base,0x20000);m.mem_map(manager,0x1000000);vms=[base+0x1000+i*0x1000 for i in range(6)];stack=base+0x1f000;callback=base+0x100;alive=[True]*6;events=[];mutation=0
 def put(p,v):m.mem_write(p,struct.pack('<I',v&0xffffffff))
 def get(p):return struct.unpack('<I',m.mem_read(p,4))[0]
 def index(p):return 0xffffffff if not p else vms.index(p)
 def hook(uc,a,n,u):
  sp=uc.reg_read(UC_X86_REG_ESP)
  if a==0x4854fe:alive[vms.index(get(sp+4))]=False
  elif a==callback:
   p=uc.reg_read(UC_X86_REG_ECX);events.append(index(p));node=get(p+0x574);target=p if mutation==1 else get(node) if mutation==2 and node else 0
   if target:put(target+0x1c,get(target+0x1c)|0x20)
   uc.reg_write(UC_X86_REG_EAX,0)
  uc.reg_write(UC_X86_REG_EIP,get(sp));uc.reg_write(UC_X86_REG_ESP,sp+4)
 for a in (callback,0x4854fe):m.hook_add(UC_HOOK_CODE,hook,begin=a,end=a)
 def run(address):
  put(stack,base);m.reg_write(UC_X86_REG_ESP,stack);m.reg_write(UC_X86_REG_ECX,manager);m.emu_start(address,base,count=100000);assert m.reg_read(UC_X86_REG_EIP)==base
 def capture():
  state=[]
  for i,p in enumerate(vms):state.extend([1,get(p+0x1c),index(get(p+0x594)),get(p+0x24),index(get(p+0x590))] if alive[i] else [0]*5)
  layers=[]
  for layer in range(36):
   p=get(manager+0xfe8218+layer*0x5cc+0x590);chain=[]
   while p:chain.append(index(p));assert len(chain)<=6;p=get(p+0x590)
   layers.append(chain)
  return dict(state=state,layers=layers,events=list(events))
 rows=[];parents=(-1,0,1,0,3,3);m.mem_write(0x4f5815,b'\0');put(0x4d8f58,0x3f800000)
 for order,mode,mask,mutation,layout in itertools.product(range(2),range(3),range(64),range(3),range(2)):
  alive[:]=[True]*6;events.clear();chain=list(range(6)) if order==0 else [5,2,4,1,3,0]
  for i,p in enumerate(vms):
   m.mem_write(p,bytes(0x700));put(p+0x1c,0x200|((i%3)*0x40)|(0x20 if mask&(1<<i) else 0));put(p+0x570,p);put(p+0x580,p);put(p+0x594,vms[parents[i]] if parents[i]>=0 else 0);put(p+0x5b8,callback)
   if i:put(p+0x588,vms[i-1]+0x580)
   if i<5:put(p+0x584,vms[i+1]+0x580)
   overlay=mode==2 or mode==1 and i%2;put(p+0x24,24 if layout==0 else (0,24,33,34,35,0)[i] if overlay else (0,3,24,33,3,24)[i])
  for group in range(2):
   members=[i for i in chain if (0 if mode==0 else 1 if mode==2 else i%2)==group];put(manager+(0xfe8208 if group==0 else 0xfe8210),vms[members[0]]+0x570 if members else 0);put(manager+(0xfe820c if group==0 else 0xfe8214),vms[members[-1]]+0x570 if members else 0)
   for k,i in enumerate(members):put(vms[i]+0x574,vms[members[k+1]]+0x570 if k+1<len(members) else 0);put(vms[i]+0x578,vms[members[k-1]]+0x570 if k else 0)
  ticks=[]
  for tick in range(3):events.clear();run(0x47e5e0);run(0x47e6c0);ticks.append(capture())
  rows.append(dict(input=[order,mode,mask,mutation,layout],ticks=ticks))
 report=dict(executableSha256=hashlib.sha256(img.data).hexdigest(),rows=rows,scope='Whole original47e5e0 ordinary and47e6c0 overlay update, actual46fe50 with stopped/null instruction and controlled pre-update callbacks, whole47eb50 destruction. Six synthetic external VMs with flattened grandchildren, two registry orders, ordinary/overlay/mixed membership,64 initial retirement masks, self/next retirement callbacks and two layer layouts; three consecutive ticks. Callback and CRT free controlled, lock disabled. Exact callback order, surviving flags2/parent/layer/draw-next and all36 live draw chains. No script animation, geometry, native pool recycling, registration factory or full original scene claim.')
 (ROOT/'artifacts/th14/anm-traversal-native.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print('PASS native traversal',len(rows),sum(len(r['ticks']) for r in rows))
if __name__=='__main__':main()
