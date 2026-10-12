"""Own43e5f0/43f980 finite pause initialization, navigation/resume and end wait."""
import hashlib,importlib,itertools,json,struct
from pathlib import Path
from unicorn import *
from unicorn.x86_const import *
ROOT=Path(__file__).resolve().parents[1]
def main():
 img,_,_=importlib.import_module('th-anm-handlers').handlers(16);m=Uc(UC_ARCH_X86,UC_MODE_32)
 for _,b,size,raw,n in img.sections:
  start=b&~4095;m.mem_map(start,((b+size+4095)&~4095)-start);m.mem_write(b,img.data[raw:raw+n])
 m.mem_map(0x70000000,0x30000);menu,control,hud,stack,ret=(0x70000000+n for n in (0x1000,0x5000,0x6000,0x2d000,0x2e000))
 def put(p,v):m.mem_write(p,struct.pack('<I',v&0xffffffff))
 def get(p):return struct.unpack('<I',m.mem_read(p,4))[0]
 def bits(v):return struct.unpack('<I',struct.pack('<f',v))[0]
 sounds=[];pending=[3,4];resumed=False;keys=0
 def boundary(machine,a,size,user):
  nonlocal resumed
  sp=machine.reg_read(UC_X86_REG_ESP)
  if a==0x46f0b0:
   id_=get(sp+4)
   if id_ in (100,200):pending[0 if id_==100 else 1]=get(sp+8)
  elif a==0x46f5a0:put(get(sp+4),0);machine.reg_write(UC_X86_REG_EAX,get(sp+4))
  elif a==0x45e150:sounds.append(get(sp+4))
  elif a==0x4186f0:machine.reg_write(UC_X86_REG_EAX,int(bool(keys&get(sp+4))))
  elif a==0x43f6a0:resumed=True
  elif a==0x43f740:pending[:]=[1,1]
  elif a==0x46f1c0:
   id_=get(sp+4)
   if id_ in (100,200):pending[0 if id_==100 else 1]=0
 for a,cleanup in ((0x46f0b0,8),(0x46f5a0,12),(0x46f1c0,4),(0x45e150,8),(0x4186f0,4),(0x43f6a0,0),(0x43f740,0),(0x440bd0,0),(0x45ed00,12),(0x47499b,0)):
  m.mem_write(a,b'\xc2'+struct.pack('<H',cleanup) if cleanup else b'\xc3');m.hook_add(UC_HOOK_CODE,boundary,begin=a,end=a)
 inputs=[]
 for sub,clock,replay,continues,rate in itertools.product((0,1),(0,9,10,11),(0,1),(0,1),(.5,1,1.25)):inputs.append((1,sub,clock,replay,continues,rate,0,0,0))
 for sub,clock,rate in itertools.product((2,3,4,5),(0,8,9),(.5,1,1.25)):inputs.append((2,sub,clock,0,0,rate,0,0,0))
 for selected,pressed,repeat,rate in itertools.product((0,1,4),(0,16,32,256),(0,16,32),(.5,1,1.25)):
  if pressed==256 or pressed in (16,32) or repeat:inputs.append((1,6,12,0,0,rate,selected,pressed,repeat))
 for pressed,rate in itertools.product((1,0x80000),(.5,1,1.25)):inputs.append((1,6,12,0,0,rate,0,pressed,0))
 for clock,rate in itertools.product((0,11,12,13),(.5,1,1.25)):inputs.append((1,16,clock,0,0,rate,0,0,0))
 for selected,pressed,replay,rate in itertools.product((1,4),(1,0x80000),(0,1),(.5,1,1.25)):inputs.append((1,6,12,replay,0,rate,selected,pressed,0))
 for pressed,rate in itertools.product((0x200000,0x10000,0x200100,0x10001),(.5,1,1.25)):inputs.append((1,6,12,0,0,rate,0,pressed,0))
 for sub,clock,selected,pressed,repeat,continues,rate in itertools.product((7,9),(19,20,21,29,30,31),(0,1),(0,1,2,16,32,256),(0,16,32),(0,1),(.5,1,1.25)):
  inputs.append((1,sub,clock,0,continues,rate,selected,pressed,repeat))
 for clock,selected,continues,rate in itertools.product((0,19,20,21),(0,1),(0,1),(.5,1,1.25)):inputs.append((1,8,clock,0,continues,rate,selected,0,0))
 for clock,selected,replay,rate in itertools.product((11,12,13),(1,4),(0,1),(.5,1,1.25)):inputs.append((1,16,clock,replay,0,rate,selected,0,0))
 for clock,selected,rate in itertools.product((11,12,13),(1,4),(.5,1,1.25)):inputs.append((2,16,clock,0,0,rate,selected,0,0))
 cases=[]
 def invalid(machine,access,address,size,value,user):
  print('unmapped',hex(machine.reg_read(UC_X86_REG_EIP)),hex(address),len(cases),kind,sub,clock,selected,pressed,repeat);return False
 m.hook_add(UC_HOOK_MEM_INVALID,invalid)
 for kind,sub,clock,replay,continues,rate,selected,pressed,repeat in inputs:
  m.mem_write(menu,bytes(0x800));pending[:]=[3,4];sounds.clear();resumed=False;keys=pressed|repeat
  for p,v in ((0x4a6dd4,control),(0x4a6dcc,hud),(0x4a57b8,continues),(control+0xac,replay),(0x4a50bc,pressed),(0x4a5788,bits(rate)),(0x490eb0,0x4a5788),(menu+0x1ec,kind),(menu+0x1f4,sub),(menu+0x1e4,100),(menu+0x1e8,200),(menu+0x34,selected),(menu+0x38,selected),(menu+0x3c,5),(menu+0x104,1),(menu+0x204,0),(0x4c17c4,0),(0x4c1800,0)):put(p,v)
  if sub==8 or sub in (7,9) and clock>20:
   for p,v in ((menu+0x3c,2),(menu+0xc0,1),(menu+0x40,4),(menu+0x80,5)):put(p,v)
  for off in (0xc,0x20):
   for n,v in enumerate((clock-1,clock,bits(clock),0,1)):put(menu+off+n*4,v)
  put(stack,ret);m.reg_write(UC_X86_REG_ESP,stack);m.reg_write(UC_X86_REG_ECX,menu);m.emu_start(0x43e5f0,ret,count=20000);assert m.reg_read(UC_X86_REG_EIP)==ret
  output=[get(menu+o) for o in (0x1ec,0x1f4,0xc,0x10,0x14,0x1c,0x20,0x24,0x28,0x30,0x34,0x38,0x3c,0x104,0x108)]+[get(menu+0xc4+n*4) for n in range(16)]+pending+[int(resumed)]
  output += [get(menu+0xc0)]+[get(menu+0x40+n*4) for n in range(16)]+[get(menu+0x80+n*4) for n in range(16)]
  action=0
  if get(menu+0x1ec)==0:action=1 if resumed and selected==0 else 2 if get(0x4c17c4) in (2,4) else 3 if get(0x4c17c4) in (10,11) else 0
  output.append(action)
  cases.append(dict(kind=kind,sub=sub,clock=clock,replay=replay,continues=continues,rate=rate,selected=selected,pressed=pressed,repeat=repeat,output=output,sounds=list(sounds)))
 (ROOT/'artifacts/th16/pause-update-native.json').write_text(json.dumps(dict(executableSha256=hashlib.sha256(img.data).hexdigest(),cases=cases),separators=(',',':'))+'\n',encoding='utf-8');print(f'{len(cases)} own pause update cases')
if __name__=='__main__':main()
