"""Full retail432100 negative MSG/music/result request branches."""
import hashlib,importlib,itertools,json,struct
from pathlib import Path
from unicorn import Uc,UC_ARCH_X86,UC_MODE_32,UC_HOOK_CODE
from unicorn.x86_const import *
ROOT=Path(__file__).resolve().parents[1]
def main():
 img,_,_=importlib.import_module('th-anm-handlers').handlers(14);m=Uc(UC_ARCH_X86,UC_MODE_32)
 for _,b,size,raw,n in img.sections:
  start=b&~4095;m.mem_map(start,((b+size+4095)&~4095)-start);m.mem_write(b,img.data[raw:raw+n])
 m.mem_map(0,4096);base,game,control,score,spell,vm,stack=0x70000000,0x70001000,0x70003000,0x70005000,0x70040000,0x70041000,0x7004f000;m.mem_map(base,0x50000)
 def put(p,v):m.mem_write(p,struct.pack('<I',v&0xffffffff))
 def get(p):return struct.unpack('<I',m.mem_read(p,4))[0]
 events=[]
 def hook(uc,a,size,user):
  sp=uc.reg_read(UC_X86_REG_ESP);pop=None
  if a==0x46ef90:events.append(['audio',get(sp+4),get(sp+8)]);pop=12
  elif a==0x47fcb0:uc.reg_write(UC_X86_REG_EAX,vm);pop=0
  elif a==0x40af00:events.append(['front',get(sp+8)]);pop=8
  elif a==0x46fe50:pop=0
  elif a==0x47e890:put(get(sp+4),123);uc.reg_write(UC_X86_REG_EAX,get(sp+4));pop=8
  elif a==0x4854a0:pop=0
  elif a in (0x449d30,0x436f90):events.append(['failure' if a==0x449d30 else 'completion']);pop=0
  if pop is not None:uc.reg_write(UC_X86_REG_EIP,get(sp));uc.reg_write(UC_X86_REG_ESP,sp+4+pop)
 m.hook_add(UC_HOOK_CODE,hook)
 table=[]
 for stage in range(1,8):
  p=0x4d5988+stage*0xcc;table.append(dict(stage=stage,names=[img.read(img.u32(p+0xc+i*4),32).split(b'\0')[0].decode() for i in range(2)],cues=[img.u32(p+0x30+i*4) for i in range(2)]))
 rows=[]
 for row in table:
  for id,replay,stop,match in itertools.product((-3,-1),(0,1),(0,1),(0,1,2)):
   m.mem_write(base,bytes(0x4d000));put(0x4db550,game);put(0x4db558,control);put(0x4db68c,score);put(0x4db534,spell);put(0x4f56cc,base+0x46000);put(game+0x148,base+0x44000);put(game+0x194,base+0x48000);put(0x4db69c,0x4d5988+row['stage']*0xcc);put(0x4f58b8,32 if match else 0);put(control+0x94,replay);put(0x4d916c,stop<<4);m.mem_write(0x4f5815,b'\0')
   name=row['names'][id==-1]+'.wav' if match==1 else 'different.wav';m.mem_write(0x4f9e00,name.encode()+b'\0');events.clear();put(stack,base);put(stack+4,id);m.reg_write(UC_X86_REG_ESP,stack);m.reg_write(UC_X86_REG_ECX,game);m.emu_start(0x432100,base,count=100000);assert m.reg_read(UC_X86_REG_EIP)==base
   rows.append(dict(stage=row['stage'],id=id,replay=replay,stop=stop,match=match,events=events[:],dialogueAfter=get(game+0x194),unlocks=list(m.mem_read(score+0x24256,18))))
 results=[]
 for flags in (0,1,2,0x80,0x81,0xff):
  put(spell+0x7c,flags);events.clear();put(stack,base);put(stack+4,-2);m.reg_write(UC_X86_REG_ESP,stack);m.reg_write(UC_X86_REG_ECX,game);m.emu_start(0x432100,base,count=100000);assert m.reg_read(UC_X86_REG_EIP)==base;results.append(dict(flags=flags,events=events[:]))
 (ROOT/'artifacts/th14/music-request-native.json').write_text(json.dumps(dict(executableSha256=hashlib.sha256(img.data).hexdigest(),table=table,rows=rows,results=results,scope='Full retail432100 with actual seven stage descriptors: -3/-1, config stop bit4, replay, current-track spell practice suppression, unlock bytes, unchanged dialogue pointer; -2 failure/completion dispatch. Audio/ANM/ending/menu services controlled. No original audio/GPU or complete gameplay equivalence.'),indent=2)+'\n',encoding='utf-8');print(f'PASS {len(rows)} music requests and {len(results)} result branches')
if __name__=='__main__':main()
