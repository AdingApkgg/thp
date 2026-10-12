"""Retail45fb40 Records controls and460460 spell rows; resource/keyboard services controlled."""
import hashlib,importlib,itertools,json,re,struct
from pathlib import Path
from unicorn import Uc,UC_ARCH_X86,UC_MODE_32,UC_HOOK_CODE
from unicorn.x86_const import *
ROOT=Path(__file__).resolve().parents[1]

def main():
 img,_,_=importlib.import_module('th-anm-handlers').handlers(14);m=Uc(UC_ARCH_X86,UC_MODE_32)
 for _,b,size,raw,n in img.sections:
  start=b&~4095;m.mem_map(start,((b+size+4095)&~4095)-start);m.mem_write(b,img.data[raw:raw+n])
 base,menu,score,sup,resource,vm,out,stack=0x70000000,0x70001000,0x70010000,0x70050000,0x70070000,0x70071000,0x70074000,0x7007f000;m.mem_map(base,0x80000)
 def put(p,v):m.mem_write(p,struct.pack('<I',v&0xffffffff))
 def get(p):return struct.unpack('<I',m.mem_read(p,4))[0]
 def string(p):return bytes(m.mem_read(p,256)).split(b'\0')[0].decode('latin1')
 events=[];requests=[];serial=79;key=-1
 def hook(uc,a,size,data):
  nonlocal serial
  pop=None;sp=uc.reg_read(UC_X86_REG_ESP);this=uc.reg_read(UC_X86_REG_ECX)
  if a==0x458d70:
   script=get(sp+4);put(this+0x2c8+script*4,1000+script);events.append(['create',script]);pop=4
  elif a==0x47fcb0:uc.reg_write(UC_X86_REG_EAX,vm);pop=0
  elif a==0x40af00:events.append(['ascii' if this==resource else 'text',get(sp+8)]);pop=8
  elif a==0x46fe50:pop=0
  elif a==0x47e890:
   put(get(sp+4),serial);serial+=1;uc.reg_write(UC_X86_REG_EAX,get(sp+4));pop=8
  elif a==0x47f0a0:uc.reg_write(UC_X86_REG_EAX,get(sp+4));pop=4
  elif a in (0x47f140,0x47f1b0):events.append(['interrupt',get(sp+4),get(sp+8)]);pop=8
  elif a==0x46e3d0:events.append(['sound',get(sp+4)]);pop=8
  elif a==0x402820:
   m.mem_write(this,bytes(256))
   if key>=0:m.mem_write(this+key,b'\x80')
   uc.reg_write(UC_X86_REG_EAX,1);pop=0
  elif a==0x47dd70:
   fmt=string(get(sp+28));args=sp+32;values=[]
   for match in re.finditer(r'%(?:[-+ #0]*\d*(?:\.\d+)?l?)([ds%])',fmt):
    if match[1]=='%':continue
    values.append(string(get(args)) if match[1]=='s' else struct.unpack('<i',m.mem_read(args,4))[0]);args+=4
   requests.append(dict(handle=get(sp+8),color=get(sp+12),offset=get(sp+16),font=get(sp+20),style=get(sp+24),text=(fmt%tuple(values)).encode('latin1').hex()));pop=0
  if pop is not None:uc.reg_write(UC_X86_REG_EIP,get(sp));uc.reg_write(UC_X86_REG_ESP,sp+4+pop)
 m.hook_add(UC_HOOK_CODE,hook)
 difficulty=list(m.mem_read(0x4d55a0,120));assert difficulty==[(i+2)%4 if i<26 else i%4 if i<108 else 4 for i in range(120)]
 def setup(selection,diff,page,substate,timer=0):
  nonlocal serial,key
  m.mem_write(base,bytes(0x7e000));put(0x4db68c,score);put(0x4db520,sup);put(sup+0x191e4,resource);put(0x4d967c,resource+0x400);put(0x4f56cc,out);put(0x4d8f58,0x3f800000);m.mem_write(0x4f5815,b'\0')
  for off,v in ((0x1c,10),(0x24,substate),(0x28,selection),(0x30,6),(0xf8,1),(0x100,diff),(0x108,5),(0x1d0,1),(0x1d8,page),(0x1e0,(difficulty.count(diff)+9)//10+1),(0x2a8,1),(0x2b4,timer-1),(0x2b8,timer),(0x2bc,0x3f800000),(0x2c0,0x4d8f58),(0x2c4,1)):put(menu+off,v)
  for s in [98,152+selection,158+diff,166,167,168,169,163,164,165,170]:put(menu+0x2c8+s*4,1000+s)
  for r in range(10):put(menu+0x6e0+r*4,2000+r)
  for c in range(7):
   for i in range(120):
    p=score+8+c*0x5298+0x978+i*0x9c;m.mem_write(p,f'Spell {i:03d}'.encode()+b'\x81\x48\0');put(p+0x80,(i+c)%3);put(p+0x88,0 if i%3==0 else 7)
  put(0x4d6884,0);put(0x4d6880,0);put(0x4fd744,0);put(0x4fd740,0);m.mem_write(0x4fda78,bytes(256));events.clear();requests.clear();serial=79;key=-1
 def call(a):
  put(stack,base);m.reg_write(UC_X86_REG_ESP,stack);m.reg_write(UC_X86_REG_ECX,menu);m.emu_start(a,base,count=200000);assert m.reg_read(UC_X86_REG_EIP)==base,hex(m.reg_read(UC_X86_REG_EIP))
 def snapshot():return dict(screen=get(menu+0x1c),substate=get(menu+0x24),selected=get(menu+0x28),difficulty=get(menu+0x100),page=get(menu+0x1d8),pages=get(menu+0x1e0),recordRows=get(menu+0x2b0),progress=get(0x4fd744),timeout=get(0x4fd740),events=events[:],requests=requests[:])
 entries=[]
 for state,timer in ((0,0),(1,6),(1,7),(3,5),(3,6)):
  setup(0,1,0,state,timer)
  if state==0:put(menu+0x6dc,0)
  call(0x45fb40);entries.append(dict(substate=state,timer=timer,result=snapshot()))
 controls=[];text=[]
 for selection,diff in itertools.product(range(6),range(5)):
  count=(difficulty.count(diff)+9)//10+1
  for page in range(count):
   if page:
    setup(selection,diff,page,2,17);call(0x460460);text.append(dict(selection=selection,difficulty=diff,page=page,result=snapshot()))
   for pressed,repeat in ((16,0),(32,0),(64,0),(128,0),(1,0),(2,0),(0,16),(0,128)):
    setup(selection,diff,page,2,17);put(0x4d6884,pressed);put(0x4d6880,repeat);call(0x45fb40);controls.append(dict(selection=selection,difficulty=diff,page=page,pressed=pressed,repeat=repeat,result=snapshot()))
 unlock=[]
 for progress,timeout,key_value,pressed in itertools.product((0,1,8,9),(0,299,300),(-1,24,19,1),(0,1)):
  setup(4,4,0,2,17);put(0x4fd744,progress);put(0x4fd740,timeout);put(0x4d6884,pressed);key=key_value
  for i in range(120):put(score+0x1f910+i*0x9c+0x88,(0,99998,99999,0x7fffffff,0xffffffff)[i%5])
  for c in range(6):put(score+8+c*0x5298+0x7dc,(0,0x7fffffff,0xffffffff)[c%3])
  call(0x45fb40);unlock.append(dict(progress=progress,timeout=timeout,key=key_value,pressed=pressed,result=snapshot(),score=bytes(m.mem_read(score+8,7*0x5298)).hex(),settings=bytes(m.mem_read(score+0x24230,0x42c)).hex()))
 result=dict(passed=True,executableSha256=hashlib.sha256(img.data).hexdigest(),difficulty=difficulty,entries=entries,controls=controls,text=text,unlock=unlock,scope='Actual retail45fb40 Records callback and460460 spell-row formatting; real cursor/timer/page/hidden-code logic and459300 score writes. ANM factories/bind/lookup/interrupt, font text queue/CRT formatting and keyboard supplier controlled. Tests the TH14 nine-key hidden code only in volatile fixtures, never user saves; GPU/text rasterization and full native menus excluded.')
 (ROOT/'artifacts/th14/records-native.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print(f'PASS {len(entries)} boundaries, {len(controls)} controls, {len(text)} spell pages, {len(unlock)} hidden-code boundaries')
if __name__=='__main__':main()
