"""Complete own43e5f0/43f980 score entry and high-score name branches."""
import hashlib,importlib,itertools,json,struct
from pathlib import Path
from unicorn import *
from unicorn.x86_const import *
ROOT=Path(__file__).resolve().parents[1]
def main():
 img,_,_=importlib.import_module('th-anm-handlers').handlers(16);m=Uc(UC_ARCH_X86,UC_MODE_32)
 for _,b,size,raw,n in img.sections:
  start=b&~4095;m.mem_map(start,((b+size+4095)&~4095)-start);m.mem_write(b,img.data[raw:raw+n])
 m.mem_map(0x70000000,0x80000);menu,control,hud,replay,bank,stack,ret=(0x70000000+n for n in (0x1000,0x5000,0x6000,0x7000,0x30000,0x7d000,0x7e000))
 def put(p,v):m.mem_write(p,struct.pack('<I',v&0xffffffff))
 def get(p):return struct.unpack('<I',m.mem_read(p,4))[0]
 def bits(v):return struct.unpack('<I',struct.pack('<f',v))[0]
 sounds=[];pending=[0,4];bindings=[];keys=0
 def boundary(machine,a,size,user):
  sp=machine.reg_read(UC_X86_REG_ESP)
  if a==0x46f0b0:
   id_=get(sp+4)
   if id_ in (100,200):pending[0 if id_==100 else 1]=get(sp+8)
  elif a==0x46f130:pending[0]=0 # Immediate ANM update controlled.
  elif a==0x46f5a0:put(get(sp+4),0);machine.reg_write(UC_X86_REG_EAX,get(sp+4))
  elif a==0x418fe0:
   bindings.append(get(sp+8));put(get(sp+4),100);pending[0]=4;machine.reg_write(UC_X86_REG_EAX,get(sp+4))
  elif a==0x45e150:sounds.append(get(sp+4))
  elif a==0x4186f0:machine.reg_write(UC_X86_REG_EAX,int(bool(keys&get(sp+4))))
  elif a==0x47a09e:machine.mem_write(get(sp+4),struct.pack('<Q',0x123456789abcdef0))
 for a,cleanup in ((0x46f0b0,8),(0x46f130,8),(0x46f5a0,12),(0x418fe0,12),(0x46f340,0),(0x45e150,8),(0x4186f0,4),(0x47a09e,0),(0x47499b,0)):
  m.mem_write(a,b'\xc2'+struct.pack('<H',cleanup) if cleanup else b'\xc3');m.hook_add(UC_HOOK_CODE,boundary,begin=a,end=a)
 initial=bytes.fromhex(json.loads((ROOT/'artifacts/th16/score-native.json').read_text())['initial']);inputs=[]
 for selection,difficulty,score,continues,remaining,clock,rate,last in itertools.product((0,4),(0,5),(9999,10000,50000,100000,0x80000000),(0,1),(0,1),(9,10,11),(.5,1.25),(0,1)):
  inputs.append((selection,difficulty,score,continues,remaining,2,clock,rate,last,0,0,0,0))
 for selected,length,pressed,repeat,clock,rate in itertools.product((0,12,13,87,88,89,90),(0,1,7,8),(0,1,2,256,16,32,64,128,0x101),(0,16,128),(9,10),(.5,1.25)):
  inputs.append((0,0,50000,0,1,15,clock,rate,0,selected,length,pressed,repeat))
 cases=[]
 for selection,difficulty,score,continues,remaining,sub,clock,rate,last,selected,length,pressed,repeat in inputs:
  m.mem_write(menu,bytes(0x800));m.mem_write(bank,bytes(0x1a3ac));pending[:]=[0,4];sounds.clear();bindings.clear();keys=pressed|repeat
  for n in range(5):m.mem_write(bank+8+n*0x5318,initial)
  last_name=b'AB      \0' if last else b'        \0';m.mem_write(bank+0x19f8c,last_name);m.mem_write(replay+0x20,struct.pack('<dd',1,1))
  for p,v in ((0x4a6dd4,control),(0x4a6dcc,hud),(0x4a6dc8,replay),(0x4a6f0c,bank),(0x4a57b8,continues),(0x4a57a4,selection),(0x4a57a8,0),(0x4a57ac,0),(0x4a57b4,difficulty),(0x4a57b0,score),(0x4a5790,1),(0x4a59b8,100000),(0x4a5bec,0),(0x4a5bfc,remaining),(control+0xac,0),(0x4a50bc,pressed),(0x4a5788,bits(rate)),(0x490eb0,0x4a5788),(menu+0x1ec,2),(menu+0x1f4,sub),(menu+0x1e4,0),(menu+0x1e8,200),(menu+0x3c,5),(menu+0x104,1)):put(p,v)
  if sub==15:
   for p,v in ((menu+0x34,2),(menu+0x38,2),(menu+0x3c,25),(menu+0x10c,selected),(menu+0x110,selected),(menu+0x114,91),(menu+0x1dc,1),(menu+0x1f8,length)):put(p,v)
   m.mem_write(menu+0x2d4,b'ABCDEFGH'[:length]+b' '*(8-length)+b'\0')
  for off in (0xc,0x20):
   for n,v in enumerate((clock-1,clock,bits(clock),0,1)):put(menu+off+n*4,v)
  put(stack,ret);m.reg_write(UC_X86_REG_ESP,stack);m.reg_write(UC_X86_REG_ECX,menu);m.emu_start(0x43e5f0,ret,count=30000);assert m.reg_read(UC_X86_REG_EIP)==ret
  output=[get(menu+o) for o in (0x1ec,0x1f4,0xc,0x10,0x14,0x1c,0x20,0x24,0x28,0x30,0x34,0x38,0x3c,0x104,0x108)]+[get(menu+0xc4+n*4) for n in range(16)]+[get(menu+o) for o in (0x10c,0x110,0x114,0x1dc,0x1f8,0x200)]+list(m.mem_read(menu+0x2d4,9))+pending
  rows=bytes(m.mem_read(bank+8+selection*0x5318+0x10,60*32)).hex()
  cases.append(dict(selection=selection,difficulty=difficulty,score=score,continues=continues,remaining=remaining,sub=sub,clock=clock,rate=rate,last=last,selected=selected,length=length,pressed=pressed,repeat=repeat,output=output,sounds=list(sounds),bindings=list(bindings),rows=rows,lastName=list(m.mem_read(bank+0x19f8c,9))))
 (ROOT/'artifacts/th16/gameover-update-native.json').write_text(json.dumps(dict(executableSha256=hashlib.sha256(img.data).hexdigest(),cases=cases),separators=(',',':'))+'\n',encoding='utf-8');print(f'{len(cases)} own TH16 game-over score/name updates')
if __name__=='__main__':main()
