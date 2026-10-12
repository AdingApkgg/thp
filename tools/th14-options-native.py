"""Retail 44f970, with only ANM allocation/binding/lookup/interrupt boundaries."""
import hashlib,importlib,itertools,json,struct
from pathlib import Path
from unicorn import Uc,UC_ARCH_X86,UC_MODE_32,UC_HOOK_CODE
from unicorn.x86_const import *
ROOT=Path(__file__).resolve().parents[1]
def main():
 img,_,_=importlib.import_module('th-anm-handlers').handlers(14)
 m=Uc(UC_ARCH_X86,UC_MODE_32)
 for _,base,size,raw,n in img.sections:
  begin=base&~4095;m.mem_map(begin,((base+size+4095)&~4095)-begin);m.mem_write(base,img.data[raw:raw+n])
 ret,player,sht,arena,stack=0x70000000,0x70001000,0x70020000,0x70030000,0x700ff000;m.mem_map(ret,0x100000)
 put=lambda p,v:m.mem_write(p,struct.pack('<I',v&0xffffffff));get=lambda p:struct.unpack('<I',m.mem_read(p,4))[0]
 events=[];vms={};next_id=0;pending=0
 def allocate(script):
  nonlocal next_id
  next_id+=1;v=arena+next_id*0x1000;vms[next_id]=v;put(v+0x24,14);events.append(['create',script]);return v,next_id
 def hook(machine,a,size,user):
  nonlocal pending
  sp=m.reg_read(UC_X86_REG_ESP)
  if a==0x47fcb0:
   pending,_=allocate(-1);m.reg_write(UC_X86_REG_EAX,pending)
  elif a==0x40af00:events[-1][1]=get(sp+8)
  elif a==0x42df70:
   out,script=get(sp+4),get(sp+8);v,i=allocate(script);put(v+0x1c,0x20200);put(out,i);m.reg_write(UC_X86_REG_EAX,out)
  elif a==0x47e890:
   out=get(sp+4);put(out,next_id);m.reg_write(UC_X86_REG_EAX,out)
  elif a==0x47f0a0:m.reg_write(UC_X86_REG_EAX,vms.get(get(sp+4),0))
  elif a==0x47f140:events.append(['interrupt',get(sp+4),get(sp+8)])
  elif a==0x46fe50:m.reg_write(UC_X86_REG_EAX,0)
 for a,n in ((0x47fcb0,0),(0x40af00,8),(0x42df70,16),(0x47e890,8),(0x47f0a0,4),(0x47f140,8),(0x46fe50,0)):
  m.mem_write(a,b'\xc2'+struct.pack('<H',n) if n else b'\xc3');m.hook_add(UC_HOOK_CODE,hook,begin=a,end=a)
 rows=[];resources={}
 for slot in range(6):
  path=ROOT/f'artifacts/archive-differential/th14-bBPoO0/pl{slot//2:02}{"ab"[slot%2]}.sht';data=path.read_bytes();resources[path.name]=hashlib.sha256(data).hexdigest();m.mem_write(sht,data)
  for old_count,power,focus in itertools.product((0,1,4),(0,39,40,80,120,159,160),(0,1)):
   m.mem_write(player,bytes(0x19000));m.mem_write(arena,bytes(0x20000));events.clear();vms.clear();next_id=0;pending=0
   put(player+0x688,sht);put(player+0x10,ret);put(player+0x5ec,-321);put(player+0x5f0,50319);put(player+0x18334,old_count);put(player+0x183a4,0x3f800000);put(player+0x184b0,focus)
   for off,v in ((0x4f5828,slot//2),(0x4f582c,slot%2),(0x4f5858,power),(0x4f585c,160),(0x4f5860,40)):put(off,v)
   put(stack,ret);m.reg_write(UC_X86_REG_ESP,stack);m.reg_write(UC_X86_REG_ECX,player);m.reg_write(UC_X86_REG_MXCSR,0x1f80)
   try:m.emu_start(0x44f970,ret,count=100000)
   except Exception as e:raise RuntimeError(f'{slot,old_count,power,focus}: pc {m.reg_read(UC_X86_REG_EIP):x}') from e
   assert m.reg_read(UC_X86_REG_EIP)==ret
   opts=[]
   for i in range(8):
    o=player+0xd6ec+i*0xe4;opts.append([get(o+k) for k in (0,0x54,0x58,0x5c,0x60,0x64,0x68,0x6c,0x70,0xd0,0xd4)])
   rows.append(dict(slot=slot,oldCount=old_count,power=power,focus=focus,result=[get(player+0x18334),get(player+0x183a4)],options=opts,events=events[:],animations=[[get(v+0x1c),get(v+0x24),get(v+0x5a0)] for v in vms.values()]))
 out=ROOT/'artifacts/th14/options-native.json';out.write_text(json.dumps(dict(executableSha256=hashlib.sha256(img.data).hexdigest(),resources=resources,rows=rows),indent=2)+'\n',encoding='utf8');print(f'{len(rows)} retail option rebuild cases.')
if __name__=='__main__':main()
