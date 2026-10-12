"""Retail45e710/45eb90 practice menu state and draw with controlled services."""
import hashlib,importlib,itertools,json,re,struct
from pathlib import Path
from unicorn import Uc,UC_ARCH_X86,UC_MODE_32,UC_HOOK_CODE
from unicorn.x86_const import *
ROOT=Path(__file__).resolve().parents[1]
def main():
 img,_,_=importlib.import_module('th-anm-handlers').handlers(14);m=Uc(UC_ARCH_X86,UC_MODE_32)
 for _,b,size,raw,n in img.sections:
  start=b&~4095;m.mem_map(start,((b+size+4095)&~4095)-start);m.mem_write(b,img.data[raw:raw+n])
 base,menu,score,sup,stack=0x70000000,0x70001000,0x70010000,0x70050000,0x700ff000;m.mem_map(base,0x100000)
 def put(p,v):m.mem_write(p,struct.pack('<I',v&0xffffffff))
 def get(p):return struct.unpack('<I',m.mem_read(p,4))[0]
 def flt(p):return struct.unpack('<f',m.mem_read(p,4))[0]
 def string(p):return bytes(m.mem_read(p,255)).split(b'\0')[0].decode('latin1')
 events=[];requests=[]
 def hook(uc,a,size,data):
  sp=uc.reg_read(UC_X86_REG_ESP);this=uc.reg_read(UC_X86_REG_ECX);pop=None
  if a==0x458d70:
   script=get(sp+4);put(this+0x2c8+script*4,1000+script);events.append(['create',script]);pop=4
  elif a==0x46e3d0:events.append(['sound',get(sp+4)]);pop=8
  elif a==0x46ef90:events.append(['audio',get(sp+4),get(sp+8)]);pop=12
  elif a==0x402820:uc.reg_write(UC_X86_REG_EAX,0);pop=0
  elif a==0x420d20:events.append(['loading']);pop=0
  elif a==0x41eea0:put(get(sp+4),79);uc.reg_write(UC_X86_REG_EAX,get(sp+4));events.append(['fade']);pop=16
  elif a==0x47f140:events.append(['interrupt',get(sp+4),get(sp+8)]);pop=8
  elif a==0x40bb10:
   p=get(sp+8);fmt=string(get(sp+12));args=sp+16;values=[]
   for match in re.finditer(r'%(?:[-+ #0]*\d*(?:\.\d+)?)([ds%])',fmt):
    if match[1]=='%':continue
    values.append(string(get(args)) if match[1]=='s' else struct.unpack('<i',m.mem_read(args,4))[0]);args+=4
   text=fmt%tuple(values);requests.append(dict(text=text.encode('latin1').hex(),position=[flt(p+i*4) for i in range(3)],color=get(sup+0x191b0),shadow=get(sup+0x191c4),font=get(sup+0x191c8),scale=[flt(sup+0x191b4),flt(sup+0x191b8)]));pop=0
  if pop is not None:uc.reg_write(UC_X86_REG_EIP,get(sp));uc.reg_write(UC_X86_REG_ESP,sp+4+pop)
 m.hook_add(UC_HOOK_CODE,hook)
 def setup(selection,difficulty,state,timer,selected=0,mask=0,last=2,numbers=0):
  m.mem_write(base,bytes(0xfe000));put(0x4db520,sup);put(0x4db68c,score);put(0x4d8f58,0x3f800000);put(0x4f5828,selection>>1);put(0x4f582c,selection&1);put(0x4f5834,difficulty);put(0x4d5ff4,last);put(0x4f58c4,4);put(0x4f58a4,1);put(0x4db6a0,4)
  m.mem_write(0x4fd748,bytes(256));m.mem_write(0x4f5815,b'\0');put(0x4d6884,0);put(0x4d6880,0);put(0x4f56cc,sup+0x1a000)
  for n in range(9):m.mem_write(0x4fd779+n,bytes([128 if numbers&(1<<n) else 0]))
  for off,v in ((0x1c,8),(0x24,state),(0x28,selected),(0x30,6),(0x34,1),(0x74,2),(0xb4,1),(0xf8,1),(0x2b4,timer-1),(0x2b8,timer),(0x2bc,0x3f800000),(0x2c0,0x4d8f58),(0x2c4,1),(0x460,1102)):put(menu+off,v)
  character=score+8+selection*0x5298
  for n in range(6):
   index=n+1+difficulty*8;put(character+0x7f0+index*8,(0,2345678,0x7fffffff,0x80000000)[n%4]);m.mem_write(character+0x7f4+1+index*8,bytes([(mask>>n)&1]))
  put(sup+0x191b0,0xffffffff);m.mem_write(sup+0x191b4,struct.pack('<2f',1,1));events.clear();requests.clear()
 def call(address):
  put(stack,base);m.reg_write(UC_X86_REG_ESP,stack);m.reg_write(UC_X86_REG_ECX,menu);m.emu_start(address,base,count=1000000);assert m.reg_read(UC_X86_REG_EIP)==base,hex(m.reg_read(UC_X86_REG_EIP))
 def snap():return dict(screen=get(menu+0x1c),substate=get(menu+0x24),selected=get(menu+0x28),count=get(menu+0x30),depth=get(menu+0xb4),last=get(0x4d5ff4),numbers=get(0x4f58c4),stage=get(0x4f58a4),events=events[:])
 entries=[]
 for last in range(6):
  setup(0,1,0,0,last=last);call(0x45e710);entries.append(dict(last=last,result=snap()))
 controls=[]
 for selection,difficulty,selected,mask,pressed in itertools.product(range(6),range(4),range(6),(0,21,63),(0,16,32,1,2,16|1,32|1)):
  setup(selection,difficulty,2,17,selected,mask);put(0x4d6884,pressed);call(0x45e710);controls.append(dict(selection=selection,difficulty=difficulty,selected=selected,mask=mask,pressed=pressed,result=snap()))
 numbers=[]
 for keys in [0,*[1<<n for n in range(9)],511,6,384]:
  setup(0,1,2,17,0,63,numbers=keys);put(0x4d6884,1);call(0x45e710);numbers.append(dict(keys=keys,result=snap()))
 boundaries=[]
 for state,timer,selected in itertools.product((1,3,4),(5,6,10,11,39,40),(0,5)):
  setup(0,1,state,timer,selected,63);call(0x45e710);boundaries.append(dict(state=state,timer=timer,selected=selected,result=snap()))
 layouts=[]
 for selection,difficulty,state,timer,selected,mask in itertools.product(range(6),range(4),(2,3),(0,9,10,14),(0,5),(0,21,63)):
  setup(selection,difficulty,state,timer,selected,mask);call(0x45eb90);layouts.append(dict(selection=selection,difficulty=difficulty,state=state,timer=timer,selected=selected,mask=mask,requests=requests[:]))
 result=dict(passed=True,executableSha256=hashlib.sha256(img.data).hexdigest(),entries=entries,controls=controls,numbers=numbers,boundaries=boundaries,layouts=layouts,scope='Actual full retail45e710/45eb90; six remembered stages, six loadouts/four normal difficulties, all stage cursors and unavailable/sparse/full practice flags, real cursor/history/timer helpers, numeric keyboard selection and fade/loading boundaries, six score rows with signed limits. ANM/audio/Loading/input-device detection/CRT/ASCII sink controlled; keyboard backend only, no controller/GPU/whole practice gameplay equivalence.')
 (ROOT/'artifacts/th14/title-practice-native.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print(f'PASS {len(entries)} entries, {len(controls)} inputs, {len(numbers)} number masks, {len(boundaries)} boundaries, {len(layouts)} text layouts')
if __name__=='__main__':main()

