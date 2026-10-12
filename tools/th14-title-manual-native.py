"""Full retail461d10 title Manual entry/wait/exit with controlled help/ANM services."""
import hashlib,importlib,itertools,json,struct
from pathlib import Path
from unicorn import Uc,UC_ARCH_X86,UC_MODE_32,UC_HOOK_CODE
from unicorn.x86_const import *
ROOT=Path(__file__).resolve().parents[1]
MENU,RESOURCE,HELP,VM,STACK,RETURN=0x70000000,0x70008000,0x70013000,0x70020000,0x7002f000,0x70030000
def main():
 img,_,_=importlib.import_module('th-anm-handlers').handlers(14);m=Uc(UC_ARCH_X86,UC_MODE_32)
 for _,b,size,raw,n in img.sections:
  start=b&~4095;m.mem_map(start,((b+size+4095)&~4095)-start);m.mem_write(b,img.data[raw:raw+n])
 m.mem_map(MENU,0x31000)
 def put(p,v):m.mem_write(p,struct.pack('<I',v&0xffffffff))
 def get(p):return struct.unpack('<I',m.mem_read(p,4))[0]
 bindings=[];labels=[];services=[]
 def boundary(uc,a,size,data):
  sp=uc.reg_read(UC_X86_REG_ESP);cleanup=0
  if a==0x47fcb0:uc.reg_write(UC_X86_REG_EAX,VM)
  elif a==0x40af00:bindings.append([2,get(sp+8)]);cleanup=8
  elif a==0x46fe50:pass
  elif a==0x47e890:
   p=get(sp+4);put(p,119);uc.reg_write(UC_X86_REG_EAX,p);cleanup=8
  elif a==0x458d70:
   script=get(sp+4);bindings.append([24,script]);put(MENU+0x2c8+script*4,100+script);cleanup=4
  elif a==0x437b70:
   services.append('create_help');put(0x4db55c,HELP);put(HELP+0x128,0);uc.reg_write(UC_X86_REG_EAX,HELP)
  elif a==0x437a80:services.append('destroy_help')
  elif a==0x4854fe:services.append('free_help')
  elif a==0x47f140:
   labels.append([get(sp+4),get(sp+8)]);cleanup=8
  else:return
  uc.reg_write(UC_X86_REG_EIP,get(sp));uc.reg_write(UC_X86_REG_ESP,sp+4+cleanup)
 m.hook_add(UC_HOOK_CODE,boundary);rows=[]
 for substate,timer,ascii_present,finished in itertools.product((0,1,2),(0,19,20,99),(0,1),(0,1)):
  m.mem_write(MENU,bytes(0x30000));bindings.clear();labels.clear();services.clear()
  for p,v in ((MENU+0x1c,16),(MENU+0x24,substate),(MENU+0x6dc,119 if ascii_present else 0),(MENU+0x464,203),(MENU+0x2b4,timer-1),(MENU+0x2b8,timer),(MENU+0x2c0,0x4d8f58),(MENU+0x2c4,1),(0x4db520,RESOURCE),(RESOURCE+0x191e4,RESOURCE),(0x4db55c,HELP),(HELP+0x128,finished)):put(p,v)
  m.mem_write(MENU+0x2bc,struct.pack('<f',float(timer)));m.mem_write(0x4f5815,b'\0');put(STACK,RETURN);m.reg_write(UC_X86_REG_ESP,STACK);m.reg_write(UC_X86_REG_ECX,MENU)
  m.emu_start(0x461d10,RETURN,count=100000);assert m.reg_read(UC_X86_REG_EIP)==RETURN
  rows.append(dict(substate=substate,timer=timer,asciiPresent=ascii_present,finished=finished,state=[get(MENU+0x1c),get(MENU+0x24),get(MENU+0x2b8),bool(get(MENU+0x6dc)),bool(get(MENU+0x464))],bindings=bindings[:],labels=labels[:],services=services[:],helpOrigin=get(HELP+0x12c)))
 result=dict(executableSha256=hashlib.sha256(img.data).hexdigest(),rows=rows,scope='Full original461d10 title Manual callback and458c80 state/timer helper, entry ascii19 only if absent plus title103/help factory, wait without exiting before help finished, finished cleanup/return Main and helpOrigin X128. ANM allocate/bind/tick/register, title creation/interrupt, help factory/destructor/free controlled. Help controller437c40 is proved separately; actual resource threads, GPU/font/PNG pixels and cursor history excluded.')
 (ROOT/'artifacts/th14/title-manual-native.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print(f'PASS {len(rows)} retail title Manual entry/wait/exit cases')
if __name__=='__main__':main()
