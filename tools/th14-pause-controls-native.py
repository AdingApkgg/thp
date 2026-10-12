"""Execute retail4490c0 pause controls. ANM/audio delivery are observed boundaries."""
import hashlib,importlib,json,struct
from pathlib import Path
from unicorn import Uc,UC_ARCH_X86,UC_MODE_32,UC_HOOK_CODE
from unicorn.x86_const import *
ROOT=Path(__file__).resolve().parents[1]
def main():
 img,_,_=importlib.import_module('th-anm-handlers').handlers(14);m=Uc(UC_ARCH_X86,UC_MODE_32)
 for _,b,size,raw,n in img.sections:
  start=b&~4095;m.mem_map(start,((b+size+4095)&~4095)-start);m.mem_write(b,img.data[raw:raw+n])
 base,menu,control,help,stack=0x70000000,0x70001000,0x70010000,0x70020000,0x700ff000;m.mem_map(base,0x100000)
 def put(p,v):m.mem_write(p,struct.pack('<I',v&0xffffffff))
 def get(p):return struct.unpack('<I',m.mem_read(p,4))[0]
 events=[];sounds=[];hidden=[]
 def hook(uc,a,size,data):
  sp=uc.reg_read(UC_X86_REG_ESP);cleanup=0
  if a==0x47f140:events.append([get(sp+4),get(sp+8)]);cleanup=8
  elif a==0x47fb30:
   out,script=get(sp+4),get(sp+8);put(out,1000+script);uc.reg_write(UC_X86_REG_EAX,out);cleanup=8
  elif a==0x46e3d0:sounds.append(get(sp+4));cleanup=8
  elif a in (0x47f560,0x47f520):hidden.append(a==0x47f560)
  elif a==0x437b70:put(0x4db55c,help)
  elif a==0x437c20:put(0x4db55c,0)
  elif a==0x4854a0:pass
  else:return
  uc.reg_write(UC_X86_REG_EIP,get(sp));uc.reg_write(UC_X86_REG_ESP,sp+4+cleanup)
 m.hook_add(UC_HOOK_CODE,hook)
 cases=[]
 for replay in (0,1):
  for continues in (0,1):cases.append(dict(state=1,timer=10,selected=0,pressed=0,replay=replay,continues=continues))
 cases.append(dict(state=2,timer=10,selected=0,pressed=0,replay=0,continues=0))
 for replay in (0,1):
  for selected in range(5):cases.append(dict(state=3,timer=20,selected=selected,pressed=1,replay=replay,continues=0))
 for state in (5,7):
  for selected in (0,1):
   for pressed in (1,2,16,32):cases.append(dict(state=state,timer=31,selected=selected,pressed=pressed,replay=0,continues=0))
 rows=[]
 for case in cases:
  m.mem_write(base,bytes(0xff000));events.clear();sounds.clear();hidden.clear()
  for p,v in ((0x4db558,control),(0x4db55c,help),(control+0x94,case['replay']),(0x4f5838,case['continues']),(menu+4,case['state']),(menu+0x14,case['timer']),(menu+0x38,case['selected']),(menu+0x40,2 if case['state'] in (5,7) else 5),(menu+0x108,1),(menu+0x1e8,100),(menu+0x1ec,200),(0x4d6884,case['pressed']),(0x4d6880,0),(help+0x128,0)):put(p,v)
  put(stack,base);m.reg_write(UC_X86_REG_ESP,stack);m.reg_write(UC_X86_REG_ECX,menu)
  m.emu_start(0x4490c0,base,count=100000);assert m.reg_read(UC_X86_REG_EIP)==base
  rows.append(dict(**case,nextState=get(menu+4),cursor=[get(menu+0x38),get(menu+0x40),get(menu+0x108),get(menu+0x10c)],disabled=[get(menu+0xc8+i*4) for i in range(get(menu+0x10c))],events=events[:],sounds=sounds[:],hidden=hidden[:]))
 result=dict(executableSha256=hashlib.sha256(img.data).hexdigest(),rows=rows,scope='Actual retail4490c0 pause controller, five-choice initialization/disabled entries, selection child-script interrupts, confirm acceptance/cancel/movement. ANM lookup/interrupt sink and sound delivery controlled. Not rendered animation or whole-game equality.')
 (ROOT/'artifacts/th14/pause-controls-native-oct11.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print(f'PASS {len(rows)} retail pause control cases')
if __name__=='__main__':main()
