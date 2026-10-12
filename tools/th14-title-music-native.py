"""Actual461ee0 Music Room callback; ANM/text/audio/archive services controlled."""
import hashlib,importlib,itertools,json,re,struct
from pathlib import Path
from unicorn import Uc,UC_ARCH_X86,UC_MODE_32,UC_HOOK_CODE
from unicorn.x86_const import *
ROOT=Path(__file__).resolve().parents[1]

def main():
 img,_,_=importlib.import_module('th-anm-handlers').handlers(14);m=Uc(UC_ARCH_X86,UC_MODE_32)
 for _,b,size,raw,n in img.sections:
  start=b&~4095;m.mem_map(start,((b+size+4095)&~4095)-start);m.mem_write(b,img.data[raw:raw+n])
 base,menu,score,sup,title,ascii,text,vm_start,cmt,stack=0x70000000,0x70001000,0x70010000,0x70050000,0x70070000,0x70071000,0x70072000,0x70080000,0x700a0000,0x700ff000;m.mem_map(base,0x100000)
 data=(ROOT/'artifacts/archive-differential/th14-ppPprY/musiccmt.txt').read_bytes();lines=data.replace(b'\r',b'').split(b'\n');entries=[]
 for i,line in enumerate(lines):
  if line.startswith(b'@'):entries.append(dict(path=line[1:].decode('latin1'),title=lines[i+1].hex(),comments=[s.hex() for s in lines[i+2:i+10]]))
 def put(p,v):m.mem_write(p,struct.pack('<I',v&0xffffffff))
 def get(p):return struct.unpack('<I',m.mem_read(p,4))[0]
 def string(p):return bytes(m.mem_read(p,256)).split(b'\0')[0].decode('latin1')
 events=[];requests=[];positions=[];next_vm=vm_start;bound=0
 def fresh():
  nonlocal next_vm
  p=next_vm;next_vm+=0x800;m.mem_write(p,bytes(0x800));return p
 def hook(uc,a,size,user):
  nonlocal bound
  sp=uc.reg_read(UC_X86_REG_ESP);this=uc.reg_read(UC_X86_REG_ECX);pop=None
  if a==0x458d70:
   script=get(sp+4);put(this+0x2c8+script*4,fresh());events.append(['create',script]);pop=4
  elif a==0x47fcb0:bound=fresh();uc.reg_write(UC_X86_REG_EAX,bound);pop=0
  elif a==0x40af00:events.append(['ascii' if this==ascii else 'text' if this==text else 'title',get(sp+8)]);pop=8
  elif a==0x46fe50:pop=0
  elif a==0x47e890:put(get(sp+4),bound);uc.reg_write(UC_X86_REG_EAX,get(sp+4));pop=8
  elif a==0x402b00:put(uc.reg_read(UC_X86_REG_EDX),len(data));uc.reg_write(UC_X86_REG_EAX,cmt);pop=4
  elif a==0x47f0a0:uc.reg_write(UC_X86_REG_EAX,get(sp+4));pop=4
  elif a==0x47f420:uc.reg_write(UC_X86_REG_EAX,get(this));pop=0
  elif a in (0x47f140,0x4113e0):pop=8 if a==0x47f140 else 4
  elif a==0x41be50:
   p=get(sp+16);row=next((n for n in range(len(entries)) if get(menu+0x720+n*4)==this),-1);positions.append(dict(row=row,target=list(struct.unpack('<3f',m.mem_read(p,12))),duration=get(sp+4),mode=get(sp+8)));pop=16
  elif a==0x46e3d0:events.append(['sound',get(sp+4)]);pop=8
  elif a==0x445690:events.append(['track',string(get(sp+8))]);pop=8
  elif a==0x445710:events.append(['music',get(sp+8)]);pop=8
  elif a==0x46ef90:events.append(['audio',get(sp+4)]);pop=12
  elif a==0x4855d2:pop=0
  elif a==0x47db50:
   fmt=string(get(sp+32));args=sp+36;values=[]
   for match in re.finditer(r'%(?:[-+ #0]*\d*(?:\.\d+)?l?)([ds%])',fmt):
    if match[1]=='%':continue
    values.append(string(get(args)) if match[1]=='s' else struct.unpack('<i',m.mem_read(args,4))[0]);args+=4
   requests.append(dict(color=get(sp+12),offset=get(sp+16),font=get(sp+20),style=get(sp+24),text=(fmt%tuple(values)).encode('latin1').hex()));pop=0
  if pop is not None:uc.reg_write(UC_X86_REG_EIP,get(sp));uc.reg_write(UC_X86_REG_ESP,sp+4+pop)
 m.hook_add(UC_HOOK_CODE,hook)
 def setup(state,timer,selection=0,heard=1,prompt=0,line=8):
  nonlocal next_vm
  m.mem_write(base,bytes(0xfe000));next_vm=vm_start;m.mem_write(cmt,data+b'\0');put(0x4db68c,score);put(0x4db520,sup);put(sup+0x191e4,ascii);put(0x4d967c,text);put(0x4f56cc,sup+0x1a000);put(0x4d8f58,0x3f800000);m.mem_write(0x4f5815,b'\0');m.mem_write(0x4d916c,b'\0')
  for off,v in ((0x14,title),(0x1c,13),(0x24,state),(0x28,selection),(0x30,len(entries)),(0xb4,1),(0x34,6),(0x74,10),(0xf8,1),(0x794,len(entries)),(0x798,line),(0x79c,selection),(0x7a0,prompt),(0x59e4,max(0,selection-9)),(0x2b4,timer-1),(0x2b8,timer),(0x2bc,0x3f800000),(0x2c0,0x4d8f58),(0x2c4,1)):put(menu+off,v)
  for n,e in enumerate(entries):
   m.mem_write(menu+0x7a4+n*64,e['path'].encode()+b'\0');m.mem_write(menu+0xfa4+n*66,bytes.fromhex(e['title'])+b'\0')
   for r,b in enumerate(e['comments']):m.mem_write(menu+0x17e4+(n*8+r)*66,bytes.fromhex(b)+b'\0')
   put(menu+0x720+n*4,fresh())
  for n in range(8):put(menu+0x770+n*4,fresh())
  for n in range(len(entries)):m.mem_write(score+0x24256+n,bytes([heard]))
  put(0x4d6884,0);put(0x4d6880,0);events.clear();requests.clear();positions.clear()
 def call():
  put(stack,base);m.reg_write(UC_X86_REG_ESP,stack);m.reg_write(UC_X86_REG_ECX,menu);m.emu_start(0x461ee0,base,count=1000000);assert m.reg_read(UC_X86_REG_EIP)==base,hex(m.reg_read(UC_X86_REG_EIP))
 def snapshot():return dict(screen=get(menu+0x1c),substate=get(menu+0x24),selected=get(menu+0x28),count=get(menu+0x794),line=get(menu+0x798),playing=get(menu+0x79c),prompt=get(menu+0x7a0),scroll=get(menu+0x59e4),depth=get(menu+0xb4),events=events[:],requests=requests[:],positions=positions[:])
 init=[]
 for heard in (0,1):
  setup(0,1,heard=heard,line=0);call();init.append(dict(heard=heard,result=snapshot()))
 controls=[]
 for selected,heard,prompt,line,timer,pressed in itertools.product(range(len(entries)),(0,1),(0,1),range(9),(0,1),(0,16,32,1,2)):
  setup(2,timer,selected,heard,prompt,line);put(0x4d6884,pressed);call();controls.append(dict(selected=selected,heard=heard,prompt=prompt,line=line,timer=timer,pressed=pressed,result=snapshot()))
 exits=[]
 for state,timer in ((1,4),(1,5),(3,9),(3,10)):
  setup(state,timer);call();exits.append(dict(substate=state,timer=timer,result=snapshot()))
 result=dict(passed=True,executableSha256=hashlib.sha256(img.data).hexdigest(),entries=entries,init=init,controls=controls,exits=exits,scope='Actual retail461ee0 Music Room state machine, original musiccmt.txt parser and data, title/comment creation ids, hidden-title/spoiler text, cursor/scroll/prompt/play requests, single cursor pop on exit. ANM binding/lookup/interrupt/interpolation, font queue and archive/audio/file services controlled; no original waveform/GPU equivalence.')
 (ROOT/'artifacts/th14/title-music-native.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print(f'PASS {len(entries)} tracks, {len(init)} entries, {len(controls)} controls, {len(exits)} boundaries')
if __name__=='__main__':main()
