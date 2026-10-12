"""Execute retail4286b7 spell/ordinary interrupt assignments."""
import hashlib,importlib,itertools,json,struct
from pathlib import Path
from unicorn import Uc,UC_ARCH_X86,UC_MODE_32,UC_HOOK_CODE
from unicorn.x86_const import *
ROOT=Path(__file__).resolve().parents[1]
def main():
 img,_,_=importlib.import_module('th-anm-handlers').handlers(14);m=Uc(UC_ARCH_X86,UC_MODE_32)
 for _,b,size,raw,n in img.sections:
  start=b&~4095;m.mem_map(start,((b+size+4095)&~4095)-start);m.mem_write(b,img.data[raw:raw+n])
 base,owner,code,stack=0x70000000,0x70010000,0x70018000,0x7001f000;m.mem_map(base,0x20000)
 def put(p,v):m.mem_write(p,struct.pack('<I',v&0xffffffff))
 def get(p):return struct.unpack('<I',m.mem_read(p,4))[0]
 args=[];reads=[]
 def hook(uc,a,size,user):
  sp=uc.reg_read(UC_X86_REG_ESP);index=get(sp+4);reads.append(index);uc.reg_write(UC_X86_REG_EAX,args[index]&0xffffffff);uc.reg_write(UC_X86_REG_EIP,get(sp));uc.reg_write(UC_X86_REG_ESP,sp+8)
 m.hook_add(UC_HOOK_CODE,hook,begin=0x42c1d0,end=0x42c1d0)
 rows=[]
 for flags,boss,slot,health,time in itertools.product((0,16,32,48),(0,1),range(8),(-1,0,100),(0,90,0x7fffffff)):
  m.mem_write(base,bytes(0x1e000));put(0x4f58b8,flags);put(base+0x4054,boss*0x800000);put(base+0x40ec,owner);args[:]=[slot,health,time];reads.clear();m.mem_write(code+0x20,b'next_phase\0')
  p=owner+0x525c+slot*16
  for n,v in enumerate((100,200,0x1111,0x2222)):put(p+n*4,v)
  m.reg_write(UC_X86_REG_EDI,base);m.reg_write(UC_X86_REG_ESI,code);m.reg_write(UC_X86_REG_ESP,stack);m.emu_start(0x4286b7,0x429c28,count=10000);assert m.reg_read(UC_X86_REG_EIP)==0x429c28
  words=[get(p+n*4) for n in range(4)];names=[]
  for n,v in enumerate(words[2:]):names.append('old_health' if v==0x1111 else 'old_timeout' if v==0x2222 else bytes(m.mem_read(v,32)).split(b'\0')[0].decode())
  rows.append(dict(flags=flags,boss=boss,slot=slot,health=health,time=time,result=words[:2],names=names,reads=reads[:]))
 (ROOT/'artifacts/th14/spell-interrupt-native.json').write_text(json.dumps(dict(executableSha256=hashlib.sha256(img.data).hexdigest(),rows=rows,scope='Complete retail4286b7 handler, actual42bed0 assignment helper for ordinary requests; integer argument lookup controlled. Exact interrupt health/time and next-phase versus BossDead/BossEscape names. No interpreter/phase execution/browser proof.'),indent=2)+'\n',encoding='utf-8');print(f'PASS {len(rows)} spell/ordinary interrupt assignments')
if __name__=='__main__':main()
