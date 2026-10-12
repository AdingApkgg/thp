"""Run retail 429ff0 negative music requests; audio/factory are recorded boundaries."""
import hashlib,importlib,json,struct
from pathlib import Path
from unicorn import *
from unicorn.x86_const import *
ROOT=Path(__file__).resolve().parents[1]
def main():
 img,_,_=importlib.import_module('th-anm-handlers').handlers(16);m=Uc(UC_ARCH_X86,UC_MODE_32)
 for _,base,size,raw,n in img.sections:
  start=base&~4095;m.mem_map(start,((base+size+4095)&~4095)-start);m.mem_write(base,img.data[raw:raw+n])
 m.mem_map(0,4096);m.mem_map(0x70000000,0x50000)
 player,score,spell,stack=0x70001000,0x70008000,0x70030000,0x7004e000
 put=lambda p,v:m.mem_write(p,struct.pack('<I',v&0xffffffff))
 get=lambda p:struct.unpack('<I',m.mem_read(p,4))[0]
 events=[]
 def boundary(machine,address,size,user):
  sp=m.reg_read(UC_X86_REG_ESP)
  if address==0x45ed00:events.append(['audio',get(sp+4),get(sp+8)])
  elif address==0x406380:events.append(['front',get(sp+8),get(sp+12),get(sp+16)]);put(get(sp+4),123)
 for addr,cleanup in ((0x47499b,0),(0x45ed00,12),(0x406380,16)):
  m.mem_write(addr,b'\xc2'+struct.pack('<H',cleanup) if cleanup else b'\xc3');m.hook_add(UC_HOOK_CODE,boundary,begin=addr,end=addr)
 put(0x4a6dcc,player);put(player+0x178,0x70002000);put(0x4a6f0c,score);put(0x4a6dd4,spell)
 table=[]
 for stage in range(1,8):
  p=0x4a22d0+stage*0xd4
  names=[img.read(img.u32(p+0xc+i*4),32).split(b'\0')[0].decode() for i in range(2)]
  table.append(dict(stage=stage,cues=[img.u32(p+0x28),img.u32(p+0x2c)],names=names))
 rows=[]
 for row in table:
  stage=row['stage'];put(0x4a6f18,0x4a22d0+stage*0xd4)
  for id in (-3,-1):
   for existing in (0,0x70004000):
    for stop in (0,1):
     for practice_match in (0,1,2):
      m.mem_write(score,bytes(0x20000));put(player+0x1c8,existing);put(0x4a5bec,0x20 if practice_match else 0);put(spell+0xac,0);put(0x4c12cc,stop<<4)
      name=row['names'][id==-1]+'.wav' if practice_match==1 else 'different.wav'
      m.mem_write(0x4dc0f0,name.encode()+b'\0');events.clear();put(stack,0x70000000);put(stack+4,id)
      m.reg_write(UC_X86_REG_ESP,stack);m.reg_write(UC_X86_REG_ECX,player);m.reg_write(UC_X86_REG_MXCSR,0x1f80)
      m.emu_start(0x429ff0,0x70000000,count=100000);assert m.reg_read(UC_X86_REG_EIP)==0x70000000
      rows.append(dict(stage=stage,id=id,existing=existing,stop=stop,practiceMatch=practice_match,events=events.copy(),dialogueAfter=get(player+0x1c8),unlocks=list(m.mem_read(score+0x19fa6,18))))
 logos=[]
 for mode in (0,8,13):
  for flags in (0,0x10,0x40,0x80):
   put(0x4c17c4,mode);put(0x4a5bec,flags);put(stack,0x70000000);events.clear();m.reg_write(UC_X86_REG_ESP,stack)
   m.emu_start(0x42c240,0x70000000,count=10000);logos.append(dict(mode=mode,flags=flags,events=events.copy()))
 out=ROOT/'artifacts/th16/music-request-native.json';out.parent.mkdir(parents=True,exist_ok=True)
 out.write_text(json.dumps(dict(executableSha256=hashlib.sha256(img.data).hexdigest(),table=table,rows=rows,logos=logos,scope='Full retail429ff0 for -3/-1 and actual stage descriptors1..7, plus complete42c240 logo requester with modes0/8/13 and run flags0/10/40/80. Queue45ed00 and front factory406380 are controlled request recorders; cookie is a sink. Observe ordinary/config-bit4/spell-practice matching branches, descriptor unlock bytes and untouched dialogue pointer. No actual audio, native front VM execution, ECL cancellation, ending/results, GPU or complete game claim.'),separators=(',',':'))+'\n')
 print(len(rows),'retail TH16 music request cases')
if __name__=='__main__':main()
