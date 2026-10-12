"""Complete retail 4440e0, with ANM allocation/binding/tick/registry boundaries.

Original nine SHTs, all four characters and five seasons. Existing animation
families are empty; nonzero option fields expose the seasonal main-array alias.
"""
import hashlib,importlib,itertools,json,struct
from pathlib import Path
from unicorn import Uc,UC_ARCH_X86,UC_MODE_32,UC_HOOK_CODE
from unicorn.x86_const import *
ROOT=Path(__file__).resolve().parents[1]

def main():
 img,_,_=importlib.import_module('th-anm-handlers').handlers(16)
 m=Uc(UC_ARCH_X86,UC_MODE_32)
 for _,base,size,raw,n in img.sections:
  begin=base&~4095;m.mem_map(begin,((base+size+4095)&~4095)-begin);m.mem_write(base,img.data[raw:raw+n])
 ret,player,sht,sub,arena,stack=0x70000000,0x70001000,0x70040000,0x70042000,0x70050000,0x701ff000
 m.mem_map(ret,0x200000)
 put=lambda p,v:m.mem_write(p,struct.pack('<I',v&0xffffffff))
 get=lambda p:struct.unpack('<I',m.mem_read(p,4))[0]
 events=[];vms={};next_id=0
 def allocate(script):
  nonlocal next_id
  next_id+=1;v=arena+next_id*0x1000;vms[next_id]=v;m.mem_write(v,bytes(0x600));put(v+0x18,14);events.append([script,0,0]);return v,next_id
 def hook(machine,a,size,user):
  sp=m.reg_read(UC_X86_REG_ESP)
  if a==0x46f600:v,_=allocate(-1);m.reg_write(UC_X86_REG_EAX,v)
  elif a==0x407b20:events[-1][0]=get(sp+8)
  elif a==0x426160:
   out,script,layer=get(sp+4),get(sp+8),get(sp+12);v,i=allocate(script)
   # Own helper's initialization is a controlled boundary here.
   put(v+0x534,0x400);put(out,i);m.reg_write(UC_X86_REG_EAX,out);events[-1][1]=0x400;events[-1][2]=layer
  elif a==0x46e7d0:
   out=get(sp+4);put(out,next_id);m.reg_write(UC_X86_REG_EAX,out)
  elif a==0x46efa0:m.reg_write(UC_X86_REG_EAX,vms.get(get(sp+4),0))
  elif a==0x45f980:
   v=m.reg_read(UC_X86_REG_ECX);events[-1][1]=get(v+0x534);events[-1][2]=get(v+0x18);m.reg_write(UC_X86_REG_EAX,0)
 for a,n in ((0x46f600,0),(0x407b20,8),(0x426160,16),(0x46e7d0,8),(0x46efa0,4),(0x46f0b0,8),(0x45f980,0)):
  m.mem_write(a,b'\xc2'+struct.pack('<H',n) if n else b'\xc3');m.hook_add(UC_HOOK_CODE,hook,begin=a,end=a)
 # These globals are runtime-initialized by 43deb0, not stored in the PE.
 for i,v in enumerate((100,230,390,590,840,1140)):put(0x4a583c+i*4,v)
 rows=[];resources={};names=('pl00','pl02','pl03','pl01');seasons=('pl00sub','pl02sub','pl03sub','pl01sub','pl04sub')
 for character,season in itertools.product(range(4),range(5)):
  for dest,name in ((sht,names[character]),(sub,seasons[season])):
   path=ROOT/f'artifacts/th16/options-corpus/{name}.sht';data=path.read_bytes();resources[path.name]=hashlib.sha256(data).hexdigest();m.mem_write(dest,data)
  for old,power,points,focus in itertools.product(((0,0),(1,2),(4,6)),(0,99,100,200,399,400),(0,99,100,229,230,389,390,589,590,839,840,1139,1140),(0,1)):
   m.mem_write(player,bytes(0x30000));events.clear();vms.clear();next_id=0
   for off,val in ((0xc,ret),(0x10,ret),(0x2c788,sht),(0x2c78c,sub),(0x61c,-321),(0x620,50319),(0x165c8,focus),(0x165f4,old[0]),(0x1669c,old[1])):put(player+off,val)
   for i in range(12):
    o=player+0x660+i*0xe4
    for k in (0,0x54,0x58,0x5c,0x60,0x64,0x68,0x6c,0x70,0xd0,0xd4):put(o+k,17+i*31+k)
   for off,val in ((0x4a6ef8,player),(0x4a57a4,character),(0x4a57a8,0),(0x4a57ac,season),(0x4a57e4,power),(0x4a57e8,400),(0x4a57ec,100),(0x4a5808,points)):put(off,val)
   put(stack,ret);m.reg_write(UC_X86_REG_ESP,stack);m.reg_write(UC_X86_REG_ECX,player+0x610);m.reg_write(UC_X86_REG_MXCSR,0x1f80)
   m.emu_start(0x4440e0,ret,count=100000);assert m.reg_read(UC_X86_REG_EIP)==ret
   opts=[[get(player+0x660+i*0xe4+k) for k in (0,0x54,0x58,0x5c,0x60,0x64,0x68,0x6c,0x70,0xd0,0xd4)] for i in range(12)]
   rows.append(dict(character=character,season=season,old=old,power=power,points=points,focus=focus,result=[get(player+0x165f4),get(player+0x16698),get(player+0x1669c)],options=opts,events=events[:],animations=[[get(v+0x534),get(v+0x18),get(v+0x5e4)] for v in vms.values()]))
 out=ROOT/'artifacts/th16/options-native.json';out.write_text(json.dumps(dict(executableSha256=hashlib.sha256(img.data).hexdigest(),resources=resources,rows=rows),separators=(',',':'))+'\n',encoding='utf8');print(f'{len(rows)} retail TH16 option rebuild cases.')
if __name__=='__main__':main()
