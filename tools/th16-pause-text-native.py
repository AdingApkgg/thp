"""Own43edc0 normal game-over text, including43ec10/43e730."""
import hashlib,importlib,itertools,json,re,struct
from pathlib import Path
from unicorn import *
from unicorn.x86_const import *
ROOT=Path(__file__).resolve().parents[1]
def main():
 img,_,_=importlib.import_module('th-anm-handlers').handlers(16);m=Uc(UC_ARCH_X86,UC_MODE_32)
 for _,b,size,raw,n in img.sections:
  start=b&~4095;m.mem_map(start,((b+size+4095)&~4095)-start);m.mem_write(b,img.data[raw:raw+n])
 m.mem_map(0x70000000,0xa0000);menu,bank,ascii,tm,stack,ret=(0x70000000+n for n in (0x1000,0x10000,0x40000,0x60000,0x9d000,0x9e000))
 def put(p,v):m.mem_write(p,struct.pack('<I',v&0xffffffff))
 def get(p):return struct.unpack('<I',m.mem_read(p,4))[0]
 def z(p):
  b=bytearray()
  while (v:=m.mem_read(p+len(b),1)[0]):b.append(v)
  return b.decode('latin1')
 requests=[]
 def boundary(machine,a,size,user):
  sp=machine.reg_read(UC_X86_REG_ESP)
  if a==0x46efa0:machine.reg_write(UC_X86_REG_EAX,0)
  elif a==0x47a36a:machine.reg_write(UC_X86_REG_EAX,tm)
  elif a==0x408260:
   pos=get(sp+8);fmt=z(get(sp+12));arg=16
   def render(match):
    nonlocal arg
    flags,width,precision,modifier,kind=match.groups();v=get(sp+arg);arg+=4
    if kind=='s':s=z(v);s=s[:int(precision)] if precision else s
    elif kind=='c':s=chr(v&255)
    else:
     value=v if kind=='u' else v if v<0x80000000 else v-0x100000000;s=str(value)
     if precision:s=('0' if value==0 else '') if int(precision)==0 else s.rjust(int(precision),'0')
    return s.rjust(int(width or 0),'0' if '0' in flags else ' ')
   text=re.sub(r'%([-+ #0]*)(\d*)(?:\.(\d+))?([hl]*)([sdcu])',render,fmt)
   requests.append(dict(text=text,words=[get(pos+n*4) for n in range(3)]+[get(ascii+0x1920c)]))
 for a,cleanup in ((0x46efa0,4),(0x47a36a,0),(0x408260,0)):
  m.mem_write(a,b'\xc2'+struct.pack('<H',cleanup) if cleanup else b'\xc3');m.hook_add(UC_HOOK_CODE,boundary,begin=a,end=a)
 initial=bytes.fromhex(json.loads((ROOT/'artifacts/th16/score-native.json').read_text())['initial']);inputs=[]
 for rank,selected,length,unranked,dated,credits in itertools.product((0,9),(0,88,89,90),(0,7,8),(0,1),(0,1),(0,5)):inputs.append((15,rank,selected,length,unranked,dated,credits))
 for sub,credits in itertools.product((2,6,14,16),(0,5)):inputs.append((sub,0,0,0,0,0,credits))
 cases=[]
 for sub,rank,selected,length,unranked,dated,credits in inputs:
  m.mem_write(menu,bytes(0x800));m.mem_write(bank,bytes(0x1a3ac));requests.clear();m.mem_write(ascii,bytes(0x20000))
  for n in range(5):m.mem_write(bank+8+n*0x5318,initial)
  for p,v in ((0x4a6f0c,bank),(0x4a6d98,ascii),(0x4a57a4,0),(0x4a57a8,0),(0x4a57b4,0),(0x4a5bfc,credits),(menu+0x1ec,2),(menu+0x1f4,sub),(menu+0x34,rank),(menu+0x10c,selected),(menu+0x1f8,length),(menu+0x200,unranked),(ascii+0x1920c,0xffffffff)):put(p,v)
  m.mem_write(menu+0x2d4,b'ABCDEFGH'[:length]+b' '*(8-length)+b'\0')
  if dated:
   row=bank+8+0x10+rank*32;m.mem_write(row+16,struct.pack('<Q',86400));m.mem_write(row+4,b'\x09\x02')
  for n,v in enumerate((0,0,0,2,0,70,5,1,0)):put(tm+n*4,v)
  put(stack,ret);m.reg_write(UC_X86_REG_ESP,stack);m.reg_write(UC_X86_REG_ECX,menu);m.emu_start(0x43edc0,ret,count=30000);assert m.reg_read(UC_X86_REG_EIP)==ret
  cases.append(dict(sub=sub,rank=rank,selected=selected,length=length,unranked=unranked,dated=dated,credits=credits,requests=list(requests)))
 (ROOT/'artifacts/th16/pause-text-native.json').write_text(json.dumps(dict(executableSha256=hashlib.sha256(img.data).hexdigest(),cases=cases),separators=(',',':'))+'\n',encoding='utf-8');print(f'{len(cases)} own TH16 normal game-over ASCII request cases')
if __name__=='__main__':main()
