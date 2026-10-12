"""Whole44d330 movement with controlled ANM lookup/bind/tick/interrupt.

Existing focus handle, eight inactive or active callback-free options. The
native focus allocation branch and nonzero option callbacks are excluded.
"""
import hashlib,importlib,itertools,json,struct
from pathlib import Path
from unicorn import *
from unicorn.x86_const import *
ROOT=Path(__file__).resolve().parents[1]
FIELDS=(0x680,0x184b0,0x182bc,0x678,0x67c,0x604,0x608,0x60c,0x610,0x614,0x618,0x61c,0x620,0x5ec,0x5f0,0x5e0,0x5e4,0x5e8,0x1830c,0x18334)
OPTION=(0,0x54,0x58,0x5c,0x60,0xd4)
def main():
 img,_,_=importlib.import_module('th-anm-handlers').handlers(14);m=Uc(UC_ARCH_X86,UC_MODE_32)
 for _,base,size,raw,n in img.sections:
  first=base&~4095;m.mem_map(first,((base+size+4095)&~4095)-first);m.mem_write(base,img.data[raw:raw+n])
 end,player,enemy,arena,stack=0x70000000,0x70001000,0x70020000,0x70030000,0x700ff000;m.mem_map(end,0x100000)
 put=lambda p,v:m.mem_write(p,struct.pack('<I',v&0xffffffff))
 get=lambda p:struct.unpack('<I',m.mem_read(p,4))[0]
 bits=lambda f:struct.unpack('<I',struct.pack('<f',f))[0]
 events=[]
 def hook(machine,a,size,user):
  sp=m.reg_read(UC_X86_REG_ESP)
  if a==0x47f0a0:m.reg_write(UC_X86_REG_EAX,arena+get(sp+4)*0x1000 if 0<get(sp+4)<=17 else 0)
  elif a==0x40af00:events.append([0,get(sp+8)])
  elif a==0x47f140:
   handle=get(sp+4)
   if 0<handle<=17:put(arena+handle*0x1000+0x4a0,get(sp+8))
  elif a==0x46fe50:m.reg_write(UC_X86_REG_EAX,0)
 for a,n in ((0x47f0a0,4),(0x40af00,8),(0x47f140,8),(0x46fe50,0)):
  m.mem_write(a,b'\xc2'+struct.pack('<H',n) if n else b'\xc3');m.hook_add(UC_HOOK_CODE,hook,begin=a,end=a)
 rows=[]
 for index,(held,env,transition,variant,previous,rate) in enumerate(itertools.product(range(0,256,8),range(3),(0,3,4),range(3),(-100,0,100),(0.,.5,1.,1.5))):
  m.mem_write(player,bytes(0x19000));events.clear()
  for handle in range(1,18):
   vm=arena+handle*0x1000;m.mem_write(vm,bytes(0x600));m.mem_write(vm+0x59c,struct.pack('<fff',91.,-72.,33.));m.mem_write(vm+0x68,struct.pack('<ff',.75,1.25));put(vm+0x4a0,77)
  flags=(0,0x12,0x10)[variant];count=(0,1,4,8)[index%4];active=index%9;clock=(0,29,31)[variant]
  for off,v in ((0x5ec,(-321,-23560,23560)[variant]),(0x5f0,(50319,4000,55350)[variant]),(0x6a4,transition),(0x5f4,576),(0x5f8,256),(0x5fc,407),(0x600,181),(0x678,previous),(0x67c,101),(0x182d4,flags),(0x182bc,(29,30,67)[variant]),(0x1830c,clock),(0x18334,count),(0xd6d8,1),(0x10,arena),(0xd6dc,bits((1.,.5,1.5)[variant])),(0x18308,bits(2.25))):put(player+off,v)
  for off,v in ((0x5e8,5.25),(0x60c,7.25),(0x610,11.25),(0x614,12.5),(0x618,13.75),(0xd6e0,(0.,.125,1.25)[variant]),(0xd6e4,(0.,-.25,-.875)[variant])):put(player+off,bits(v))
  for n in range(66):put(player+0x183a8+n*4,0x10203040+n*101)
  for n in range(8):
   o=player+0xd6ec+n*0xe4
   for off,v in ((0,2 if n<active else 0),(0x54,123),(0x58,456),(0x5c,-300+n*53),(0x60,50000+n*97),(0x64,-2048+n*512),(0x68,-1024+n*256),(0x6c,-512+n*128),(0x70,-3072+n*384),(0xb0,2+n*2),(0xb4,3+n*2),(0xd4,n%2)):
    put(o+off,v)
  put(0x4d6a90,held);put(0x4db544,enemy if env else 0);put(enemy+0xd8,int(env==2));put(0x4d8f58,bits(rate));put(stack,end)
  m.reg_write(UC_X86_REG_ESP,stack);m.reg_write(UC_X86_REG_ECX,player);m.reg_write(UC_X86_REG_MXCSR,0x1f80);m.emu_start(0x44d330,end,count=100000);assert m.reg_read(UC_X86_REG_EIP)==end
  rows.append(dict(held=held,env=env,transition=transition,variant=variant,previous=previous,rate=rate,count=count,active=active,output=[get(player+o) for o in FIELDS],history=[get(player+0x183a8+n*4) for n in range(66)],options=[[get(player+0xd6ec+n*0xe4+o) for o in OPTION] for n in range(8)],focus=bool(get(player+0xd6d8)),body=events[-1][1] if events else 0,animations=[[get(arena+h*0x1000+o) for o in (0x59c,0x5a0,0x5a4,0x68,0x6c,0x4a0)]+[get(arena+h*0x1000+0x18)&8] for h in range(1,18)]))
 (ROOT/'artifacts/th14/player-motion-native.json').write_text(json.dumps(dict(executableSha256=hashlib.sha256(img.data).hexdigest(),rows=rows),separators=(',',':'))+'\n',encoding='utf8');print(f'{len(rows)} full native TH14 movement and eight-option cases')
if __name__=='__main__':main()
