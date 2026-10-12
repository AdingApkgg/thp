"""Whole retail47eb50 destruction with real registry/flattened family links."""
import hashlib,importlib,itertools,json,struct
from pathlib import Path
from unicorn import Uc,UC_ARCH_X86,UC_MODE_32,UC_HOOK_CODE
from unicorn.x86_const import *
ROOT=Path(__file__).resolve().parents[1]

def main():
 img=importlib.import_module('th-anm-handlers').handlers(14)[0];m=Uc(UC_ARCH_X86,UC_MODE_32)
 for _,b,size,raw,n in img.sections:
  start=b&~4095;m.mem_map(start,((b+size+4095)&~4095)-start);m.mem_write(b,img.data[raw:raw+n])
 base=0x70000000;manager=0x71000000;m.mem_map(base,0x20000);m.mem_map(manager,0x1000000);vms=[base+0x1000+i*0x1000 for i in range(6)];stack=base+0x1f000;alive=[True]*6
 def put(p,v):m.mem_write(p,struct.pack('<I',v&0xffffffff))
 def get(p):return struct.unpack('<I',m.mem_read(p,4))[0]
 def free(uc,a,n,u):
  sp=uc.reg_read(UC_X86_REG_ESP);alive[vms.index(get(sp+4))]=False;uc.reg_write(UC_X86_REG_EIP,get(sp));uc.reg_write(UC_X86_REG_ESP,sp+4)
 m.hook_add(UC_HOOK_CODE,free,begin=0x4854fe,end=0x4854fe)
 def index(p,offset=0):return 0xffffffff if not p else vms.index(p-offset)
 def capture():
  state=[]
  for i,p in enumerate(vms):
   state.extend([1,get(p+0x1c),index(get(p+0x594)),index(get(p+0x584),0x580),index(get(p+0x588),0x580),index(get(p+0x574),0x570),index(get(p+0x578),0x570)] if alive[i] else [0]*7)
  state.extend(index(get(manager+o),0x570) for o in (0xfe8208,0xfe820c,0xfe8210,0xfe8214));return state
 rows=[];parents=(-1,0,1,0,3,3)
 for order,mode in itertools.product(itertools.permutations(range(6)),range(3)):
  alive[:]=[True]*6
  for i,p in enumerate(vms):
   m.mem_write(p,bytes(0x700));put(p+0x1c,0x200|((i%3)*0x40));put(p+0x570,p);put(p+0x580,p);put(p+0x594,vms[parents[i]] if parents[i]>=0 else 0)
   if i:put(p+0x588,vms[i-1]+0x580)
   if i<5:put(p+0x584,vms[i+1]+0x580)
  for group in range(2):
   chain=[i for i in range(6) if (0 if mode==0 else 1 if mode==2 else i%2)==group]
   put(manager+(0xfe8208 if group==0 else 0xfe8210),vms[chain[0]]+0x570 if chain else 0);put(manager+(0xfe820c if group==0 else 0xfe8214),vms[chain[-1]]+0x570 if chain else 0)
   for k,i in enumerate(chain):put(vms[i]+0x574,vms[chain[k+1]]+0x570 if k+1<len(chain) else 0);put(vms[i]+0x578,vms[chain[k-1]]+0x570 if k else 0)
  states=[]
  for i in order:
   put(stack,base);put(stack+4,vms[i]);m.reg_write(UC_X86_REG_ESP,stack);m.reg_write(UC_X86_REG_ECX,manager);m.emu_start(0x47eb50,base,count=10000);assert m.reg_read(UC_X86_REG_EIP)==base;assert not alive[i];states.append(capture())
  rows.append(dict(order=order,mode=mode,states=states))
 report=dict(executableSha256=hashlib.sha256(img.data).hexdigest(),rows=rows,scope='Whole original47eb50 destructor on six synthetic externally allocated VMs, flattened family containing grandchildren, all720 deletion permutations, ordinary/overlay/mixed registry membership. Actual registry and child unlinking, surviving flags2 and parent pointers; only CRT free boundary controlled to retain freed bytes and record lifetime. No callbacks, geometry storage, native pool recycling, manager update traversal or complete original scene claim.')
 (ROOT/'artifacts/th14/anm-destruction-native.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print('PASS native destruction',len(rows),sum(len(r['states']) for r in rows))
if __name__=='__main__':main()
